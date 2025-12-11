import os
import telebot
from telebot import types
import logging
import base64
import shutil
from encryption import aes_cipher, rsa_cipher, ecc_cipher
from utils import file_manager, crypto_utils, db_manager

try:
    import pyzipper
except ImportError:
    pyzipper = None

# Initialize DB
db_manager.init_db()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8597263076:AAFtIBCqPuZUaNuto7SdwPCdpUFkteegdJo")

bot = telebot.TeleBot(BOT_TOKEN)

USER_STATE = {}

STATE_IDLE = "IDLE"
STATE_WAIT_ALGO = "WAIT_ALGO"
STATE_WAIT_FILE_ENCRYPT = "WAIT_FILE_ENCRYPT"
STATE_WAIT_PASSWORD_ENCRYPT = "WAIT_PASSWORD_ENCRYPT"
STATE_WAIT_FILE_DECRYPT = "WAIT_FILE_DECRYPT"
STATE_WAIT_PASSWORD_DECRYPT = "WAIT_PASSWORD_DECRYPT"
STATE_ADMIN_AUTH_LOGIN = "ADMIN_AUTH_LOGIN"
STATE_ADMIN_AUTH_PASS = "ADMIN_AUTH_PASS"
STATE_ADMIN_BROADCAST = "ADMIN_BROADCAST"

