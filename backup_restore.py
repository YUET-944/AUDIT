"""
Database backup and restore functionality
"""
import sqlite3
import shutil
import os
import zipfile
import json
from datetime import datetime
import logging
import traceback
from database import get_db_connection

logger = logging.getLogger(__name__)

class DatabaseBackupRestore:
    def __init__(self, db_path='finance.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name=None):
        """Create a backup of the database"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
            
            # Create backup file path
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
            
            # Copy the database file
            shutil.copy2(self.db_path, backup_path)
            
            # Create a metadata file with backup information
            metadata = {
                'backup_name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'source_db': self.db_path,
                'file_size': os.path.getsize(backup_path),
                'tables': self._get_table_info()
            }
            
            metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def _get_table_info(self):
        """Get information about all tables in the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            table_info = {}
            for table in tables:
                table_name = table[0]
                # Get row count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                table_info[table_name] = {'row_count': row_count}
            
            conn.close()
            return table_info
            
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}\n{traceback.format_exc()}")
            return {}
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.db'):
                    backup_name = file[:-3]  # Remove .db extension
                    metadata_file = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
                    
                    metadata = {}
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    
                    backups.append({
                        'name': backup_name,
                        'file': file,
                        'path': os.path.join(self.backup_dir, file),
                        'size': os.path.getsize(os.path.join(self.backup_dir, file)),
                        'created': metadata.get('timestamp', 'Unknown'),
                        'metadata': metadata
                    })
            
            # Sort by creation time (most recent first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}\n{traceback.format_exc()}")
            return []
    
    def restore_backup(self, backup_name):
        """Restore database from a backup"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create a backup of current database before restoring
            current_backup_path = self.create_backup(f"before_restore_{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            logger.info(f"Created backup of current database before restore: {current_backup_path}")
            
            # Close any existing connections (this is important)
            # In a real application, you'd need to ensure all connections are closed
            
            # Restore the database
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"Database restored successfully from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def delete_backup(self, backup_name):
        """Delete a backup file"""
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.db")
            metadata_path = os.path.join(self.backup_dir, f"{backup_name}_metadata.json")
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            logger.info(f"Backup deleted: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def create_compressed_backup(self, backup_name=None):
        """Create a compressed backup as a zip file"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"compressed_backup_{timestamp}"
            
            # Create temporary backup
            temp_backup_path = os.path.join(self.backup_dir, f"temp_{backup_name}.db")
            shutil.copy2(self.db_path, temp_backup_path)
            
            # Create zip file
            zip_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_backup_path, os.path.basename(temp_backup_path))
                
                # Add metadata
                metadata = {
                    'backup_name': backup_name,
                    'timestamp': datetime.now().isoformat(),
                    'source_db': self.db_path,
                    'original_size': os.path.getsize(temp_backup_path),
                    'compressed_size': os.path.getsize(zip_path)
                }
                
                # Write metadata to zip as a separate file
                metadata_str = json.dumps(metadata, indent=2)
                zipf.writestr(f"{backup_name}_metadata.json", metadata_str)
            
            # Remove temporary backup
            os.remove(temp_backup_path)
            
            logger.info(f"Compressed backup created: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating compressed backup: {str(e)}\n{traceback.format_exc()}")
            raise e

# Global backup instance
backup_manager = DatabaseBackupRestore()

# Helper functions for the main app
def create_database_backup():
    """Create a database backup for the main app"""
    try:
        backup_path = backup_manager.create_backup()
        return backup_path
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}\n{traceback.format_exc()}")
        raise e

def get_available_backups():
    """Get list of available backups for the main app"""
    try:
        backups = backup_manager.list_backups()
        return backups
    except Exception as e:
        logger.error(f"Error getting available backups: {str(e)}\n{traceback.format_exc()}")
        return []

def restore_from_backup(backup_name):
    """Restore from a specific backup for the main app"""
    try:
        success = backup_manager.restore_backup(backup_name)
        return success
    except Exception as e:
        logger.error(f"Error restoring from backup: {str(e)}\n{traceback.format_exc()}")
        raise e

def delete_backup(backup_name):
    """Delete a specific backup for the main app"""
    try:
        success = backup_manager.delete_backup(backup_name)
        return success
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}\n{traceback.format_exc()}")
        raise e