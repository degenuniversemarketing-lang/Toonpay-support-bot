from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_ticket_action_keyboard(ticket_id: str):
    """Keyboard for admin actions on ticket"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Reply", callback_data=f"reply_{ticket_id}"),
            InlineKeyboardButton(text="🟡 In Progress", callback_data=f"progress_{ticket_id}")
        ],
        [
            InlineKeyboardButton(text="🔴 Close", callback_data=f"close_{ticket_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_main_keyboard():
    """Main keyboard for admin panel"""
    buttons = [
        [InlineKeyboardButton(text="📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📋 All Tickets", callback_data="admin_tickets")],
        [InlineKeyboardButton(text="🔍 Search User", callback_data="admin_search")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="admin_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
