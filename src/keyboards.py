# src/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.config import config

def get_main_keyboard():
    """Main menu keyboard for users"""
    keyboard = [
        [InlineKeyboardButton("🎫 New Ticket", callback_data='new_ticket')],
        [InlineKeyboardButton("📋 My Tickets", callback_data='my_tickets')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard():
    """Category selection keyboard"""
    keyboard = []
    row = []
    
    for i, (cat_id, cat_info) in enumerate(config.CATEGORIES.items(), 1):
        button = InlineKeyboardButton(
            f"{cat_info['emoji']} {cat_info['name']}", 
            callback_data=f'cat_{cat_id}'
        )
        row.append(button)
        
        if i % 2 == 0:  # 2 buttons per row
            keyboard.append(row)
            row = []
    
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard():
    """Confirmation keyboard for ticket creation"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data='confirm_yes'),
            InlineKeyboardButton("❌ Cancel", callback_data='confirm_no')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_tickets_keyboard(tickets):
    """Keyboard for user's tickets list"""
    keyboard = []
    
    for ticket in tickets[:5]:  # Show only last 5
        status_emoji = config.STATUS_EMOJIS.get(ticket.status, '⚪')
        category_info = config.CATEGORIES.get(ticket.category, {'emoji': '📌'})
        
        button_text = f"{status_emoji} {ticket.ticket_id[:8]}... {category_info['emoji']}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f'view_ticket_{ticket.ticket_id}')
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

def get_ticket_action_keyboard(ticket_id: str, status: str):
    """Admin ticket action keyboard"""
    keyboard = []
    
    if status == 'open':
        keyboard.append([
            InlineKeyboardButton("🟡 Mark In Progress", callback_data=f'inprogress_{ticket_id}'),
            InlineKeyboardButton("🔴 Close No Reply", callback_data=f'close_{ticket_id}')
        ])
        keyboard.append([
            InlineKeyboardButton("✅ Reply", callback_data=f'reply_{ticket_id}')
        ])
    elif status == 'in_progress':
        keyboard.append([
            InlineKeyboardButton("✅ Reply & Close", callback_data=f'reply_{ticket_id}'),
            InlineKeyboardButton("🔴 Close No Reply", callback_data=f'close_{ticket_id}')
        ])
    
    keyboard.append([
        InlineKeyboardButton("👤 View User", callback_data=f'viewuser_{ticket_id}')
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_filter_keyboard():
    """Filter keyboard for admin panel"""
    keyboard = [
        [
            InlineKeyboardButton("🟢 Open", callback_data='filter_open'),
            InlineKeyboardButton("🟡 In Progress", callback_data='filter_in_progress')
        ],
        [
            InlineKeyboardButton("✅ Replied", callback_data='filter_replied_closed'),
            InlineKeyboardButton("🔴 Closed", callback_data='filter_closed_no_reply')
        ],
        [
            InlineKeyboardButton("📋 All Tickets", callback_data='filter_all')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_super_admin_keyboard():
    """Super admin main keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data='sa_stats')],
        [InlineKeyboardButton("📋 All Tickets", callback_data='sa_all_tickets')],
        [InlineKeyboardButton("👥 Manage Admins", callback_data='sa_manage_admins')],
        [InlineKeyboardButton("👥 Manage Groups", callback_data='sa_manage_groups')],
        [InlineKeyboardButton("📤 Export Data", callback_data='sa_export')],
        [InlineKeyboardButton("📢 Broadcast", callback_data='sa_broadcast')],
        [InlineKeyboardButton("💾 Backup", callback_data='sa_backup')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='sa_settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_export_keyboard():
    """Export options keyboard"""
    keyboard = [
        [InlineKeyboardButton("👥 Export Users", callback_data='export_users')],
        [InlineKeyboardButton("🎫 Export Tickets", callback_data='export_tickets')],
        [InlineKeyboardButton("📊 Complete Export", callback_data='export_complete')],
        [InlineKeyboardButton("🔙 Back", callback_data='sa_back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_management_keyboard():
    """Admin management keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Admin", callback_data='add_admin')],
        [InlineKeyboardButton("➖ Remove Admin", callback_data='remove_admin')],
        [InlineKeyboardButton("📋 List Admins", callback_data='list_admins')],
        [InlineKeyboardButton("🔙 Back", callback_data='sa_back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_group_management_keyboard():
    """Group management keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Group", callback_data='add_group')],
        [InlineKeyboardButton("➖ Remove Group", callback_data='remove_group')],
        [InlineKeyboardButton("📋 List Groups", callback_data='list_groups')],
        [InlineKeyboardButton("🔙 Back", callback_data='sa_back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard():
    """Support button for groups"""
    keyboard = [
        [InlineKeyboardButton("📩 Submit Ticket", url=f"https://t.me/{config.BOT_USERNAME[1:]}?start=group")]
    ]
    return InlineKeyboardMarkup(keyboard)
