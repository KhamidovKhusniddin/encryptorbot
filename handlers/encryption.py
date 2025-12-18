import os
import shutil
import base64
import time
import logging
from telebot import types
from loader import bot, USER_STATE, db_manager, lang_manager, logger
from config import States, DOWNLOADS_DIR, MAX_FILE_SIZE
from encryption import aes_cipher, rsa_cipher, ecc_cipher
from utils import file_manager, crypto_utils

try:
    import pyzipper
except ImportError:
    pyzipper = None

# --- Helpers ---
# --- Helpers ---
def secure_delete(path):
    if os.path.isfile(path):
        try:
            length = os.path.getsize(path)
            with open(path, "wb") as f:
                f.write(os.urandom(length))
        except: pass
        os.remove(path)

def cleanup(path):
    if os.path.exists(path):
        if os.path.isfile(path): secure_delete(path)
        else: shutil.rmtree(path, ignore_errors=True)
    
    dir_path = os.path.dirname(path)
    if os.path.exists(dir_path) and "downloads" in dir_path:
        shutil.rmtree(dir_path, ignore_errors=True)

# --- Handlers ---

@bot.callback_query_handler(func=lambda call: call.data in ["AES", "RSA", "ECC"])
def algo_callback(call):
    user_id = call.from_user.id
    choice = call.data
    USER_STATE[user_id] = {"state": States.WAIT_FILE_ENCRYPT, "algo": choice}
    
    lang = db_manager.get_user_language(user_id)
    bot.edit_message_text(
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        text=lang_manager.get_text(lang, 'algo_selected', algo=choice),
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['document', 'photo'])
def handle_files(message):
    user_id = message.from_user.id
    state_data = USER_STATE.get(user_id, {"state": States.IDLE})
    state = state_data.get("state")
    
    if db_manager.is_blocked(user_id): return
    if state == States.ADMIN_BROADCAST: return # Handled in admin.py

    try:
        # 1. Info Extraction
        if message.content_type == 'document':
            file_id = message.document.file_id
            file_name = message.document.file_name
            file_size = message.document.file_size
        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            file_name = f"photo_{file_id[:10]}.jpg"
            file_size = message.photo[-1].file_size
        else: return

        # 2. Check Size
        if file_size and file_size > MAX_FILE_SIZE:
            lang = db_manager.get_user_language(user_id)
            size_mb = file_size / (1024 * 1024)
            bot.send_message(message.chat.id, lang_manager.get_text(lang, 'file_too_large', size=f"{size_mb:.1f}"))
            return

        # 3. Encryption Flow
        if state == States.WAIT_FILE_ENCRYPT:
            bot.send_message(message.chat.id, "📥 Downloading...")
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            download_dir = os.path.join(DOWNLOADS_DIR, str(user_id))
            os.makedirs(download_dir, exist_ok=True)
            file_path = os.path.join(download_dir, file_name)
            
            with open(file_path, 'wb') as f: f.write(downloaded_file)
            
            USER_STATE[user_id]["file_path"] = file_path
            USER_STATE[user_id]["original_name"] = file_name
            USER_STATE[user_id]["state"] = States.WAIT_PASSWORD_ENCRYPT
            
            lang = db_manager.get_user_language(user_id)
            bot.send_message(message.chat.id, lang_manager.get_text(lang, 'enter_password'), parse_mode="Markdown")

        # 4. Decryption Flow
        elif state == States.WAIT_FILE_DECRYPT:
            if not file_name.endswith('.zip'):
                bot.send_message(message.chat.id, "⚠️ Only .zip files!")
                return
            
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
            
            download_dir = os.path.join(DOWNLOADS_DIR, str(user_id) + "_dec")
            os.makedirs(download_dir, exist_ok=True)
            zip_path = os.path.join(download_dir, file_name)
            with open(zip_path, 'wb') as f: f.write(downloaded)
            
            extract_dir = os.path.join(download_dir, "extracted")
            if os.path.exists(extract_dir): shutil.rmtree(extract_dir)

            # Check encryption
            is_encrypted = False
            if pyzipper:
                try:
                    with pyzipper.AESZipFile(zip_path) as zf:
                        for info in zf.infolist():
                            if info.flag_bits & 0x1: is_encrypted = True; break
                except: is_encrypted = True
            
            if is_encrypted:
                lang = db_manager.get_user_language(user_id)
                USER_STATE[user_id] = {
                    "state": States.WAIT_PASSWORD_DECRYPT, 
                    "zip_path": zip_path, 
                    "extract_dir": extract_dir,
                    "attempts": 0
                }
                bot.send_message(message.chat.id, lang_manager.get_text(lang, 'file_protected'), parse_mode="Markdown")
            else:
                try:
                    lang = db_manager.get_user_language(user_id)
                    bot.send_message(message.chat.id, lang_manager.get_text(lang, 'decrypting'))
                    process_decryption_final(message, zip_path, extract_dir, None)
                    USER_STATE[user_id] = {"state": States.IDLE}
                except Exception as e:
                     logger.error(e)
                     bot.send_message(message.chat.id, "Error or password needed.")

    except Exception as e:
        logger.error(f"File handle error: {e}")
        bot.send_message(message.chat.id, "❌ Error occurred.")

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("state") == States.WAIT_PASSWORD_ENCRYPT)
def handle_enc_password(message):
    user_id = message.from_user.id
    password = message.text.strip()
    state_data = USER_STATE.get(user_id)
    lang = db_manager.get_user_language(user_id)

    # Password Policy
    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        bot.send_message(message.chat.id, lang_manager.get_text(lang, 'password_weak'), parse_mode="Markdown")
        return

    progress_msg = bot.send_message(message.chat.id, "⏳ 0% [░░░░░░░░░░]")
    
    try:
        # Animation
        for i in range(1, 4):
            time.sleep(0.2)
            bars = "█" * (i*3) + "░" * (10 - i*3)
            try: bot.edit_message_text(f"⏳ {i*30}% [{bars}]", message.chat.id, progress_msg.message_id)
            except: pass
        
        bot.edit_message_text(lang_manager.get_text(lang, 'encrypting'), message.chat.id, progress_msg.message_id)

        algo = state_data["algo"]
        file_path = state_data["file_path"]
        orig_name = state_data["original_name"]

        if algo == "AES": process_aes(message, file_path, orig_name, password)
        elif algo == "RSA": process_rsa(message, file_path, orig_name, password)
        elif algo == "ECC": process_ecc(message, file_path, orig_name, password)
        
        db_manager.increment_stats(user_id, "encrypt")
        db_manager.add_file_history(user_id, orig_name, algo, "encrypt")
        USER_STATE[user_id]["last_password"] = password

        try: bot.delete_message(message.chat.id, progress_msg.message_id)
        except: pass
        
        bot.send_message(message.chat.id, "💡 Use /qrcode to get a QR code for your password.")

    except Exception as e:
        logger.error(f"Enc Error: {e}")
        bot.send_message(message.chat.id, f"❌ Error: {e}")
    finally:
        cleanup(state_data["file_path"])
        USER_STATE[user_id]["state"] = States.IDLE

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("state") == States.WAIT_PASSWORD_DECRYPT)
def handle_dec_password(message):
    user_id = message.from_user.id
    password = message.text.strip()
    state_data = USER_STATE.get(user_id)
    zip_path = state_data["zip_path"]
    extract_dir = state_data["extract_dir"]
    attempts = state_data.get("attempts", 0)
    lang = db_manager.get_user_language(user_id)

    bot.send_message(message.chat.id, lang_manager.get_text(lang, 'decrypting'))
    
    try:
        process_decryption_final(message, zip_path, extract_dir, password)
        cleanup(zip_path)
        USER_STATE[user_id] = {"state": States.IDLE}
    except ValueError:
        attempts += 1
        USER_STATE[user_id]["attempts"] = attempts
        if attempts < 3:
            bot.send_message(message.chat.id, lang_manager.get_text(lang, 'password_incorrect', attempts=attempts))
        else:
            bot.send_message(message.chat.id, lang_manager.get_text(lang, 'too_many_attempts'))
            cleanup(zip_path)
            USER_STATE[user_id] = {"state": States.IDLE}
    except Exception as e:
        logger.error(f"Dec Error: {e}")
        bot.send_message(message.chat.id, f"Error: {e}")
        cleanup(zip_path)
        USER_STATE[user_id] = {"state": States.IDLE}

