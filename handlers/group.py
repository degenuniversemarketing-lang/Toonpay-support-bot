from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
import logging

logger = logging.getLogger(__name__)

class GroupHandlers:
    def __init__(self):
        self.activated_groups = set()  # Will be loaded from database
    
    async def support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command in groups - only works in activated groups"""
        if update.effective_chat.type == 'private':
            return
        
        chat_id = update.effective_chat.id
        
        # Check if group is activated (from database)
        db = context.bot_data.get('db')
        if db:
            activated = db.is_group_activated(chat_id)
        else:
            # Fallback to config if db not available
            activated = chat_id == Config.ADMIN_GROUP_ID  # For backward compatibility
        
        if not activated:
            logger.warning(f"Unauthorized /support attempt in group {chat_id}")
            return
        
        keyboard = [[InlineKeyboardButton("📝 Submit Ticket", url=f"https://t.me/{context.bot.username}?start=private")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            Config.SUPPORT_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
