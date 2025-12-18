from loader import bot, logger
from config import DOWNLOADS_DIR
from utils.file_cleaner import FileCleaner, start_cleanup_scheduler
from utils.commands import set_default_commands
import handlers.user
import handlers.admin
import handlers.encryption

if __name__ == "__main__":
    logger.info("🚀 Starting Bot...")
    
    # Set Commands
    set_default_commands()

    
    # Start File Cleaner
    file_cleaner = FileCleaner(downloads_dir=DOWNLOADS_DIR, max_age_hours=24)
    start_cleanup_scheduler(file_cleaner, interval_hours=1)
    
    # Start Polling
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