ADMIN_ID = 8332161047
ADMIN_LOGIN = "KHUSNIDDIN"
ADMIN_PASS = "ADMIN!@"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    db_manager.add_user(user.id, user.username, user.first_name, user.last_name)
    
    USER_STATE[message.from_user.id] = {"state": STATE_IDLE}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_enc = types.KeyboardButton("🔒 Shifrlash")
    btn_dec = types.KeyboardButton("🔓 Deshifrlash")
    markup.add(btn_enc, btn_dec)
    
    bot.send_message(
        message.chat.id, 
        "👋 **Assalamu alaykum!**\n\nMen **shifrlash boti**man. Ma'lumotlaringizni xavfsiz saqlashga yordam beraman.\n\n👇 *Quyidagi bo'limlardan birini tanlang:*", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_login(message):
    if message.from_user.id != ADMIN_ID:
        return # Ignore non-admins
    
    USER_STATE[message.from_user.id] = {"state": STATE_ADMIN_AUTH_LOGIN}
    bot.send_message(message.chat.id, "🕵️‍♂️ **Admin Panel**\n\nIltimos, **Login** kiriting:", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID: return
    action = call.data.split("_")[1]
    
    if action == "stats":
        summary = db_manager.get_stats_summary()
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **Statistika:**\n\n{summary}", parse_mode="Markdown")
        
    elif action == "db":
        bot.answer_callback_query(call.id, "📂 Tayyorlanmoqda...")
        csv_data = db_manager.get_all_users_csv()
        with open("users_export.csv", "w") as f: f.write(csv_data)
        with open("users_export.csv", "rb") as f:
            bot.send_document(call.message.chat.id, f, caption="📂 **Foydalanuvchilar Bazasi**")
            
    elif action == "broadcast":
        USER_STATE[call.from_user.id] = {"state": STATE_ADMIN_BROADCAST}
        bot.send_message(call.message.chat.id, "📢 **Xabar Yuborish**\n\nBarcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm) yozing:", parse_mode="Markdown")
        
    elif action == "logout":
        USER_STATE[call.from_user.id] = {"state": STATE_IDLE}
        bot.edit_message_text("🚪 Panel yopildi.", call.message.chat.id, call.message.message_id)

# -------------------

@bot.message_handler(func=lambda m: m.text == "🔒 Shifrlash")
def enc_menu(m):
    USER_STATE[m.from_user.id] = {"state": STATE_WAIT_ALGO}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔑 AES (Tezkor)", callback_data="AES"))
    markup.add(types.InlineKeyboardButton("🛡️ RSA (Kuchli)", callback_data="RSA"))
    markup.add(types.InlineKeyboardButton("🧬 ECC (Zamonaviy)", callback_data="ECC"))
    
    bot.send_message(m.chat.id, "🎛 **Shifrlash algoritmini tanlang:**\n\n_Har birining xavfsizlik darajasi turlicha._", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔓 Deshifrlash")
def dec_menu(m):
    USER_STATE[m.from_user.id] = {"state": STATE_WAIT_FILE_DECRYPT}
    bot.send_message(m.chat.id, "Deshifrlash uchun ZIP yuboring:", reply_markup=types.ReplyKeyboardRemove())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("admin_"): return # Handled by admin handler
    user_id = call.from_user.id
    choice = call.data
    USER_STATE[user_id] = {"state": STATE_WAIT_FILE_ENCRYPT, "algo": choice}
    bot.edit_message_text(
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        text=f"✅ **{choice} algoritmi tanlandi.**\n\n📄 Endi shifrlamoqchi bo'lgan **fayl, rasm yoki hujjatni** yuboring:",
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['document', 'photo'])
def handle_docs(message):
    user_id = message.from_user.id
    state_data = USER_STATE.get(user_id, {"state": STATE_IDLE})
    state = state_data.get("state")
    
    # ... logic for broadcast photo handling could be added here if generic text handler doesn't catch it ...
    if state == STATE_ADMIN_BROADCAST:
        handle_broadcast(message) # Helper to reuse logic
        return

    try:
        # Determine file info (Document or Photo)
        if message.content_type == 'document':
            file_id = message.document.file_id
            file_name = message.document.file_name
        elif message.content_type == 'photo':
            # Photos don't have original filenames, so we generate one
            file_id = message.photo[-1].file_id
            file_name = f"photo_{file_id[:10]}.jpg"
        else:
            return # Should not happen based on content_types

        if state == STATE_WAIT_FILE_ENCRYPT:
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            
            # Use absolute path to prevent CWD confusion
            download_dir = os.path.abspath(f"downloads/{user_id}")
            os.makedirs(download_dir, exist_ok=True)
            file_path = os.path.join(download_dir, file_name)
            
            logging.info(f"Downloading file/photo: {file_name}")
            with open(file_path, 'wb') as f: f.write(downloaded_file)
            
            USER_STATE[user_id]["file_path"] = file_path
            USER_STATE[user_id]["original_name"] = file_name
            USER_STATE[user_id]["state"] = STATE_WAIT_PASSWORD_ENCRYPT
            bot.send_message(
                message.chat.id, 
                "🔐 **Xavfsizlik bosqichi**\n\nZIP arxivga qo'yiladigan **maxfiy parolni** o'z o'ylab topib, menga yozing:\n\n_(Bu parol faylni ochish uchun kerak bo'ladi)_",
                parse_mode="Markdown"
            )

        elif state == STATE_WAIT_FILE_DECRYPT:
            if message.content_type == 'photo':
                 bot.send_message(message.chat.id, "⚠️ Rasm emas, ZIP fayl yuboring (fayl sifatida)!")
                 return
            
            if not file_name.endswith('.zip'):
                bot.send_message(message.chat.id, "⚠️ Faqat .zip fayl yuboring!")
                return
            
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            download_dir = os.path.abspath(f"downloads/{user_id}")
            os.makedirs(download_dir, exist_ok=True)
            zip_path = os.path.join(download_dir, file_name)
            with open(zip_path, 'wb') as f: f.write(downloaded)
            
            extract_dir = os.path.join(download_dir, "extracted")
            if os.path.exists(extract_dir): shutil.rmtree(extract_dir)

            # Check if password needed by trying to extract list
            is_encrypted = False
            if pyzipper:
                try:
                    with pyzipper.AESZipFile(zip_path) as zf:
                        for info in zf.infolist():
                            if info.flag_bits & 0x1: is_encrypted = True; break
                except: is_encrypted = True # Assume yes if fail
            
            if is_encrypted:
                USER_STATE[user_id] = {
                    "state": STATE_WAIT_PASSWORD_DECRYPT, 
                    "zip_path": zip_path, 
                    "extract_dir": extract_dir,
                    "attempts": 0
                }
                bot.send_message(message.chat.id, "🔑 **Fayl himoyalangan!**\n\nIltimos, faylni ochish uchun **parolni** kiriting:", parse_mode="Markdown")
            else:
                # Try extract immediately
                try:
                    bot.send_message(message.chat.id, "🔓 Deshifrlanmoqda...")
                    process_decryption_final(message, zip_path, extract_dir, None)
                    USER_STATE[user_id] = {"state": STATE_IDLE}
                except Exception as e:
                    # Maybe it actually needed password but logic failed detection
                     logging.error(e)
                     bot.send_message(message.chat.id, "Xatolik yoki parol kerak.")
    except Exception as e:
        bot.reply_to(message, f"Xato: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    state_data = USER_STATE.get(user_id, {})
    state = state_data.get("state")
    
    logging.info(f"Text received: '{message.text}' from {user_id}, state: {state}")

    # --- ADMIN AUTH & BROADCAST ---
    if state == STATE_ADMIN_AUTH_LOGIN:
        if message.text == ADMIN_LOGIN:
            USER_STATE[user_id]["state"] = STATE_ADMIN_AUTH_PASS
            bot.send_message(message.chat.id, "✅ Login to'g'ri.\n🔑 **Parol kiriting:**", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ **Login noto'g'ri!**")
            USER_STATE[user_id] = {"state": STATE_IDLE}
        return

    if state == STATE_ADMIN_AUTH_PASS:
        if message.text == ADMIN_PASS:
            USER_STATE[user_id] = {"state": STATE_IDLE, "is_admin": True} # Session active (or just show menu once)
            show_admin_dashboard(message.chat.id)
        else:
            bot.send_message(message.chat.id, "❌ **Parol noto'g'ri!**")
            USER_STATE[user_id] = {"state": STATE_IDLE}
        return

    if state == STATE_ADMIN_BROADCAST:
        handle_broadcast(message)
        return
    # -----------------------------

    if state == STATE_WAIT_PASSWORD_ENCRYPT:
        password = message.text.strip()
        
        # Security Policy
        if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            bot.send_message(
                message.chat.id, 
                "❌ **Parol juda oddiy!**\n\nIltimos, xavfsizlik uchun:\n- Kamida **8 ta belgi**,\n- **Harflar va raqamlar** qatnashgan parol yozing.", 
                parse_mode="Markdown"
            )
            return

        bot.send_message(message.chat.id, "⏳ **Shifrlanmoqda...**\n_Iltimos, biroz kuting._", parse_mode="Markdown")
        algo = state_data["algo"]
        file_path = state_data["file_path"]
        orig_name = state_data["original_name"]
        
        try:
            if algo == "AES": process_aes(message, file_path, orig_name, password)
            elif algo == "RSA": process_rsa(message, file_path, orig_name, password)
            elif algo == "ECC": process_ecc(message, file_path, orig_name, password)
        except Exception as e:
            bot.send_message(message.chat.id, f"Xato: {e}")
        finally:
             if os.path.exists(os.path.dirname(file_path)): shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
             USER_STATE[user_id] = {"state": STATE_IDLE}

    elif state == STATE_WAIT_PASSWORD_DECRYPT:
        password = message.text.strip()
        zip_path = state_data["zip_path"]
        extract_dir = state_data["extract_dir"]
        attempts = state_data.get("attempts", 0)

        bot.send_message(message.chat.id, "🔓 **Ochilmoqda...**", parse_mode="Markdown")
        try:
             process_decryption_final(message, zip_path, extract_dir, password)
             # If we reached here, no exception raised (Success)
             if os.path.exists(os.path.dirname(zip_path)): shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)
             USER_STATE[user_id] = {"state": STATE_IDLE}

        except ValueError:
             attempts += 1
             USER_STATE[user_id]["attempts"] = attempts
             
             if attempts < 3:
                 bot.send_message(message.chat.id, f"❌ **Parol noto'g'ri!**\n\nQayta urinib ko'ring ({attempts}/3):", parse_mode="Markdown")
                 # Do NOT reset state or delete files
             else:
                 bot.send_message(message.chat.id, "🚫 **Juda ko'p urinishlar!**\nJarayon bekor qilindi.", parse_mode="Markdown")
                 if os.path.exists(os.path.dirname(zip_path)): shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)
                 USER_STATE[user_id] = {"state": STATE_IDLE}

        except Exception as e:
             bot.send_message(message.chat.id, f"Xato: {e}")
             if os.path.exists(os.path.dirname(zip_path)): shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)
             USER_STATE[user_id] = {"state": STATE_IDLE}

def show_admin_dashboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton("📥 Bazani Yuklash", callback_data="admin_db"),
        types.InlineKeyboardButton("📢 Xabar Yuborish", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🚪 Chiqish", callback_data="admin_logout")
    )
    bot.send_message(chat_id, "🔧 **Admin Boshqaruv Paneli**\n\nKerakli bo'limni tanlang:", reply_markup=markup, parse_mode="Markdown")

def handle_broadcast(message):
    ids = db_manager.get_all_user_ids()
    count = 0
    
    msg_id = bot.send_message(message.chat.id, "🚀 **Xabar yuborilmoqda...**", parse_mode="Markdown").message_id
    
    for uid in ids:
        try:
            if message.content_type == 'text':
                bot.send_message(uid, message.text)
            elif message.content_type == 'photo':
                 bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            count += 1
        except:
            pass # User blocked bot
            
    bot.delete_message(message.chat.id, msg_id)
    bot.send_message(message.chat.id, f"✅ **Xabar yuborildi!**\n\n👥 Qabul qildi: {count} ta foydalanuvchi.")
    USER_STATE[message.from_user.id] = {"state": STATE_IDLE}

def process_aes(message, file_path, orig_name, password):
    data = file_manager.read_file(file_path)
    aes_key = aes_cipher.generate_aes_key()
    iv, ciphertext = aes_cipher.encrypt_aes(data, aes_key)
    
    # Encrypt Key with Password (Double Security)
    salt, piv, enc_aes_key = crypto_utils.encrypt_data_with_password(aes_key, password)
    
    enc_path = file_path + ".enc"
    file_manager.write_file(enc_path, ciphertext)
    
    zip_path = file_path + "_secure.zip"
    file_manager.create_secure_zip(
        zip_path, enc_path, enc_aes_key, 
        {"iv": iv, "algo": b"AES", "filename": orig_name.encode(), "salt": salt, "piv": piv},
        password=password # Encrypt ZIP itself
    )
    with open(zip_path, 'rb') as f: bot.send_document(message.chat.id, f, visible_file_name=orig_name+".zip", caption="Zip Parol: " + password)

def process_rsa(message, file_path, orig_name, password):
    data = file_manager.read_file(file_path)
    priv, pub = rsa_cipher.generate_rsa_key_pair()
    aes_key = aes_cipher.generate_aes_key()
    iv, ciphertext = aes_cipher.encrypt_aes(data, aes_key)
    enc_aes_key = rsa_cipher.encrypt_rsa(aes_key, pub)
    
    priv_pem = rsa_cipher.private_key_to_pem(priv)
    salt, piv, enc_priv_pem = crypto_utils.encrypt_data_with_password(priv_pem, password)
    
    enc_path = file_path + ".enc"
    file_manager.write_file(enc_path, ciphertext)
    
    zip_path = file_path + "_rsa_secure.zip"  
    
    if pyzipper:
        with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode())
            write_rsa_zip_content(zf, enc_path, enc_aes_key, iv, orig_name, enc_priv_pem, salt, piv)
    else:
        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # No zip password fallback
            write_rsa_zip_content(zf, enc_path, enc_aes_key, iv, orig_name, enc_priv_pem, salt, piv)

    with open(zip_path, 'rb') as f: bot.send_document(message.chat.id, f, visible_file_name=orig_name+".zip", caption="RSA Zip Parol: " + password)

def write_rsa_zip_content(zf, enc_path, enc_aes_key, iv, orig_name, enc_priv_pem, salt, piv):
    zf.write(enc_path, os.path.basename(enc_path))
    zf.writestr("encrypted_aes_key.bin", base64.b64encode(enc_aes_key))
    zf.writestr("iv.txt", base64.b64encode(iv))
    zf.writestr("algo.txt", "RSA")
    zf.writestr("filename.txt", base64.b64encode(orig_name.encode()))
    zf.writestr("encrypted_private_key.bin", base64.b64encode(enc_priv_pem))
    zf.writestr("salt.txt", base64.b64encode(salt))
    zf.writestr("piv.txt", base64.b64encode(piv))

def process_ecc(message, file_path, orig_name, password):
    data = file_manager.read_file(file_path)
    priv, pub = ecc_cipher.generate_ecc_key_pair()
    aes_key = aes_cipher.generate_aes_key()
    file_iv, file_ciphertext = aes_cipher.encrypt_aes(data, aes_key)
    ephem_pub, key_iv, enc_aes_key_tag = ecc_cipher.encrypt_ecc_hybrid(aes_key, pub)
    
    from cryptography.hazmat.primitives import serialization
    priv_pem = priv.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
    salt, piv, enc_priv_pem = crypto_utils.encrypt_data_with_password(priv_pem, password)
    
    enc_path = file_path + ".enc"
    file_manager.write_file(enc_path, file_ciphertext)
    
    zip_path = file_path + "_ecc_secure.zip"
    
    if pyzipper:
        with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode())
            write_ecc_zip_content(zf, enc_path, enc_aes_key_tag, key_iv, ephem_pub, file_iv, orig_name, enc_priv_pem, salt, piv)
    else:
        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zf:
            write_ecc_zip_content(zf, enc_path, enc_aes_key_tag, key_iv, ephem_pub, file_iv, orig_name, enc_priv_pem, salt, piv)

    with open(zip_path, 'rb') as f: bot.send_document(message.chat.id, f, visible_file_name=orig_name+".zip", caption="ECC Zip Parol: " + password)

