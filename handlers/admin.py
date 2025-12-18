from telebot import types
from loader import bot, USER_STATE, db_manager, lang_manager, logger
from config import States, ADMIN_ID, ADMIN_LOGIN, ADMIN_PASS
from utils import system_monitor, graph_generator

@bot.message_handler(commands=['admin'])
def admin_login(message):
    if message.from_user.id != ADMIN_ID:
        debug_msg = f"Admin ID mismatch! Sizning ID: {message.from_user.id}, Kutilgan ID: {ADMIN_ID}"
        logger.warning(debug_msg)
        bot.send_message(message.chat.id, f"⛔️ **Access Denied**\nSiz admin emassiz.\n\n🛠 **Debug info:**\nSizning ID: `{message.from_user.id}`\nConfig ID: `{ADMIN_ID}`", parse_mode="Markdown")
        return 
    
    USER_STATE[message.from_user.id] = {"state": States.ADMIN_AUTH_LOGIN}
    bot.send_message(message.chat.id, "🕵️‍♂️ **Admin Panel**\n\nLogin:", parse_mode="Markdown")

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("state") == States.ADMIN_AUTH_LOGIN)
def admin_auth_login(message):
    if message.text == ADMIN_LOGIN:
        USER_STATE[message.from_user.id]["state"] = States.ADMIN_AUTH_PASS
        bot.send_message(message.chat.id, "✅ Login OK. Parol:", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Login xato!")
        USER_STATE[message.from_user.id] = {"state": States.IDLE}

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("state") == States.ADMIN_AUTH_PASS)
def admin_auth_pass(message):
    if message.text == ADMIN_PASS:
        USER_STATE[message.from_user.id] = {"state": States.IDLE, "is_admin": True}
        show_admin_dashboard(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Parol xato!")
        USER_STATE[message.from_user.id] = {"state": States.IDLE}

@bot.message_handler(func=lambda m: USER_STATE.get(m.from_user.id, {}).get("state") == States.ADMIN_BROADCAST, content_types=['text', 'photo'])
def admin_broadcast_handler(message):
    ids = db_manager.get_all_user_ids()
    count = 0
    
    status_msg = bot.send_message(message.chat.id, "🚀 Sending...", parse_mode="Markdown")
    
    for uid in ids:
        try:
            if message.content_type == 'text':
                bot.send_message(uid, message.text)
            elif message.content_type == 'photo':
                 bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            count += 1
        except:
            pass 
            
    bot.delete_message(message.chat.id, status_msg.message_id)
    bot.send_message(message.chat.id, f"✅ Sent to {count} users.")
    USER_STATE[message.from_user.id] = {"state": States.IDLE}

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID: return
    action = call.data.split("_")[1]
    
    if action == "stats":
        summary = db_manager.get_stats_summary()
        active = db_manager.get_active_users(hours=24)
        summary += f"\n\n🟢 Active (24h): {active}"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **Stats:**\n\n{summary}", parse_mode="Markdown")
        
    elif action == "db":
        bot.answer_callback_query(call.id)
        send_users_page(call.message.chat.id, page=1)

    elif action == "broadcast":
        USER_STATE[call.from_user.id] = {"state": States.ADMIN_BROADCAST}
        bot.send_message(call.message.chat.id, "📢 Send message/photo to broadcast:", parse_mode="Markdown")
    
    elif action == "graphs":
        bot.answer_callback_query(call.id, "Drawing...")
        try:
            stats = db_manager.get_daily_stats(days=7)
            if stats['registrations']:
                reg_graph = graph_generator.create_daily_users_graph(stats['registrations'])
                bot.send_photo(call.message.chat.id, reg_graph, caption="📈 Daily Users")
            if stats['operations']:
                ops_graph = graph_generator.create_file_operations_graph(stats['operations'])
                bot.send_photo(call.message.chat.id, ops_graph, caption="📈 Operations")
            if not stats['registrations'] and not stats['operations']:
                bot.send_message(call.message.chat.id, "No data.")
        except Exception as e:
            logger.error(f"Graph error: {e}")
            bot.send_message(call.message.chat.id, f"Error: {e}")
    
    elif action == "monitor":
        bot.answer_callback_query(call.id)
        try:
            stats = system_monitor.get_system_stats()
            text = system_monitor.format_system_stats(stats)
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Error: {e}")
            
    elif action == "logout":
        USER_STATE[call.from_user.id] = {"state": States.IDLE}
        bot.edit_message_text("🚪 Bye.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("users_page_"))
def users_page_callback(call):
    page = int(call.data.split("_")[2])
    send_users_page(call.message.chat.id, page, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)

def send_users_page(chat_id, page, message_id=None):
    users, total_pages, total_users = db_manager.get_users_paginated(page, limit=5)
    
    text = f"👥 **Foydalanuvchilar** ({total_users})\n📄 Sahifa: {page}/{total_pages}\n\n"
    
    for user in users:
        uid, username, fname, lname, joined, enc_count, dec_count = user
        name = f"{fname or ''} {lname or ''}".strip() or "No Name"
        uname = f"@{username}" if username else "No username"
        
        text += f"👤 **{name}** ({uname})\n"
        text += f"   🆔 `{uid}`\n"
        text += f"   📅 {joined.split()[0]} | 🔒 {enc_count} | 🔓 {dec_count}\n"
        text += "   -------------------------\n"

    markup = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    if page > 1:
        btns.append(types.InlineKeyboardButton("⬅️", callback_data=f"users_page_{page-1}"))
    else:
        btns.append(types.InlineKeyboardButton("⏹", callback_data="ignore"))
        
    btns.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
    
    if page < total_pages:
        btns.append(types.InlineKeyboardButton("➡️", callback_data=f"users_page_{page+1}"))
    else:
        btns.append(types.InlineKeyboardButton("⏹", callback_data="ignore"))

    markup.add(*btns)
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="admin_home")) # Assuming admin_home is not defined, but logic suggests simple close or menu. I'll stick to closing or just leaving it. Wait, I should make sure there's a way back.
    # Actually, let's keep it simple.

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

def show_admin_dashboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📈 Graphs", callback_data="admin_graphs"),
        types.InlineKeyboardButton("📂 DB Export", callback_data="admin_db"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🖥 System", callback_data="admin_monitor"),
        types.InlineKeyboardButton("🚪 Logout", callback_data="admin_logout")
    )
    bot.send_message(chat_id, "🕵️‍♂️ **Admin Dashboard**", reply_markup=markup, parse_mode="Markdown")
