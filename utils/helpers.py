import pandas as pd
import io
from datetime import datetime, timedelta

def create_excel_sheet(tickets):
    """Create Excel file with two sheets"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Solved & Closed tickets
        solved_closed = [t for t in tickets if t['status'] in ['closed', 'solved']]
        if solved_closed:
            df1 = pd.DataFrame(solved_closed)
            df1.to_excel(writer, sheet_name='Solved_Closed', index=False)
        
        # Sheet 2: In Progress & Pending tickets
        in_progress = [t for t in tickets if t['status'] in ['pending', 'in_progress']]
        if in_progress:
            df2 = pd.DataFrame(in_progress)
            df2.to_excel(writer, sheet_name='In_Progress_Pending', index=False)
    
    output.seek(0)
    return output

def parse_time_string(time_str):
    """Parse time string like '1 day', '2 hours', '30 minutes'"""
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
