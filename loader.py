import logging
import telebot
from logging.handlers import RotatingFileHandler
from config import BOT_TOKEN, LOG_FILE, LOG_LEVEL, MAX_LOG_BYTES, BACKUP_COUNT
from utils.language_manager import lang_manager
from utils import db_manager

# Configure Logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(LOG_LEVEL)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(LOG_LEVEL)

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize DB
db_manager.init_db()

# Global State Container
# In a more complex app, we might use Redis, but dict is fine for this scale
USER_STATE = {}
