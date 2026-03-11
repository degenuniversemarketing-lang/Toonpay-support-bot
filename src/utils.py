# src/utils.py
from datetime import datetime
import html
import re
from typing import Dict, Any, List
import pandas as pd
import io
from src.config import config

def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ""
    return html.escape(str(text))

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M")

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    # Remove common phone number characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and len(cleaned) >= 8

def format_user_info(user) -> str:
    """Format user information for display"""
    text = f"""
👤 <b>User Found:</b>
• ID: <code>{user.user_id}</code>
• Username: @{user.username if user.username else 'N/A'}
• Name: {escape_html(user.full_name)}
• Email: {escape_html(user.email)}
• Phone: {escape_html(user.phone)}
• Registered: {format_datetime(user.registered_at)}
• Total Tickets: {user.total_tickets}
"""
    return text

def format_ticket_info(ticket, include_admin: bool = False) -> str:
    """Format ticket information"""
    status_emoji = config.STATUS_EMOJIS.get(ticket.status, '⚪')
    category_info = config.CATEGORIES.get(ticket.category, {'name': ticket.category, 'emoji': '📌'})
    
    text = f"""
{status_emoji} <b>Ticket #{ticket.ticket_id}</b>
📂 Category: {category_info['emoji']} {category_info['name']}
📅 Created: {format_datetime(ticket.created_at)}
📝 <b>Question:</b>
{escape_html(ticket.question)}
"""
    
    if ticket.admin_reply:
        text += f"""
💬 <b>Admin Reply:</b>
{escape_html(ticket.admin_reply)}
"""
    
    if include_admin and ticket.assigned_to:
        text += f"\n👨‍💼 Assigned to: <code>{ticket.assigned_to}</code>"
    
    if ticket.closed_at:
        text += f"\n🔒 Closed: {format_datetime(ticket.closed_at)}"
    
    return text

def format_ticket_list(tickets: List, title: str = "📋 Tickets") -> str:
    """Format list of tickets"""
    if not tickets:
        return "📭 No tickets found."
    
    text = f"<b>{title}</b>\n\n"
    
    for ticket in tickets[:10]:  # Show last 10
        status_emoji = config.STATUS_EMOJIS.get(ticket.status, '⚪')
        category_info = config.CATEGORIES.get(ticket.category, {'emoji': '📌'})
        
        text += f"{status_emoji} <b>{ticket.ticket_id}</b> {category_info['emoji']}\n"
        text += f"   From: {escape_html(ticket.user.full_name if ticket.user else 'Unknown')}"
        if ticket.user and ticket.user.username:
            text += f" (@{ticket.user.username})"
        text += f"\n"
        text += f"   Created: {format_datetime(ticket.created_at)}\n"
        
        if ticket.status == 'in_progress' and ticket.assigned_to:
            text += f"   🟡 Marked by: <code>{ticket.assigned_to}</code>\n"
        elif ticket.status == 'replied_closed' and ticket.closed_by:
            text += f"   ✅ Replied by: <code>{ticket.closed_by}</code>\n"
        elif ticket.status == 'closed_no_reply' and ticket.closed_by:
            text += f"   🔴 Closed by: <code>{ticket.closed_by}</code>\n"
        
        text += "\n"
    
    return text

def format_statistics(stats: Dict[str, Any]) -> str:
    """Format statistics for display"""
    text = f"""
📊 <b>System Statistics</b>

👥 <b>Users:</b> {stats['total_users']}
🎫 <b>Tickets:</b> {stats['total_tickets']}

📈 <b>Ticket Status:</b>
🟢 Open: {stats['open']}
🟡 In Progress: {stats['in_progress']}
✅ Replied & Closed: {stats['replied_closed']}
🔴 Closed No Reply: {stats['closed_no_reply']}

📅 <b>Today's Tickets:</b> {stats['today_tickets']}

👨‍💼 <b>Admins:</b> {stats['total_admins']}
👥 <b>Active Groups:</b> {stats['total_groups']}

📊 <b>Category Breakdown:</b>
"""
    
    for cat_id, count in stats['categories'].items():
        cat_info = config.CATEGORIES.get(cat_id, {'emoji': '📌'})
        text += f"{cat_info['emoji']} {cat_id.title()}: {count}\n"
    
    return text

def format_user_statistics(user_id: int, stats: Dict[str, int]) -> str:
    """Format user statistics"""
    text = f"""
📊 <b>User Statistics</b>
👤 User ID: <code>{user_id}</code>

📋 <b>Ticket Breakdown:</b>
• Total Tickets: {stats['total']}
• 🟢 Open: {stats['open']}
• 🟡 In Progress: {stats['in_progress']}
• ✅ Replied & Closed: {stats['replied_closed']}
• 🔴 Closed No Reply: {stats['closed_no_reply']}
"""
    return text

def create_excel_export(users: List, tickets: List) -> bytes:
    """Create Excel file with all data"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Users sheet
        users_data = []
        for user in users:
            users_data.append({
                'User ID': user.user_id,
                'Username': user.username,
                'Full Name': user.full_name,
                'Email': user.email,
                'Phone': user.phone,
                'Registered': user.registered_at,
                'Last Active': user.last_active,
                'Total Tickets': user.total_tickets
            })
        
        if users_data:
            df_users = pd.DataFrame(users_data)
            df_users.to_excel(writer, sheet_name='Users', index=False)
        
        # Tickets sheet
        tickets_data = []
        for ticket in tickets:
            user = ticket.user
            tickets_data.append({
                'Ticket ID': ticket.ticket_id,
                'User ID': ticket.user_id,
                'Username': user.username if user else 'N/A',
                'User Name': user.full_name if user else 'N/A',
                'Category': ticket.category,
                'Question': ticket.question,
                'Admin Reply': ticket.admin_reply,
                'Status': ticket.status,
                'Created': ticket.created_at,
                'Closed': ticket.closed_at,
                'Assigned To': ticket.assigned_to,
                'Closed By': ticket.closed_by
            })
        
        if tickets_data:
            df_tickets = pd.DataFrame(tickets_data)
            df_tickets.to_excel(writer, sheet_name='Tickets', index=False)
        
        # Summary sheet
        summary_data = {
            'Total Users': [len(users)],
            'Total Tickets': [len(tickets)],
            'Open Tickets': [sum(1 for t in tickets if t.status == 'open')],
            'In Progress': [sum(1 for t in tickets if t.status == 'in_progress')],
            'Replied & Closed': [sum(1 for t in tickets if t.status == 'replied_closed')],
            'Closed No Reply': [sum(1 for t in tickets if t.status == 'closed_no_reply')]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output.getvalue()
