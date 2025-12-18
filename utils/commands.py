from telebot import types
from loader import bot

def set_default_commands():
    bot.set_my_commands([
        types.BotCommand("start", "♻️ Restart / Main Menu"),
        types.BotCommand("help", "📚 Help & Instructions"),
        types.BotCommand("language", "🌐 Change Language"),
        types.BotCommand("history", "📜 File History"),
        types.BotCommand("qrcode", "📱 Get Password QR"),
        types.BotCommand("admin", "🕵️‍♂️ Admin Panel")
    ])
