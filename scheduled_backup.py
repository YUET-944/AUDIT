"""
Scheduled backup script for the financial dashboard
"""
import schedule
import time
import logging
from datetime import datetime
import os
from backup_restore import backup_manager
import threading

logger = logging.getLogger(__name__)

def perform_backup():
    """Perform a database backup"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"automated_backup_{timestamp}"
        
        backup_path = backup_manager.create_compressed_backup(backup_name)
        logger.info(f"Automated backup completed: {backup_path}")
        
        # Optional: Clean up old backups (keep only last 7 days)
        cleanup_old_backups(days_to_keep=7)
        
    except Exception as e:
        logger.error(f"Error during automated backup: {str(e)}")

def cleanup_old_backups(days_to_keep=7):
    """Clean up backups older than specified days"""
    try:
        import os
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        backup_dir = backup_manager.backup_dir
        
        for filename in os.listdir(backup_dir):
            if filename.startswith("automated_backup_") and (filename.endswith(".db") or filename.endswith(".zip")):
                file_path = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    logger.info(f"Removed old backup: {filename}")
                    
    except Exception as e:
        logger.error(f"Error during backup cleanup: {str(e)}")

def start_scheduler():
    """Start the backup scheduler in a separate thread"""
    # Schedule daily backups at 2 AM
    schedule.every().day.at("02:00").do(perform_backup)
    
    # Schedule weekly backups (Sunday at 1 AM)
    schedule.every().sunday.at("01:00").do(perform_backup)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Backup scheduler started")

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    # For testing purposes
    print("Starting backup scheduler...")
    start_scheduler()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Backup scheduler stopped.")