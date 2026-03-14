import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.models import Group
from src.database import db_session

logger = logging.getLogger(__name__)

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command in groups"""
    chat_id = update.effective_chat.id
    
    # Check if group is active
    group = db_session.query(Group).filter_by(group_id=chat_id, is_active=True).first()
    if not group:
        return  # Bot not activated in this group
    
    # Reply to the user who sent /support
    await update.message.reply_text(
        "🆘 **Need Help?**\n\n"
        "Click the button below to open a support ticket. "
        "Our team will assist you within 24 hours.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📝 Submit Ticket", url=f"https://t.me/{context.bot.username}?start=from_group")
        ]])
    )
