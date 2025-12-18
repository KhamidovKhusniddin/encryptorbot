import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN")
ADMIN_PASS = os.getenv("ADMIN_PASS")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "bot_downloads")
LOG_FILE = os.path.join(BASE_DIR, "bot.log")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
LOG_LEVEL = logging.INFO
BACKUP_COUNT = 3
MAX_LOG_BYTES = 10 * 1024 * 1024

# States
class States:
    IDLE = "IDLE"
    WAIT_ALGO = "WAIT_ALGO"
    WAIT_FILE_ENCRYPT = "WAIT_FILE_ENCRYPT"
    WAIT_PASSWORD_ENCRYPT = "WAIT_PASSWORD_ENCRYPT"
    WAIT_FILE_DECRYPT = "WAIT_FILE_DECRYPT"
    WAIT_PASSWORD_DECRYPT = "WAIT_PASSWORD_DECRYPT"
    ADMIN_AUTH_LOGIN = "ADMIN_AUTH_LOGIN"
    ADMIN_AUTH_PASS = "ADMIN_AUTH_PASS"
    ADMIN_BROADCAST = "ADMIN_BROADCAST"
    ADMIN_WAIT_BLOCK_ID = "ADMIN_WAIT_BLOCK_ID"
    WAIT_LANGUAGE = "WAIT_LANGUAGE"
