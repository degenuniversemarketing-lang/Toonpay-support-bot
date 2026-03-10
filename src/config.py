import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID', '0'))
    ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', '0'))
    
    # Categories for tickets
    CATEGORIES = [
        "💳 Card",
        "🆔 KYC", 
        "🔧 Technical",
        "💰 Payment",
        "❓ Other"
    ]
    
    # Status options
    TICKET_STATUS = {
        'open': '🟢 Open',
        'in_progress': '🟡 In Progress',
        'closed': '🔴 Closed'
    }
