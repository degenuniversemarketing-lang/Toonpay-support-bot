import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    SUPER_ADMIN_IDS = [int(id) for id in os.getenv('SUPER_ADMIN_IDS', '').split(',') if id]
    ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', 0))
    
    # Categories
    CATEGORIES = {
        'card': '💳 Card Issue',
        'kyc': '📋 KYC Issue',
        'technical': '🔧 Technical Issue',
        'payment': '💰 Payment Issue',
        'other': '❓ Other'
    }
    
    # Bot Settings
    TICKETS_PER_PAGE = 10
    MAX_PENDING_DISPLAY = 300
