import logging
import sys
import os
import traceback
import asyncio
import requests
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
from handlers.user import UserHandlers, LANGUAGE, CATEGORY, NAME, EMAIL, PHONE, QUESTION
from handlers.admin import AdminHandlers
from handlers.group import GroupHandlers
from handlers.super_admin import SuperAdminHandlers
from handlers.custom import CustomCommandHandler
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

async def remove_persistent_menu(application: Application):
    """Remove persistent menu buttons and commands"""
    try:
        # Remove the menu button (the buttons at bottom)
        await application.bot.set_chat_menu_button(
            chat_id=None,  # None means default for all users
            menu_button={"type": "default"}  # This removes custom button
        )
        
        # Clear all commands (removes /command suggestions)
        await application.bot.delete_my_commands(scope={"type": "default"})
        await application.bot.delete_my_commands(scope={"type": "all_private_chats"})
        await application.bot.delete_my_commands(scope={"type": "all_group_chats"})
        
        logger.info("✅ Persistent menu and commands removed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to remove menu: {e}")
        return False

async def post_init(application: Application) -> None:
    """Run after bot initialization"""
    # Remove persistent menu buttons first
    await remove_persistent_menu(application)
    
    # Test admin group connection
    try:
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

def main():
    """Start the bot."""
    try:
        # Delete any existing webhook first
        webhook_url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
        response = requests.post(webhook_url)
        if response.status_code == 200:
            logger.info("✅ Webhook deleted via direct API call")
        else:
            logger.warning(f"⚠️ Webhook deletion returned: {response.text}")
        
        # Initialize database
        logger.info("Initializing database...")
        db = Database()
        
        # Initialize handlers
        user_handlers = UserHandlers(db)
        admin_handlers = AdminHandlers(db)
        group_handlers = GroupHandlers()
        super_admin_handlers = SuperAdminHandlers(db)
        custom_handler = CustomCommandHandler(db)
        
        # Create application
        logger.info("Creating bot application...")
        application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
        
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
                LANGUAGE: [CallbackQueryHandler(user_handlers.language_selected, pattern='^lang_')],
                CATEGORY: [CallbackQueryHandler(user_handlers.category_selected, pattern='^cat_')],
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_name)],
                EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_email)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_phone)],
                QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_question)],
            },
            fallbacks=[
                CommandHandler('cancel', user_handlers.cancel),
                CallbackQueryHandler(user_handlers.button_handler, pattern='^cancel$')
            ],
            per_message=False,
            name="ticket_conversation"
        )
        
        # Add handlers
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(user_handlers.button_handler, pattern='^(my_tickets|help)$'))
        
        # Admin group commands
        application.add_handler(CommandHandler('pending', admin_handlers.pending))
        application.add_handler(CommandHandler('stats', admin_handlers.stats))
        application.add_handler(CommandHandler('search', admin_handlers.search))
        application.add_handler(CommandHandler('download', admin_handlers.download))
        application.add_handler(CommandHandler('download_solved', admin_handlers.download_solved))
        application.add_handler(CommandHandler('download_pending', admin_handlers.download_pending))
        
        # Admin action handlers
        application.add_handler(CallbackQueryHandler(admin_handlers.handle_admin_actions, pattern='^(reply_|progress_|spam_)'))
        
        # Admin reply message handler
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            admin_handlers.handle_admin_reply
        ))
        
        # Group support command
        application.add_handler(CommandHandler('support', group_handlers.support))
        
        # SUPER ADMIN COMMANDS - Group Management
        application.add_handler(CommandHandler('activate', super_admin_handlers.activate_group, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('deactivate', super_admin_handlers.deactivate_group, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('listactivated', super_admin_handlers.list_activated_groups, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - Data Management
        application.add_handler(CommandHandler('deletedata', super_admin_handlers.delete_data, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - Custom Filters
        application.add_handler(CommandHandler('addfilter', super_admin_handlers.add_filter, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('removefilter', super_admin_handlers.remove_filter, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('listfilters', super_admin_handlers.list_filters, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - User Broadcast
        application.add_handler(CommandHandler('broadcast', super_admin_handlers.broadcast, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - Group Broadcast (NEW)
        application.add_handler(CommandHandler('broadcast_groups', super_admin_handlers.broadcast_groups, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('broadcast_group', super_admin_handlers.broadcast_group, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - Channel Broadcast (NEW)
        application.add_handler(CommandHandler('broadcast_channels', super_admin_handlers.broadcast_channels, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('broadcast_channel', super_admin_handlers.broadcast_channel, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - Channel Management (NEW)
        application.add_handler(CommandHandler('addchannel', super_admin_handlers.add_channel, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('removechannel', super_admin_handlers.remove_channel, filters=filters.ChatType.PRIVATE))
        application.add_handler(CommandHandler('listchannels', super_admin_handlers.list_channels, filters=filters.ChatType.PRIVATE))
        
        # SUPER ADMIN COMMANDS - Statistics
        application.add_handler(CommandHandler('allstats', super_admin_handlers.all_stats, filters=filters.ChatType.PRIVATE))
        
        # Custom commands handler (must be last - low priority)
        application.add_handler(MessageHandler(
            filters.COMMAND & filters.ChatType.PRIVATE,
            custom_handler.handle
        ), group=999)
        
        # Start bot
        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        logger.error(traceback.format_exc())
        # Try to notify super admin via raw request
        try:
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
