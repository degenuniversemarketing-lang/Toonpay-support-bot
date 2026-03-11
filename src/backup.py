# src/backup.py
import os
import subprocess
from datetime import datetime
import schedule
import time
import threading
import logging
from pathlib import Path

from src.config import config
from src.database import db

logger = logging.getLogger(__name__)

class BackupManager:
    
    BACKUP_DIR = Path("backups")
    
    @classmethod
    def ensure_backup_dir(cls):
        """Ensure backup directory exists"""
        cls.BACKUP_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def create_backup(cls) -> str:
        """Create database backup"""
        try:
            cls.ensure_backup_dir()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = cls.BACKUP_DIR / f"backup_{timestamp}.sql"
            
            # Extract database URL parts
            db_url = config.DATABASE_URL
            
            if db_url.startswith('postgresql'):
                # PostgreSQL backup
                # Format: postgresql://user:pass@host:port/dbname
                import urllib.parse
                
                parsed = urllib.parse.urlparse(db_url)
                dbname = parsed.path[1:]  # Remove leading /
                user = parsed.username
                password = parsed.password
                host = parsed.hostname
                port = parsed.port or 5432
                
                # Set PGPASSWORD environment variable
                env = os.environ.copy()
                env['PGPASSWORD'] = password
                
                # Run pg_dump
                cmd = [
                    'pg_dump',
                    '-h', host,
                    '-p', str(port),
                    '-U', user,
                    '-d', dbname,
                    '-f', str(filename)
                ]
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Backup created: {filename}")
                    return str(filename)
                else:
                    logger.error(f"Backup failed: {result.stderr}")
                    return None
            
            elif db_url.startswith('sqlite'):
                # SQLite backup - just copy the file
                import shutil
                
                db_path = db_url.replace('sqlite:///', '')
                shutil.copy2(db_path, filename)
                logger.info(f"Backup created: {filename}")
                return str(filename)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    @classmethod
    def restore_backup(cls, backup_file: str) -> bool:
        """Restore database from backup"""
        try:
            db_url = config.DATABASE_URL
            
            if db_url.startswith('postgresql'):
                import urllib.parse
                
                parsed = urllib.parse.urlparse(db_url)
                dbname = parsed.path[1:]
                user = parsed.username
                password = parsed.password
                host = parsed.hostname
                port = parsed.port or 5432
                
                env = os.environ.copy()
                env['PGPASSWORD'] = password
                
                # Drop and recreate database
                drop_cmd = [
                    'dropdb',
                    '-h', host,
                    '-p', str(port),
                    '-U', user,
                    '--if-exists',
                    dbname
                ]
                subprocess.run(drop_cmd, env=env, capture_output=True)
                
                create_cmd = [
                    'createdb',
                    '-h', host,
                    '-p', str(port),
                    '-U', user,
                    dbname
                ]
                subprocess.run(create_cmd, env=env, capture_output=True)
                
                # Restore from backup
                restore_cmd = [
                    'psql',
                    '-h', host,
                    '-p', str(port),
                    '-U', user,
                    '-d', dbname,
                    '-f', backup_file
                ]
                
                result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Restored from: {backup_file}")
                    return True
                else:
                    logger.error(f"Restore failed: {result.stderr}")
                    return False
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    @classmethod
    def cleanup_old_backups(cls, keep_days: int = 7):
        """Delete backups older than keep_days"""
        try:
            cls.ensure_backup_dir()
            cutoff = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            
            for backup_file in cls.BACKUP_DIR.glob("backup_*.sql"):
                if backup_file.stat().st_mtime < cutoff:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file}")
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    @classmethod
    def auto_backup_job(cls):
        """Job to run automatic backup"""
        logger.info("Running automatic backup...")
        backup_file = cls.create_backup()
        
        if backup_file and config.BACKUP_GROUP_ID:
            # Send backup to Telegram group
            try:
                from src.bot import application
                
                with open(backup_file, 'rb') as f:
                    application.bot.send_document(
                        chat_id=config.BACKUP_GROUP_ID,
                        document=f,
                        filename=f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                        caption="✅ Automatic backup completed"
                    )
            except Exception as e:
                logger.error(f"Failed to send backup to Telegram: {e}")
        
        # Cleanup old backups
        cls.cleanup_old_backups()

def start_backup_scheduler():
    """Start the backup scheduler in a separate thread"""
    if not config.ENABLE_AUTO_BACKUP:
        return
    
    def run_scheduler():
        # Schedule daily backup
        schedule.every(config.BACKUP_INTERVAL_HOURS).hours.do(BackupManager.auto_backup_job)
        
        # Run initial backup
        BackupManager.auto_backup_job()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    logger.info(f"Backup scheduler started (every {config.BACKUP_INTERVAL_HOURS} hours)")
