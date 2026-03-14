#!/usr/bin/env python3
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import ConversationHandler
from src.config import Config
from src.database import init_db, db_session
from src.handlers.user import *
from src.handlers.admin import *
from src.handlers.super_admin import *
from src.handlers.group import *
from src.middlewares.auth import AuthMiddleware

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Initialize database
    init_db()
    
    # Create application
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    
    # Add middleware
    application.add_handler(AuthMiddleware())
    
    # User handlers (private chat only)
    application.add_handler(CommandHandler("start", start_command, filters=filters.ChatType.PRIVATE))
    
    # Group handlers
    application.add_handler(CommandHandler("support", support_command, filters=filters.ChatType.GROUP | filters.ChatType.SUPERGROUP))
    
    # Admin group handlers
    application.add_handler(CommandHandler("pending", pending_tickets, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
    application.add_handler(CommandHandler("getdata", get_all_data, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
    application.add_handler(CommandHandler("search", search_data, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
    application.add_handler(CommandHandler("reply", reply_to_ticket, filters=filters.Chat(Config.ADMIN_GROUP_ID)))
    
    # Super admin handlers (private chat)
    application.add_handler(CommandHandler("add", add_group, filters=filters.User(Config.SUPER_ADMIN_IDS) & filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("remove", remove_group, filters=filters.User(Config.SUPER_ADMIN_IDS) & filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stats", get_statistics, filters=filters.User(Config.SUPER_ADMIN_IDS) & filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("settings", bot_settings, filters=filters.User(Config.SUPER_ADMIN_IDS) & filters.ChatType.PRIVATE))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(handle_category_selection, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(handle_ticket_submit, pattern="^submit_ticket$"))
    application.add_handler(CallbackQueryHandler(handle_support_button, pattern="^support$"))
    application.add_handler(CallbackQueryHandler(handle_admin_reply_button, pattern="^reply_"))
    application.add_handler(CallbackQueryHandler(handle_admin_in_progress_button, pattern="^progress_"))
    application.add_handler(CallbackQueryHandler(handle_admin_view_button, pattern="^view_"))
    application.add_handler(CallbackQueryHandler(handle_admin_cancel_button, pattern="^cancel_"))
    application.add_handler(CallbackQueryHandler(handle_pending_reply_button, pattern="^pending_reply_"))
    
    # Conversation handlers for ticket creation
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_ticket_creation, pattern="^new_ticket$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_id)],
            ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        filters=filters.ChatType.PRIVATE
    )
    application.add_handler(conv_handler)
    
    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()