# --- Logic Functions ---

def process_aes(message, file_path, orig_name, password):
    data = file_manager.read_file(file_path)
    aes_key = aes_cipher.generate_aes_key()
    iv, ciphertext = aes_cipher.encrypt_aes(data, aes_key)
    
    salt, piv, enc_aes_key = crypto_utils.encrypt_data_with_password(aes_key, password)
    
    enc_path = file_path + ".enc"
    file_manager.write_file(enc_path, ciphertext)
    
    zip_path = file_path + "_secure.zip"
    file_manager.create_secure_zip(
        zip_path, enc_path, enc_aes_key, 
        {"iv": iv, "algo": b"AES", "filename": orig_name.encode(), "salt": salt, "piv": piv},
        password=password
    )
    with open(zip_path, 'rb') as f: 
        bot.send_document(message.chat.id, f, visible_file_name=orig_name+".zip", caption=f"🔐 Password: `{password}`", parse_mode="Markdown")

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
    
    # We duplicate zip logic here for now as it was in main.py, but ideally move to file_manager
    if pyzipper:
        with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode())
            write_rsa_zip_content(zf, enc_path, enc_aes_key, iv, orig_name, enc_priv_pem, salt, piv)
    else:
        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zf:
            write_rsa_zip_content(zf, enc_path, enc_aes_key, iv, orig_name, enc_priv_pem, salt, piv)

    with open(zip_path, 'rb') as f:
         bot.send_document(message.chat.id, f, visible_file_name=orig_name+".zip", caption=f"🔐 RSA Password: `{password}`", parse_mode="Markdown")

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

    with open(zip_path, 'rb') as f:
         bot.send_document(message.chat.id, f, visible_file_name=orig_name+".zip", caption=f"🔐 ECC Password: `{password}`", parse_mode="Markdown")

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
    extracted = file_manager.extract_secure_zip(zip_path, extract_dir, password)
    
    algo_file = os.path.join(extract_dir, "algo.txt")
    if os.path.exists(algo_file):
        with open(algo_file, 'r') as f: algo = f.read().strip()
    elif os.path.exists(os.path.join(extract_dir, "key.txt")): algo = "AES"
    else: 
        raise ValueError("Unknown format")

    if "AES" in algo: algo = "AES"
    if "RSA" in algo: algo = "RSA"
    if "ECC" in algo: algo = "ECC"
    
    enc_file = None
    for name in os.listdir(extract_dir):
        if name.endswith(".enc") or name == "user_file_encrypted.txt": enc_file = os.path.join(extract_dir, name); break
    if not enc_file: raise ValueError("No encrypted file")
    
    filename_file = os.path.join(extract_dir, "filename.txt")
    orig_name = "decrypted.file"
    if os.path.exists(filename_file):
        with open(filename_file, 'r') as f:
            try: orig_name = base64.b64decode(f.read().strip()).decode()
            except: pass

    decrypted_data = None
    
    if algo == "AES":
        salt_path = os.path.join(extract_dir, "salt.txt")
        if os.path.exists(salt_path):
             with open(salt_path,'r') as f: salt = base64.b64decode(f.read())
             with open(os.path.join(extract_dir, "piv.txt"),'r') as f: piv = base64.b64decode(f.read())
             with open(os.path.join(extract_dir, "key.txt"),'r') as f: enc_key = base64.b64decode(f.read())
             
             aes_key = crypto_utils.decrypt_data_with_password(salt, piv, enc_key, password)
        else:
             with open(os.path.join(extract_dir, "key.txt"),'r') as f: aes_key = base64.b64decode(f.read())
        
        with open(os.path.join(extract_dir, "iv.txt"),'r') as f: iv = base64.b64decode(f.read())
        enc_data = file_manager.read_file(enc_file)
        decrypted_data = aes_cipher.decrypt_aes(iv, enc_data, aes_key)
        
    elif algo == "RSA":
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
        with open(os.path.join(extract_dir,"iv.txt"),'r') as f: iv = base64.b64decode(f.read())
        
        aes_key = rsa_cipher.decrypt_rsa(enc_aes, priv)
        enc_data = file_manager.read_file(enc_file)
        decrypted_data = aes_cipher.decrypt_aes(iv, enc_data, aes_key)
        
    elif algo == "ECC":
         with open(os.path.join(extract_dir, "salt.txt"),'r') as f: salt = base64.b64decode(f.read())
         with open(os.path.join(extract_dir, "piv.txt"),'r') as f: piv = base64.b64decode(f.read())
         with open(os.path.join(extract_dir, "encrypted_private_key.bin"),'r') as f: enc_p = base64.b64decode(f.read())
         
         priv_pem_bytes = crypto_utils.decrypt_data_with_password(salt, piv, enc_p, password)
         
         from cryptography.hazmat.backends import default_backend; from cryptography.hazmat.primitives import serialization
         priv = serialization.load_pem_private_key(priv_pem_bytes, password=None, backend=default_backend())
         
         with open(os.path.join(extract_dir,"encrypted_aes_key.bin"),'r') as f: enc_aes_tag = base64.b64decode(f.read())
         with open(os.path.join(extract_dir,"key_iv.txt"),'r') as f: key_iv = base64.b64decode(f.read())
         with open(os.path.join(extract_dir,"file_iv.txt"),'r') as f: file_iv = base64.b64decode(f.read())
         with open(os.path.join(extract_dir,"ephem_pub.pem"),'rb') as f: ephem_pub_bytes = f.read()
         
         aes_key = ecc_cipher.decrypt_ecc_hybrid(enc_aes_tag, key_iv, ephem_pub_bytes, priv)
         enc_data = file_manager.read_file(enc_file)
         decrypted_data = aes_cipher.decrypt_aes(file_iv, enc_data, aes_key)
    
    # Send back
    out_path = os.path.join(extract_dir, orig_name)
    with open(out_path, 'wb') as f: f.write(decrypted_data)
    with open(out_path, 'rb') as f: bot.send_document(message.chat.id, f, caption="🔓 Decrypted!")
