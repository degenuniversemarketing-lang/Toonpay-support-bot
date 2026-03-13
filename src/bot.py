#!/usr/bin/env python3
"""
ToonPay Support Bot
Main bot application
"""

import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PicklePersistence
)

from src.config import Config
from src.database import init_db
from src.handlers import (
    user,
    admin,
    super_admin,
    group
)

# Set up logging
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
        
        # Log admin group ID for debugging
        logger.info(f"ADMIN_GROUP_ID from config: {Config.ADMIN_GROUP_ID}")
        logger.info(f"Type of ADMIN_GROUP_ID: {type(Config.ADMIN_GROUP_ID)}")
        
        # ==================== USER HANDLERS (Private Chat Only) ====================
        # Start command
        self.application.add_handler(
            CommandHandler("start", user.start, filters=filters.ChatType.PRIVATE)
        )
        
        # User conversation handlers for ticket creation
        self.application.add_handler(user.ticket_conv_handler)
        self.application.add_handler(user.reply_conv_handler)
        
        # User callback handler (for buttons in private chat)
        self.application.add_handler(
            CallbackQueryHandler(user.handle_callback, pattern="^(?!admin_|reply_|progress_|close_|viewuser_).*")
        )
        
        # ==================== GROUP HANDLERS ====================
        # /support command works in allowed groups
        self.application.add_handler(
            CommandHandler("support", group.support_command)
        )
        
        # ==================== ADMIN HANDLERS (Admin Group Only) ====================
        # Single handler for all admin commands
        self.application.add_handler(
            MessageHandler(
                filters.COMMAND & filters.Chat(Config.ADMIN_GROUP_ID),
                admin.admin_command_handler
            )
        )
        
        # Admin callback handler for buttons (Reply, In Progress, View User, Close)
        self.application.add_handler(
            CallbackQueryHandler(
                admin.admin_callback_handler,
                pattern="^(reply_|progress_|close_|viewuser_)"
            )
        )
        
        # Admin reply handler for text messages (when admin clicks Reply button)
        self.application.add_handler(
            MessageHandler(
                filters.Chat(Config.ADMIN_GROUP_ID) & filters.TEXT & ~filters.COMMAND,
                admin.admin_reply_handler
            )
        )
        
        # ==================== SUPER ADMIN HANDLERS (Private Chat Only) ====================
        # Super admin panel
        self.application.add_handler(
            CommandHandler("super", super_admin.super_admin_panel, filters=filters.ChatType.PRIVATE)
        )
        
        # Group management
        self.application.add_handler(
            CommandHandler("addgroup", super_admin.add_group, filters=filters.ChatType.PRIVATE)
        )
        self.application.add_handler(
            CommandHandler("removegroup", super_admin.remove_group, filters=filters.ChatType.PRIVATE)
        )
        self.application.add_handler(
            CommandHandler("listgroups", super_admin.list_groups, filters=filters.ChatType.PRIVATE)
        )
        
        # Bot management
        self.application.add_handler(
            CommandHandler("broadcast", super_admin.broadcast, filters=filters.ChatType.PRIVATE)
        )
        self.application.add_handler(
            CommandHandler("superstats", super_admin.super_stats, filters=filters.ChatType.PRIVATE)
        )
        self.application.add_handler(
            CommandHandler("backup", super_admin.backup_database, filters=filters.ChatType.PRIVATE)
        )
        self.application.add_handler(
            CommandHandler("categories", super_admin.manage_categories, filters=filters.ChatType.PRIVATE)
        )
        
        # ==================== ERROR HANDLER ====================
        self.application.add_error_handler(self._error_handler)
        
        logger.info("All handlers setup complete")
    
    async def _error_handler(self, update, context):
        """Log errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Don't try to reply if update doesn't have message
        if update and update.effective_message:
            try:
                error_message = str(context.error)
                if "NoneType" in error_message and "len()" in error_message:
                    await update.effective_message.reply_text(
                        "⚠️ There was an error processing your request. Please try again."
                    )
                else:
                    await update.effective_message.reply_text(
                        f"⚠️ An error occurred. The admin has been notified."
                    )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")
        
        # Notify super admins
        for admin_id in Config.SUPER_ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ Bot Error:\n{context.error}"
                )
            except Exception as e:
                logger.error(f"Failed to notify super admin {admin_id}: {e}")
    
    async def _post_init(self, application):
        """Setup after bot initialization"""
        # Set bot commands
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("support", "Get support (in groups)"),
        ]
        
        try:
            await application.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
        
        # Store admin group ID in bot data
        application.bot_data['admin_group_id'] = Config.ADMIN_GROUP_ID
        
        logger.info(f"Bot post-initialization complete. Admin group ID: {Config.ADMIN_GROUP_ID}")
    
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
