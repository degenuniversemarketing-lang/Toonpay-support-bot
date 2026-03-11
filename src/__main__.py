#!/usr/bin/env python3
"""
ToonPay Support Bot - Main Entry Point
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    try:
        logger.info("=" * 50)
        logger.info("🚀 Starting ToonPay Support Bot")
        logger.info("=" * 50)
        
        # Import configuration
        from src.config import config
        
        logger.info(f"📊 Configuration loaded:")
        logger.info(f"   Bot Username: {config.BOT_USERNAME}")
        logger.info(f"   Admin Group: {config.ADMIN_GROUP_ID}")
        logger.info(f"   Super Admins: {config.SUPER_ADMIN_IDS}")
        logger.info(f"   Auto Backup: {config.ENABLE_AUTO_BACKUP}")
        
        # Import and run bot
        from src.bot_runner import ToonPayBot
        
        logger.info("🤖 Initializing bot...")
        bot = ToonPayBot()
        
        logger.info("✅ Bot initialized, starting...")
        bot.run()
        
    except ImportError as e:
        logger.error(f"❌ Failed to import modules: {e}")
        logger.error("Make sure all required files are present:")
        logger.error("   - src/config.py")
        logger.error("   - src/database.py")
        logger.error("   - src/bot_runner.py")
        logger.error("   - src/handlers/*.py")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
