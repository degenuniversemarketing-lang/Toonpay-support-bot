from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_ticket_keyboard(ticket_number):
    """Keyboard for admin group when new ticket arrives"""
    keyboard = [
        [
            InlineKeyboardButton("📝 Reply", callback_data=f"reply_{ticket_number}"),
            InlineKeyboardButton("⏳ In Progress", callback_data=f"progress_{ticket_number}")
        ],
        [
            InlineKeyboardButton("👁 View", callback_data=f"view_{ticket_number}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{ticket_number}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pending_ticket_keyboard(ticket_number):
    """Keyboard for pending tickets"""
    keyboard = [
        [InlineKeyboardButton("📝 Reply to this ticket", callback_data=f"pending_reply_{ticket_number}")]
    ]
    return InlineKeyboardMarkup(keyboard)
