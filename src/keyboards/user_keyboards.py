from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.config import Config

def get_start_keyboard():
    """Main menu keyboard for users"""
    keyboard = [
        [InlineKeyboardButton("🎫 New Ticket", callback_data="new_ticket")],
        [InlineKeyboardButton("📋 My Tickets", callback_data="my_tickets")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_category_keyboard():
    """Category selection keyboard"""
    keyboard = []
    for key, value in Config.CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f"cat_{key}")])
    return InlineKeyboardMarkup(keyboard)

def get_ticket_action_keyboard(ticket_number: str):
    """Keyboard for ticket actions"""
    keyboard = [
        [InlineKeyboardButton("📝 Add Reply", callback_data=f"reply_{ticket_number}")],
        [InlineKeyboardButton("🔙 Back to Tickets", callback_data="my_tickets")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_support_button():
    """Support button for group messages"""
    keyboard = [
        [InlineKeyboardButton("📩 Submit Ticket", url="https://t.me/your_bot_username?start=support")]
    ]
    return InlineKeyboardMarkup(keyboard)
