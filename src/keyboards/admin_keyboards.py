from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_ticket_admin_keyboard(ticket_number: str, user_id: int):
    """Admin keyboard for ticket management"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Reply", callback_data=f"admin_reply_{ticket_number}"),
            InlineKeyboardButton("⏳ In Progress", callback_data=f"progress_{ticket_number}")
        ],
        [
            InlineKeyboardButton("🔍 View User", callback_data=f"view_user_{user_id}"),
            InlineKeyboardButton("❌ Close", callback_data=f"close_{ticket_number}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(page: int, total_pages: int, data_type: str, search_term: str = None):
    """Pagination keyboard for browsing tickets"""
    keyboard = []
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"{data_type}_page_{page-1}_{search_term or ''}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"{data_type}_page_{page+1}_{search_term or ''}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_main_keyboard():
    """Main admin menu"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("⏳ Pending Tickets", callback_data="admin_pending")],
        [InlineKeyboardButton("🔍 Search", callback_data="admin_search")],
        [InlineKeyboardButton("📥 Download Data", callback_data="admin_download")]
    ]
    return InlineKeyboardMarkup(keyboard)
