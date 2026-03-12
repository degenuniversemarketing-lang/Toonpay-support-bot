import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import List, Dict
import csv
import aiofiles

def generate_ticket_number():
    """Generate unique ticket number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"TKT-{timestamp}"

def format_user_info(user, tickets=None):
    """Format user information for display"""
    text = f"👤 **User Details**\n"
    text += f"Name: {user.name or 'Not provided'}\n"
    text += f"Username: @{user.username if user.username else 'N/A'}\n"
    text += f"User ID: `{user.user_id}`\n"
    text += f"Email: {user.email or 'Not provided'}\n"
    text += f"Phone: {user.phone or 'Not provided'}\n"
    text += f"Joined: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    
    if tickets:
        text += f"\n📊 **Ticket Statistics**\n"
        text += f"Total Tickets: {len(tickets)}\n"
        open_tickets = sum(1 for t in tickets if t.status.value == 'open')
        in_progress = sum(1 for t in tickets if t.status.value == 'in_progress')
        closed = sum(1 for t in tickets if t.status.value == 'closed')
        text += f"Open: {open_tickets} | In Progress: {in_progress} | Closed: {closed}\n"
    
    return text

def format_ticket_info(ticket, include_replies=True):
    """Format ticket information for display"""
    status_emoji = {
        'open': '🟢',
        'in_progress': '🟡',
        'closed': '🔴',
        'pending': '⏳'
    }
    
    text = f"🎫 **Ticket #{ticket.ticket_number}**\n"
    text += f"Status: {status_emoji.get(ticket.status.value, '⚪')} {ticket.status.value.upper()}\n"
    text += f"Category: {ticket.category}\n"
    text += f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    text += f"Question: {ticket.question}\n"
    
    if include_replies and ticket.replies:
        text += f"\n📝 **Replies:**\n"
        for reply in ticket.replies:
            text += f"Admin @{reply.admin_username}: {reply.message}\n"
            text += f"Time: {reply.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    return text

async def generate_csv_report(tickets_data: List[Dict]) -> BytesIO:
    """Generate CSV report from tickets data"""
    output = BytesIO()
    
    fieldnames = [
        'Ticket Number', 'User Name', 'Username', 'User ID', 
        'Email', 'Phone', 'Category', 'Question', 'Status',
        'Admin Answer', 'Admin Username', 'Created At', 'Closed At'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for data in tickets_data:
        writer.writerow(data)
    
    output.seek(0)
    return output

async def generate_excel_report(tickets_data: List[Dict]) -> BytesIO:
    """Generate Excel report from tickets data"""
    df = pd.DataFrame(tickets_data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Tickets', index=False)
    
    output.seek(0)
    return output
