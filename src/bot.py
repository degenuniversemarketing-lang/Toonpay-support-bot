#!/usr/bin/env python3
"""
ToonPay Support Bot
Main bot application
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PicklePersistence
)
from telegram import BotCommand

from src.config import Config
from src.database import init_db, db_session
from src.handlers import (
    user,
    admin,
    super_admin,
    group
)
from src.models import AllowedGroup

# Set up logging
logging.basicFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ToonPaySupportBot:
    def __init__(self):
        self.application = None
        self._init_database()
        
    def _init_database(self):
        """Initialize database connection"""
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _setup_handlers(self):
        """Setup all bot handlers"""
        
        # User handlers (private chat only)
        self.application.add_handler(CommandHandler("start", user.start, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(user.ticket_conv_handler)
        self.application.add_handler(user.reply_conv_handler)
        self.application.add_handler(CallbackQueryHandler(user.handle_callback, pattern="^(?!admin_).*"))
        
        # Group handlers
        self.application.add_handler(CommandHandler("support", group.support_command))
        self.application.add_handler(MessageHandler(filters.ChatType.GROUPS, group.handle_group_message))
        
        # Admin handlers (admin group only)
        self.application.add_handler(CommandHandler("stats", admin.admin_stats, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
        self.application.add_handler(CommandHandler("pending", admin.admin_pending, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
        self.application.add_handler(CommandHandler("search", admin.admin_search, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
        self.application.add_handler(CommandHandler("getdata", admin.admin_getdata, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
        self.application.add_handler(CommandHandler("admin", admin.admin_start, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
        
        # Admin callback handlers
        self.application.add_handler(CallbackQueryHandler(admin.admin_callback_handler, pattern="^admin_.*|^progress_.*|^close_.*|^view_user_.*|^pending_page_.*"))
        
        # Reply handler for admin group
        self.application.add_handler(MessageHandler(
            filters.Chat(Config.ADMIN_GROUP_ID) & filters.TEXT & ~filters.COMMAND,
            admin.admin_handle_reply
        ))
        
        # Super admin handlers (private chat only)
        self.application.add_handler(CommandHandler("super", super_admin.super_admin_panel, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("addgroup", super_admin.add_group, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("removegroup", super_admin.remove_group, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("listgroups", super_admin.list_groups, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("broadcast", super_admin.broadcast, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("superstats", super_admin.super_stats, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("backup", super_admin.backup_database, filters=filters.ChatType.PRIVATE))
        self.application.add_handler(CommandHandler("categories", super_admin.manage_categories, filters=filters.ChatType.PRIVATE))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
        logger.info("All handlers setup complete")
    
    async def _error_handler(self, update, context):
        """Log errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Notify super admins
        for admin_id in Config.SUPER_ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ Bot Error:\n{context.error}"
                )
            except:
                pass
    
    async def _post_init(self, application):
        """Setup after bot initialization"""
        # Set bot commands
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("support", "Get support (in groups)"),
        ]
        
        await application.bot.set_my_commands(commands)
        
        # Store admin group ID in bot data
        application.bot_data['admin_group_id'] = Config.ADMIN_GROUP_ID
        
        logger.info("Bot post-initialization complete")
    
    def run(self):
        """Run the bot"""
        # Create persistence
        persistence = PicklePersistence(filepath="toonpay_bot_data")
        
        # Build application
        self.application = (
            Application.builder()
            .token(Config.BOT_TOKEN)
            .persistence(persistence)
            .post_init(self._post_init)
            .build()
        )
        
        # Setup handlers
        self._setup_handlers()
        
        # Start bot
        logger.info("Starting ToonPay Support Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main entry point"""
    bot = ToonPaySupportBot()
    bot.run()

if __name__ == "__main__":
    main()
