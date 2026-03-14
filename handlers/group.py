from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config

class GroupHandlers:
    async def support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command in groups"""
        if update.effective_chat.type == 'private':
            return
        
        keyboard = [[InlineKeyboardButton("📝 Submit Ticket", url=f"https://t.me/{context.bot.username}?start=private")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            Config.SUPPORT_MESSAGE,
            reply_markup=reply_markup
        )
