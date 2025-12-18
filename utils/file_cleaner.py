import os
import time
import shutil
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileCleaner:
    def __init__(self, downloads_dir="downloads", max_age_hours=24):
        """
        Initialize file cleaner
        
        Args:
            downloads_dir: Directory to clean
            max_age_hours: Maximum age of files in hours before deletion
        """
        self.downloads_dir = downloads_dir
        self.max_age_hours = max_age_hours
    
    def clean_old_files(self):
        """Remove files older than max_age_hours"""
        if not os.path.exists(self.downloads_dir):
            return
        
        now = datetime.now()
        cutoff_time = now - timedelta(hours=self.max_age_hours)
        
        cleaned_count = 0
        cleaned_size = 0
        
        for user_dir in os.listdir(self.downloads_dir):
            user_path = os.path.join(self.downloads_dir, user_dir)
            
            if not os.path.isdir(user_path):
                continue
            
            try:
                # Check directory modification time
                dir_mtime = datetime.fromtimestamp(os.path.getmtime(user_path))
                
                if dir_mtime < cutoff_time:
                    # Calculate size before deletion
                    dir_size = self._get_dir_size(user_path)
                    
                    # Remove directory
                    shutil.rmtree(user_path)
                    
                    cleaned_count += 1
                    cleaned_size += dir_size
                    
                    logger.info(f"Cleaned old directory: {user_path} ({dir_size / 1024 / 1024:.2f} MB)")
            
            except Exception as e:
                logger.error(f"Error cleaning directory {user_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleanup complete: {cleaned_count} directories, {cleaned_size / 1024 / 1024:.2f} MB freed")
        
        return cleaned_count, cleaned_size
    
    def _get_dir_size(self, path):
        """Calculate total size of directory"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size

def start_cleanup_scheduler(cleaner: FileCleaner, interval_hours=1):
    """
    Start background cleanup scheduler
    
    Args:
        cleaner: FileCleaner instance
        interval_hours: How often to run cleanup (in hours)
    """
    import threading
    
    def cleanup_loop():
        while True:
            try:
                cleaner.clean_old_files()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            
            # Sleep for interval
            time.sleep(interval_hours * 3600)
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info(f"File cleanup scheduler started (interval: {interval_hours}h, max age: {cleaner.max_age_hours}h)")
