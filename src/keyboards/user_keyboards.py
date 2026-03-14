from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.config import Config

def get_main_menu_keyboard():
    """Main menu keyboard for users"""
    keyboard = []
    
    # Create category buttons
    for category in Config.CATEGORIES:
        keyboard.append([InlineKeyboardButton(f"📌 {category}", callback_data=f"cat_{category.lower()}")])
    
    # Add support button
    keyboard.append([InlineKeyboardButton("ℹ️ About Toonpay", url="https://toon.cash")])
    
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard():
    """Categories selection keyboard"""
    keyboard = []
    for category in Config.CATEGORIES:
        keyboard.append([InlineKeyboardButton(f"📌 {category}", callback_data=f"cat_{category.lower()}")])
    
    return InlineKeyboardMarkup(keyboard)

def get_ticket_submit_keyboard():
    """Ticket submission confirmation keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Submit Ticket", callback_data="submit_ticket")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)
