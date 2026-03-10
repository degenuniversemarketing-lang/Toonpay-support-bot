from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import Config

def get_categories_keyboard():
    """Keyboard for ticket categories"""
    builder = InlineKeyboardBuilder()
    for category in Config.CATEGORIES:
        builder.add(InlineKeyboardButton(
            text=category,
            callback_data=f"cat_{category}"
        ))
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()

def get_main_menu_keyboard():
    """Main menu keyboard for users"""
    buttons = [
        [InlineKeyboardButton(text="🎫 New Ticket", callback_data="new_ticket")],
        [InlineKeyboardButton(text="📋 My Tickets", callback_data="my_tickets")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_keyboard():
    """Cancel button for forms"""
    buttons = [[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
