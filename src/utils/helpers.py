import random
import string
import pandas as pd
from datetime import datetime
import io
from aiogram.types import FSInputFile
import aiofiles

def generate_ticket_id():
    """Generate unique ticket ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TKT-{timestamp}-{random_chars}"

def format_ticket_for_admin(ticket: dict, user_info: dict = None):
    """Format ticket message for admin group"""
    status_emoji = {
        'open': '🟢',
        'in_progress': '🟡',
        'closed': '🔴'
    }
    
    message = f"""
<b>🎫 New Ticket: {ticket['ticket_id']}</b>
{status_emoji.get(ticket['status'], '🟢')} Status: {ticket['status'].title()}

<b>👤 User Details:</b>
• Name: {ticket['name']}
• Email: {ticket['email']}
• Phone: {ticket['phone']}
• User ID: <code>{ticket['user_id']}</code>

<b>📋 Ticket Details:</b>
• Category: {ticket['category']}
• Created: {ticket['created_at'].strftime('%Y-%m-%d %H:%M:%S')}

<b>📝 Issue Description:</b>
{ticket['description']}
"""
    return message

def format_user_data_for_export(users_data, tickets_data):
    """Format data for export"""
    # Create DataFrames
    users_df = pd.DataFrame(users_data)
    tickets_df = pd.DataFrame(tickets_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        users_df.to_excel(writer, sheet_name='Users', index=False)
        tickets_df.to_excel(writer, sheet_name='Tickets', index=False)
    
    output.seek(0)
    return output
