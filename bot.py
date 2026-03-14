import logging
import sys
import os
import traceback
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from telegram.error import TelegramError
from database import Database
from handlers.user import UserHandlers, CATEGORY, EMAIL, PHONE, QUESTION
from handlers.admin import AdminHandlers
from handlers.group import GroupHandlers
from handlers.super_admin import SuperAdminHandlers
from config import Config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global error handler to notify super admin
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors and notify super admin"""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Prepare error message
    error_msg = f"🚨 **Bot Error Alert** 🚨\n\n"
    
    if update:
        if update.effective_user:
            error_msg += f"**User:** @{update.effective_user.username} (ID: `{update.effective_user.id}`)\n"
        if update.effective_chat:
            error_msg += f"**Chat:** {update.effective_chat.title or 'Private'} (ID: `{update.effective_chat.id}`)\n"
        if update.effective_message:
            error_msg += f"**Message:** `{update.effective_message.text}`\n"
    
    error_msg += f"\n**Error:** `{str(context.error)[:200]}`\n"
    error_msg += f"**Traceback:**\n`{traceback.format_exc()[:1000]}`"
    
    # Send to super admin
    try:
        await context.bot.send_message(
            chat_id=Config.SUPER_ADMIN_ID,
            text=error_msg,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send error to super admin: {e}")

def main():
    """Start the bot."""
    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database()
        
        # Initialize handlers
        user_handlers = UserHandlers(db)
        admin_handlers = AdminHandlers(db)
        group_handlers = GroupHandlers()
        super_admin_handlers = SuperAdminHandlers(db)
        
        # Create application
        logger.info("Creating bot application...")
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Store db in bot_data
        application.bot_data['db'] = db
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # User conversation handler for ticket creation
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', user_handlers.start),
                CallbackQueryHandler(user_handlers.button_handler, pattern='^new_ticket$')
            ],
            states={
                CATEGORY: [CallbackQueryHandler(user_handlers.category_selected, pattern='^cat_')],
                EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_email)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_phone)],
                QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_question)],
            },
            fallbacks=[
                CommandHandler('cancel', user_handlers.cancel),
                CallbackQueryHandler(user_handlers.button_handler, pattern='^cancel$')
            ],
            per_message=True,  # Changed to True to avoid warning
            name="ticket_conversation"
        )
        
        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(user_handlers.button_handler, pattern='^(my_tickets|help)$'))
        
        # Admin group commands (only work in configured admin group)
        application.add_handler(CommandHandler('pending', admin_handlers.pending))
        application.add_handler(CommandHandler('stats', admin_handlers.stats))
        application.add_handler(CommandHandler('search', admin_handlers.search))
        application.add_handler(CommandHandler('download', admin_handlers.download))
        
        # Admin action handlers
        application.add_handler(CallbackQueryHandler(admin_handlers.handle_admin_actions, pattern='^(reply_|progress_|spam_)'))
        
        # Admin reply message handler
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            admin_handlers.handle_admin_reply
        ))
        
        # Group support command (works in any group, bot checks if group is activated)
        application.add_handler(CommandHandler('support', group_handlers.support))
        
        # Super admin commands (only for super admin in private)
        application.add_handler(CommandHandler('activate', super_admin_handlers.activate_group, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('deactivate', super_admin_handlers.deactivate_group, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('listactivated', super_admin_handlers.list_activated_groups, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('deletedata', super_admin_handlers.delete_data, filters=filters.ChatType.PRIVATE))
        
        # Test if admin group is accessible (FIXED - added await)
        try:
            # We need to await this since it's a coroutine
            await application.bot.send_message(
                chat_id=Config.ADMIN_GROUP_ID,
                text="✅ **Bot is online and ready to receive tickets!**",
                parse_mode='Markdown'
            )
            logger.info(f"Successfully connected to admin group: {Config.ADMIN_GROUP_ID}")
        except Exception as e:
            logger.error(f"Failed to send message to admin group: {e}")
            # Notify super admin
            try:
                await application.bot.send_message(
                    chat_id=Config.SUPER_ADMIN_ID,
                    text=f"⚠️ **Warning:** Bot cannot send messages to admin group `{Config.ADMIN_GROUP_ID}`!\nMake sure bot is admin in that group.\n\nError: {str(e)}",
                    parse_mode='Markdown'
                )
            except Exception as e2:
                logger.error(f"Failed to notify super admin: {e2}")
        
        # Start bot
        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        logger.error(traceback.format_exc())
        # Try to notify super admin via raw request
        try:
            import requests
            requests.post(
                f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": Config.SUPER_ADMIN_ID,
                    "text": f"🚨 **FATAL BOT ERROR** 🚨\n\nBot failed to start!\nError: {str(e)}\n\nTraceback:\n`{traceback.format_exc()[:500]}`",
                    "parse_mode": "Markdown"
                }
            )
        except:
            pass
        raise

if __name__ == '__main__':
    main()
