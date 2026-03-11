import random
import string
import pandas as pd
from datetime import datetime
import io

def generate_ticket_id():
    """Generate unique ticket ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"TKT-{timestamp}-{random_chars}"

def format_ticket_for_admin(ticket: dict):
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

<b>⏱️ ToonPay Support Available 24/7</b>
"""
    return message

def format_detailed_export(users_data, tickets_data):
    """Format data for detailed export"""
    # Create DataFrames
    users_df = pd.DataFrame(users_data)
    tickets_df = pd.DataFrame(tickets_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        users_df.to_excel(writer, sheet_name='Users', index=False)
        tickets_df.to_excel(writer, sheet_name='Tickets', index=False)
        
        # Create summary sheet
        summary_data = {
            'Metric': ['Total Users', 'Total Tickets', 'Open', 'In Progress', 'Replied & Closed', 'Closed No Reply'],
            'Value': [
                len(users_df),
                len(tickets_df),
                len(tickets_df[tickets_df['Status'] == 'open']),
                len(tickets_df[tickets_df['Status'] == 'in_progress']),
                len(tickets_df[(tickets_df['Status'] == 'closed') & (tickets_df['Admin Answer'].notna())]),
                len(tickets_df[(tickets_df['Status'] == 'closed') & (tickets_df['Admin Answer'].isna())])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    return output

def generate_ticket_link(chat_id, message_id):
    """Generate Telegram message link for ticket"""
    if message_id and chat_id:
        # Remove -100 from group ID for link
        clean_chat_id = str(chat_id).replace('-100', '')
        return f"https://t.me/c/{clean_chat_id}/{message_id}"
    return None
