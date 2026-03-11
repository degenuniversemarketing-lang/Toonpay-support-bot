# src/handlers/group.py
from telegram import Update
from telegram.ext import ContextTypes
import logging

from src.config import config
from src.keyboards import get_support_keyboard
from src.database import db

logger = logging.getLogger(__name__)

class GroupHandlers:
    
    @staticmethod
    async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command in groups"""
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        # Only work in groups
        if chat_type == 'private':
            return
        
        # Check if group is allowed
        if not db.is_group_allowed(chat_id):
            # If not allowed, just ignore (don't respond)
            return
        
        support_text = f"""
🎫 <b>Need help from {config.COMPANY_NAME} Support?</b>

Click the button below to open a private chat with our support bot and create a ticket.

{config.SUPPORT_MESSAGE}
"""
        
        await update.message.reply_text(
            support_text,
            reply_markup=get_support_keyboard(),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def delete_other_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete any other commands in groups"""
        chat_type = update.effective_chat.type
        
        # Only in groups
        if chat_type == 'private':
            return
        
        # If it's a command and not /support, delete it
        if update.message and update.message.text and update.message.text.startswith('/'):
            command = update.message.text.split()[0].lower()
            
            # Only allow /support command
            if command != '/support':
                try:
                    await update.message.delete()
                    logger.info(f"Deleted command {command} in group {update.effective_chat.id}")
                except:
                    pass
