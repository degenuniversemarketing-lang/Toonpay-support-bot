import random
import string
from datetime import datetime
from src.models import Ticket, User
from src.database import db_session
import pandas as pd
import io

def generate_ticket_number():
    """Generate unique ticket number"""
    while True:
        # Format: TKT-YYYYMMDDHHMMSS + 2 random digits
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_digits = ''.join(random.choices(string.digits, k=2))
        ticket_number = f"TKT-{timestamp}{random_digits}"
        
        # Check if exists
        existing = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if not existing:
            return ticket_number

def log_admin_action(admin_id, admin_username, action, ticket_number=None, details=None):
    """Log admin actions to database"""
    from src.models import AdminAction
    action_log = AdminAction(
        admin_id=admin_id,
        admin_username=admin_username,
        action=action,
        ticket_number=ticket_number,
        details=details
    )
    db_session.add(action_log)
    db_session.commit()

def format_ticket_details(ticket, user):
    """Format ticket details for display"""
    status_emoji = {
        'new': '🆕',
        'in_progress': '⏳',
        'closed': '✅'
    }
    
    status_text = f"{status_emoji.get(ticket.status, '📌')} {ticket.status.upper()}"
    
    ticket_text = (
        f"**Ticket:** `{ticket.ticket_number}`\n"
        f"**Status:** {status_text}\n"
        f"**User:** {ticket.name}\n"
        f"**Username:** @{user.username if user and user.username else 'N/A'}\n"
        f"**User ID:** `{ticket.user_id}`\n"
        f"**Category:** {ticket.category}\n"
        f"**Email:** {ticket.email}\n"
        f"**Phone:** {ticket.phone}\n\n"
        f"**Question:**\n{ticket.question}\n"
    )
    
    if ticket.admin_reply:
        ticket_text += f"\n**Admin Reply:**\n{ticket.admin_reply}\n"
        ticket_text += f"**Replied by:** @{ticket.admin_username or 'N/A'}\n"
        ticket_text += f"**Replied at:** {ticket.replied_at.strftime('%Y-%m-%d %H:%M') if ticket.replied_at else 'N/A'}\n"
    
    ticket_text += f"\n**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    return ticket_text

def export_data_to_excel(tickets):
    """Export tickets to Excel format"""
    data = []
    for ticket in tickets:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        data.append({
            'Ticket Number': ticket.ticket_number,
            'User Name': ticket.name,
            'Username': f"@{user.username if user and user.username else 'N/A'}",
            'User ID': ticket.user_id,
            'Phone': ticket.phone,
            'Email': ticket.email,
            'Category': ticket.category,
            'Question': ticket.question,
            'Status': ticket.status,
            'Admin Reply': ticket.admin_reply or '',
            'Replied By': ticket.admin_username or '',
            'Reply Time': ticket.replied_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.replied_at else '',
            'Created At': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tickets')
    
    output.seek(0)
    return output
