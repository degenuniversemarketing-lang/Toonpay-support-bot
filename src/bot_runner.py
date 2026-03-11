# src/bot_runner.py
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

from src.config import config
from src.database import db
from src.backup import start_backup_scheduler

from src.handlers.user import UserHandlers, NAME, EMAIL, PHONE, QUESTION, CONFIRM
from src.handlers.admin import AdminHandlers, REPLY_TEXT, SEARCH_QUERY
from src.handlers.super_admin import (
    SuperAdminHandlers, ADD_ADMIN_ID, REMOVE_ADMIN_ID,
    ADD_GROUP_ID, REMOVE_GROUP_ID, BROADCAST_TEXT
)
from src.handlers.group import GroupHandlers

logger = logging.getLogger(__name__)

class ToonPayBot:
    def __init__(self):
        self.application = None
        logger.info("Initializing ToonPayBot...")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        logger.info("Setting up handlers...")
        
        # ========== USER CONVERSATION ==========
        user_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(UserHandlers.handle_callback, pattern='^new_ticket$')
            ],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserHandlers.get_name)],
                EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserHandlers.get_email)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserHandlers.get_phone)],
                QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, UserHandlers.get_question)],
                CONFIRM: [CallbackQueryHandler(UserHandlers.confirm_ticket, pattern='^confirm_')],
            },
            fallbacks=[
                CallbackQueryHandler(UserHandlers.handle_callback, pattern='^cancel$'),
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="user_conversation"
        )
        
        # ========== ADMIN REPLY CONVERSATION ==========
        admin_reply_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(AdminHandlers.handle_callback, pattern='^reply_')
            ],
            states={
                REPLY_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, AdminHandlers.handle_reply)],
            },
            fallbacks=[
                CommandHandler('cancel', AdminHandlers.cancel_reply)
            ],
            name="admin_reply_conversation"
        )
        
        # ========== ADMIN SEARCH CONVERSATION ==========
        admin_search_conv = ConversationHandler(
            entry_points=[
                CommandHandler('search', AdminHandlers.search)
            ],
            states={
                SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, AdminHandlers.handle_search)],
            },
            fallbacks=[
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="admin_search_conversation"
        )
        
        # ========== SUPER ADMIN CONVERSATIONS ==========
        add_admin_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(SuperAdminHandlers.handle_callback, pattern='^add_admin$')
            ],
            states={
                ADD_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, SuperAdminHandlers.handle_add_admin)],
            },
            fallbacks=[
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="add_admin_conversation"
        )
        
        remove_admin_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(SuperAdminHandlers.handle_callback, pattern='^remove_admin$')
            ],
            states={
                REMOVE_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, SuperAdminHandlers.handle_remove_admin)],
            },
            fallbacks=[
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="remove_admin_conversation"
        )
        
        add_group_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(SuperAdminHandlers.handle_callback, pattern='^add_group$')
            ],
            states={
                ADD_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, SuperAdminHandlers.handle_add_group)],
            },
            fallbacks=[
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="add_group_conversation"
        )
        
        remove_group_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(SuperAdminHandlers.handle_callback, pattern='^remove_group$')
            ],
            states={
                REMOVE_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, SuperAdminHandlers.handle_remove_group)],
            },
            fallbacks=[
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="remove_group_conversation"
        )
        
        broadcast_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(SuperAdminHandlers.handle_callback, pattern='^sa_broadcast$')
            ],
            states={
                BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, SuperAdminHandlers.handle_broadcast)],
            },
            fallbacks=[
                CommandHandler('cancel', lambda u,c: ConversationHandler.END)
            ],
            name="broadcast_conversation"
        )
        
        # ========== COMMAND HANDLERS ==========
        
        # User commands (private only)
        self.application.add_handler(
            CommandHandler("start", UserHandlers.start, filters=filters.ChatType.PRIVATE)
        )
        
        # Admin group commands
        self.application.add_handler(
            CommandHandler("tickets", AdminHandlers.tickets, filters=filters.Chat(config.ADMIN_GROUP_ID))
        )
        self.application.add_handler(
            CommandHandler("data", AdminHandlers.data, filters=filters.Chat(config.ADMIN_GROUP_ID))
        )
        self.application.add_handler(
            CommandHandler("getdata", AdminHandlers.getdata, filters=filters.Chat(config.ADMIN_GROUP_ID))
        )
        self.application.add_handler(
            CommandHandler("reply", AdminHandlers.reply_command, filters=filters.Chat(config.ADMIN_GROUP_ID))
        )
        
        # Super admin commands (private only)
        self.application.add_handler(
            CommandHandler("panel", SuperAdminHandlers.panel, filters=filters.ChatType.PRIVATE)
        )
        
        # Group commands (works in allowed groups)
        self.application.add_handler(
            CommandHandler("support", GroupHandlers.support)
        )
        
        # ========== CALLBACK HANDLERS ==========
        
        # User callbacks
        self.application.add_handler(
            CallbackQueryHandler(UserHandlers.handle_callback, pattern='^(new_ticket|my_tickets|help|main_menu|cat_|view_ticket_|cancel)$')
        )
        
        # Admin callbacks
        self.application.add_handler(
            CallbackQueryHandler(AdminHandlers.handle_callback, pattern='^(inprogress_|close_|reply_|viewuser_|filter_|back_to_ticket_)')
        )
        
        # Super admin callbacks
        self.application.add_handler(
            CallbackQueryHandler(SuperAdminHandlers.handle_callback, pattern='^sa_')
        )
        
        # ========== CONVERSATION HANDLERS ==========
        self.application.add_handler(user_conv_handler)
        self.application.add_handler(admin_reply_conv)
        self.application.add_handler(admin_search_conv)
        self.application.add_handler(add_admin_conv)
        self.application.add_handler(remove_admin_conv)
        self.application.add_handler(add_group_conv)
        self.application.add_handler(remove_group_conv)
        self.application.add_handler(broadcast_conv)
        
        # ========== GROUP MESSAGE HANDLER ==========
        # Delete any other commands in groups
        self.application.add_handler(
            MessageHandler(
                filters.COMMAND & filters.ChatType.GROUP,
                GroupHandlers.delete_other_commands
            )
        )
        
        logger.info("✅ All handlers setup complete")
    
    def run(self):
        """Run the bot"""
        try:
            # Create application
            logger.info(f"Creating application with token: {config.BOT_TOKEN[:10]}...")
            self.application = Application.builder().token(config.BOT_TOKEN).build()
            
            # Setup handlers
            self.setup_handlers()
            
            # Start backup scheduler
            if config.ENABLE_AUTO_BACKUP:
                start_backup_scheduler()
                logger.info("✅ Backup scheduler started")
            
            # Start bot
            logger.info(f"🤖 Bot {config.BOT_USERNAME} is starting...")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
