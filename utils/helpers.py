import pandas as pd
import io
import csv
from datetime import datetime, timedelta
import re

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

def create_csv_file(tickets):
    """Create CSV file with all tickets - Properly encoded for all apps"""
    output = io.StringIO()
    
    # Define CSV headers exactly as requested
    headers = [
        'Name', 
        'Username', 
        'User ID', 
        'Ticket ID', 
        'Email', 
        'Phone', 
        'User Question', 
        'Admin Answer', 
        'Ticket Status', 
        'Date & Time', 
        'Replied By Admin'
    ]
    
    # Use Excel-compatible dialect
    writer = csv.writer(output, dialect='excel', quoting=csv.QUOTE_ALL)
    writer.writerow(headers)
    
    if tickets:
        for ticket in tickets:
            # Clean and format each field to ensure proper display
            row = [
                str(ticket.get('name', '')).strip(),
                str(ticket.get('username', '')).strip(),
                str(ticket.get('user_id', '')).strip(),
                str(ticket.get('ticket_id', '')).strip(),
                str(ticket.get('email', '')).strip(),
                str(ticket.get('phone', '')).strip(),
                # Clean question text - remove any special characters and normalize
                str(ticket.get('user_question', '')).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip(),
                # Clean answer text
                str(ticket.get('admin_answer', 'No reply yet')).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip(),
                str(ticket.get('ticket_status', '')).strip(),
                str(ticket.get('date_time', '')).strip(),
                str(ticket.get('replied_by_admin', '')).strip()
            ]
            writer.writerow(row)
    else:
        # Write empty row with headers only
        writer.writerow([''] * len(headers))
    
    output.seek(0)
    # Use UTF-8 with BOM for Excel compatibility, but ensure proper text display
    return io.BytesIO(output.getvalue().encode('utf-8-sig'))

def create_csv_by_status(tickets, status_filter=None):
    """Create CSV file filtered by status - Properly encoded for all apps"""
    output = io.StringIO()
    
    headers = [
        'Name', 
        'Username', 
        'User ID', 
        'Ticket ID', 
        'Email', 
        'Phone', 
        'User Question', 
        'Admin Answer', 
        'Ticket Status', 
        'Date & Time', 
        'Replied By Admin'
    ]
    
    writer = csv.writer(output, dialect='excel', quoting=csv.QUOTE_ALL)
    writer.writerow(headers)
    
    if tickets:
        for ticket in tickets:
            # Apply status filter if specified
            if status_filter and ticket.get('ticket_status') not in status_filter:
                continue
                
            # Clean and format each field
            row = [
                str(ticket.get('name', '')).strip(),
                str(ticket.get('username', '')).strip(),
                str(ticket.get('user_id', '')).strip(),
                str(ticket.get('ticket_id', '')).strip(),
                str(ticket.get('email', '')).strip(),
                str(ticket.get('phone', '')).strip(),
                str(ticket.get('user_question', '')).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip(),
                str(ticket.get('admin_answer', 'No reply yet')).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip(),
                str(ticket.get('ticket_status', '')).strip(),
                str(ticket.get('date_time', '')).strip(),
                str(ticket.get('replied_by_admin', '')).strip()
            ]
            writer.writerow(row)
    
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8-sig'))

def parse_time_string(time_str):
    """Parse time string like '1d', '2h', '30m', '7 days', '2 hours', '30 minutes'"""
    try:
        time_str = time_str.lower().strip()
        
        # Extract number and unit using regex
        match = re.match(r'(\d+)\s*([a-z]+)', time_str)
        if not match:
            return timedelta(days=30)  # Default to 30 days
        
        value = int(match.group(1))
        unit = match.group(2)
        
        # Handle different unit formats
        if unit.startswith('d'):  # days, day, d
            return timedelta(days=value)
        elif unit.startswith('h'):  # hours, hour, h
            return timedelta(hours=value)
        elif unit.startswith('m'):  # minutes, minute, m
            return timedelta(minutes=value)
        else:
            return timedelta(days=value)
    except:
        return timedelta(days=30)  # Default to 30 days
