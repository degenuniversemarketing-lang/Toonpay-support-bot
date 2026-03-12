from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from src.utils.decorators import group_command_only
from src.keyboards.user_keyboards import get_support_button

@group_command_only
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command in groups"""
    await update.message.reply_text(
        "📬 **Need help from ToonPay Support?**\n\n"
        "Click the button below to submit your ticket privately.\n"
        "Our support team will assist you within 24 hours.",
        reply_markup=get_support_button(),
        parse_mode='Markdown'
    )

# Handler for group messages (if needed)
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages in groups (if needed)"""
    pass
