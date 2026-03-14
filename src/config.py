import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', '0'))
    SUPER_ADMIN_IDS = [int(id) for id in os.getenv('SUPER_ADMIN_IDS', '').split(',') if id]
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Categories
    CATEGORIES = [
        'Card',
        'KYC',
        'Technical',
        'Payment',
        'Other'
    ]
    
    # Ticket status
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_CLOSED = 'closed'
