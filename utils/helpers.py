import pandas as pd
import io
from datetime import datetime, timedelta

def create_excel_sheet(tickets):
    """Create Excel file with two sheets"""
    output = io.BytesIO()
    
    if not tickets:
        # Create empty DataFrame if no tickets
        df_empty = pd.DataFrame(columns=['Name', 'Username', 'User ID', 'Ticket ID', 'Email', 
                                        'Phone', 'User Question', 'Admin Answer', 'Ticket Status', 
                                        'Date & Time', 'Replied By Admin'])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_empty.to_excel(writer, sheet_name='No Tickets', index=False)
    else:
        # Convert tickets to DataFrame
        df = pd.DataFrame(tickets)
        
        # Rename columns to match requested format
        column_mapping = {
            'name': 'Name',
            'username': 'Username',
            'user_id': 'User ID',
            'ticket_id': 'Ticket ID',
            'email': 'Email',
            'phone': 'Phone',
            'user_question': 'User Question',
            'admin_answer': 'Admin Answer',
            'ticket_status': 'Ticket Status',
            'date_time': 'Date & Time',
            'replied_by_admin': 'Replied By Admin'
        }
        df = df.rename(columns=column_mapping)
        
        # Split into two sheets based on status
        solved_statuses = ['closed', 'solved']
        in_progress_statuses = ['pending', 'in_progress', 'spam']
        
        # Filter tickets
        solved_closed_df = df[df['Ticket Status'].isin(solved_statuses)]
        in_progress_df = df[df['Ticket Status'].isin(in_progress_statuses)]
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not solved_closed_df.empty:
                solved_closed_df.to_excel(writer, sheet_name='Solved_Closed', index=False)
            else:
                # Create empty sheet with headers
                pd.DataFrame(columns=df.columns).to_excel(writer, sheet_name='Solved_Closed', index=False)
            
            if not in_progress_df.empty:
                in_progress_df.to_excel(writer, sheet_name='In_Progress_Pending', index=False)
            else:
                # Create empty sheet with headers
                pd.DataFrame(columns=df.columns).to_excel(writer, sheet_name='In_Progress_Pending', index=False)
    
    output.seek(0)
    return output

def parse_time_string(time_str):
    """Parse time string like '1 day', '2 hours', '30 minutes'"""
    try:
        value = int(time_str.split()[0])
        unit = time_str.split()[1].lower()
        
        if 'day' in unit:
            return timedelta(days=value)
        elif 'hour' in unit:
            return timedelta(hours=value)
        elif 'minute' in unit:
            return timedelta(minutes=value)
        else:
            return timedelta(days=value)
    except:
        return timedelta(days=30)  # Default to 30 days