def write_ecc_zip_content(zf, enc_path, enc_aes_key_tag, key_iv, ephem_pub, file_iv, orig_name, enc_priv_pem, salt, piv):
    zf.write(enc_path, os.path.basename(enc_path))
    zf.writestr("encrypted_aes_key.bin", base64.b64encode(enc_aes_key_tag))
    zf.writestr("key_iv.txt", base64.b64encode(key_iv))
    zf.writestr("ephem_pub.pem", ephem_pub)
    zf.writestr("file_iv.txt", base64.b64encode(file_iv))
    zf.writestr("algo.txt", "ECC")
    zf.writestr("filename.txt", base64.b64encode(orig_name.encode()))
    zf.writestr("encrypted_private_key.bin", base64.b64encode(enc_priv_pem))
    zf.writestr("salt.txt", base64.b64encode(salt))
    zf.writestr("piv.txt", base64.b64encode(piv))

def process_decryption_final(message, zip_path, extract_dir, password):
    # Extract using password
    extracted = file_manager.extract_secure_zip(zip_path, extract_dir, password)
    
    # Read Algo
    algo_file = os.path.join(extract_dir, "algo.txt")
    if os.path.exists(algo_file):
        with open(algo_file, 'r') as f: algo = f.read().strip()
    elif os.path.exists(os.path.join(extract_dir, "key.txt")): algo = "AES"
    else: 
        bot.reply_to(message, "❌ Algo topilmadi."); return

    if "AES" in algo: algo = "AES"
    if "RSA" in algo: algo = "RSA"
    if "ECC" in algo: algo = "ECC"
    
    # Find encrypted file
    enc_file = None
    for name in os.listdir(extract_dir):
        if name.endswith(".enc") or name == "user_file_encrypted.txt": enc_file = os.path.join(extract_dir, name); break
    if not enc_file: bot.reply_to(message, "❌ Fayl topilmadi."); return
    
    # Read filename
    filename_file = os.path.join(extract_dir, "filename.txt")
    orig_name = "decrypted.file"
    if os.path.exists(filename_file):
        with open(filename_file, 'r') as f:
            try: orig_name = base64.b64decode(f.read().strip()).decode()
            except: pass

    # Decrypt Key then File
    try:
        decrypted_data = None
        logging.info(f"Decrypting with algo: {algo}, password provided: {bool(password)}")
        
        if algo == "AES":
            salt_path = os.path.join(extract_dir, "salt.txt")
            if os.path.exists(salt_path):
                 with open(salt_path,'r') as f: 
                    content = f.read()
                    if content is None: raise ValueError("Salt file empty/None")
                    salt = base64.b64decode(content)
                    
                 with open(os.path.join(extract_dir, "piv.txt"),'r') as f: 
                    piv = base64.b64decode(f.read())
                    
                 with open(os.path.join(extract_dir, "key.txt"),'r') as f: 
                    enc_key = base64.b64decode(f.read())
                 
                 logging.info("Decrypting AES Key...")
                 aes_key = crypto_utils.decrypt_data_with_password(salt, piv, enc_key, password)
            else:
                 with open(os.path.join(extract_dir, "key.txt"),'r') as f: aes_key = base64.b64decode(f.read())
            
            with open(os.path.join(extract_dir, "iv.txt"),'r') as f: iv = base64.b64decode(f.read())
            enc_data = file_manager.read_file(enc_file)
            logging.info("Decrypting File...")
            decrypted_data = aes_cipher.decrypt_aes(iv, enc_data, aes_key)
            
        elif algo == "RSA":
            # Decrypt Priv Key
            salt_path = os.path.join(extract_dir, "salt.txt")
            if os.path.exists(salt_path):
                 with open(salt_path,'r') as f: salt = base64.b64decode(f.read())
                 with open(os.path.join(extract_dir, "piv.txt"),'r') as f: piv = base64.b64decode(f.read())
                 with open(os.path.join(extract_dir, "encrypted_private_key.bin"),'r') as f: enc_p = base64.b64decode(f.read())
                 priv_pem_bytes = crypto_utils.decrypt_data_with_password(salt, piv, enc_p, password)
            else:
                 with open(os.path.join(extract_dir, "private_key.pem"),'rb') as f: priv_pem_bytes = f.read()

            from cryptography.hazmat.backends import default_backend; from cryptography.hazmat.primitives import serialization
            priv = serialization.load_pem_private_key(priv_pem_bytes, password=None, backend=default_backend())

            with open(os.path.join(extract_dir,"encrypted_aes_key.bin"),'r') as f: enc_aes = base64.b64decode(f.read())
            aes_key = rsa_cipher.decrypt_rsa(enc_aes, priv)
            
            with open(os.path.join(extract_dir,"iv.txt"),'r') as f: iv = base64.b64decode(f.read())
            enc_data = file_manager.read_file(enc_file)
            decrypted_data = aes_cipher.decrypt_aes(iv, enc_data, aes_key)

        elif algo == "ECC":
             # Similar logic for ECC...
             salt_path = os.path.join(extract_dir, "salt.txt")
             if os.path.exists(salt_path):
                 with open(salt_path,'r') as f: salt = base64.b64decode(f.read())
                 with open(os.path.join(extract_dir, "piv.txt"),'r') as f: piv = base64.b64decode(f.read())
                 with open(os.path.join(extract_dir, "encrypted_private_key.bin"),'r') as f: enc_p = base64.b64decode(f.read())
                 priv_pem_bytes = crypto_utils.decrypt_data_with_password(salt, piv, enc_p, password)
             else:
                 with open(os.path.join(extract_dir, "private_key.pem"),'rb') as f: priv_pem_bytes = f.read()
             
             from cryptography.hazmat.backends import default_backend; from cryptography.hazmat.primitives import serialization
             priv = serialization.load_pem_private_key(priv_pem_bytes, password=None, backend=default_backend())

             with open(os.path.join(extract_dir,"encrypted_aes_key.bin"),'r') as f: enc_aes_tag = base64.b64decode(f.read())
             with open(os.path.join(extract_dir,"key_iv.txt"),'r') as f: key_iv = base64.b64decode(f.read())
             with open(os.path.join(extract_dir,"ephem_pub.pem"),'rb') as f: ephem_bytes = f.read()
             
             aes_key = ecc_cipher.decrypt_ecc_hybrid(ephem_bytes, key_iv, enc_aes_tag, priv)
             
             with open(os.path.join(extract_dir,"file_iv.txt"),'r') as f: file_iv = base64.b64decode(f.read())
             enc_data = file_manager.read_file(enc_file)
             decrypted_data = aes_cipher.decrypt_aes(file_iv, enc_data, aes_key)

        out_path = os.path.join(extract_dir, orig_name)
        file_manager.write_file(out_path, decrypted_data)
        db_manager.increment_stats(message.from_user.id, "decrypt")
        with open(out_path, 'rb') as f: 
            bot.send_document(
                message.chat.id, 
                f, 
                caption=f"🔓 **Muvaffaqiyatli Ochildi!**\n\n📂 **Fayl:** `{orig_name}`",
                parse_mode="Markdown"
            )

    except Exception as e:
        import traceback
        logging.error(traceback.format_exc())
        raise ValueError(f"Dec fail: {e}")

if __name__ == '__main__':
    print("------------------------------------------------")
    print("BOT ISHGA TUSHDI! (v3.0 - Stable)")
    print("------------------------------------------------")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import time
        time.sleep(5)
