import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from database import Database
from handlers.user import UserHandlers, EMAIL, PHONE, QUESTION
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

def main():
    # Initialize database
    db = Database()
    
    # Initialize handlers
    user_handlers = UserHandlers(db)
    admin_handlers = AdminHandlers(db)
    group_handlers = GroupHandlers()
    super_admin_handlers = SuperAdminHandlers(db)
    
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # User conversation handler for ticket creation
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('new', user_handlers.start),
            CallbackQueryHandler(user_handlers.new_ticket, pattern='^new_ticket$')
        ],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_phone)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_handlers.get_question)],
        },
        fallbacks=[CommandHandler('cancel', user_handlers.cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', user_handlers.start))
    application.add_handler(conv_handler)
    
    # Admin group commands
    application.add_handler(CommandHandler('pending', admin_handlers.pending))
    application.add_handler(CommandHandler('stats', admin_handlers.stats))
    application.add_handler(CommandHandler('search', admin_handlers.search))
    application.add_handler(CommandHandler('download', admin_handlers.download))
    
    # Group support command
    application.add_handler(CommandHandler('support', group_handlers.support))
    
    # Super admin commands
    application.add_handler(CommandHandler('add', super_admin_handlers.add_group))
    application.add_handler(CommandHandler('remove', super_admin_handlers.remove_group))
    application.add_handler(CommandHandler('listgroups', super_admin_handlers.list_groups))
    application.add_handler(CommandHandler('deletedata', super_admin_handlers.delete_data))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(admin_handlers.handle_reply_callback, pattern='^(reply_|progress_)'))
    
    # Message handler for admin replies
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        admin_handlers.handle_admin_reply
    ))
    
    # Start bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
