import pandas as pd
import io
import csv
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

def create_csv_file(tickets):
    """Create CSV file with all tickets - One sheet with all data"""
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
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    if tickets:
        for ticket in tickets:
            # Map ticket fields to CSV columns with proper formatting
            row = {
                'Name': ticket.get('name', ''),
                'Username': ticket.get('username', ''),
                'User ID': str(ticket.get('user_id', '')),
                'Ticket ID': str(ticket.get('ticket_id', '')),
                'Email': ticket.get('email', ''),
                'Phone': ticket.get('phone', ''),
                'User Question': ticket.get('user_question', '').replace('\n', ' ').replace('\r', ' '),
                'Admin Answer': ticket.get('admin_answer', 'No reply yet').replace('\n', ' ').replace('\r', ' '),
                'Ticket Status': ticket.get('ticket_status', ''),
                'Date & Time': str(ticket.get('date_time', '')),
                'Replied By Admin': ticket.get('replied_by_admin', '')
            }
            writer.writerow(row)
    else:
        # Write headers only if no tickets
        writer.writeheader()
    
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8-sig'))  # Use utf-8-sig for Excel compatibility

def create_csv_by_status(tickets, status_filter=None):
    """Create CSV file filtered by status"""
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
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    if tickets:
        for ticket in tickets:
            # Apply status filter if specified
            if status_filter and ticket.get('ticket_status') not in status_filter:
                continue
                
            row = {
                'Name': ticket.get('name', ''),
                'Username': ticket.get('username', ''),
                'User ID': str(ticket.get('user_id', '')),
                'Ticket ID': str(ticket.get('ticket_id', '')),
                'Email': ticket.get('email', ''),
                'Phone': ticket.get('phone', ''),
                'User Question': ticket.get('user_question', '').replace('\n', ' ').replace('\r', ' '),
                'Admin Answer': ticket.get('admin_answer', 'No reply yet').replace('\n', ' ').replace('\r', ' '),
                'Ticket Status': ticket.get('ticket_status', ''),
                'Date & Time': str(ticket.get('date_time', '')),
                'Replied By Admin': ticket.get('replied_by_admin', '')
            }
            writer.writerow(row)
    
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8-sig'))

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
