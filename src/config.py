# src/config.py
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

load_dotenv()

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REPLIED_CLOSED = "replied_closed"
    CLOSED_NO_REPLY = "closed_no_reply"

class TicketCategory(Enum):
    CARD = "card"
    KYC = "kyc"
    TECHNICAL = "technical"
    PAYMENT = "payment"
    OTHER = "other"

@dataclass
class Config:
    # Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    
    # Groups
    ADMIN_GROUP_ID: int = int(os.getenv("ADMIN_GROUP_ID", "0"))
    BACKUP_GROUP_ID: int = int(os.getenv("BACKUP_GROUP_ID", "0"))
    
    # Super Admins
    SUPER_ADMIN_IDS: List[int] = [
        int(id.strip()) for id in os.getenv("SUPER_ADMIN_IDS", "").split(",") if id.strip()
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///toonpay.db")
    
    # Support
    SUPPORT_MESSAGE: str = os.getenv("SUPPORT_MESSAGE", "ToonPay Support Available 24/7")
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "ToonPay")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@toonpay.com")
    
    # Categories with display names
    CATEGORIES: Dict[str, Dict[str, str]] = {
        "card": {
            "name": "💳 Card Issues",
            "emoji": "💳",
            "description": "Card not working, blocked card, card limits"
        },
        "kyc": {
            "name": "🆔 KYC Verification",
            "emoji": "🆔",
            "description": "KYC pending, verification failed, document issues"
        },
        "technical": {
            "name": "🔧 Technical Support",
            "emoji": "🔧",
            "description": "App not working, bugs, errors"
        },
        "payment": {
            "name": "💰 Payment Issues",
            "emoji": "💰",
            "description": "Failed payments, refunds, transaction issues"
        },
        "other": {
            "name": "❓ Other Questions",
            "emoji": "❓",
            "description": "General inquiries, suggestions"
        }
    }
    
    # Status emojis
    STATUS_EMOJIS: Dict[str, str] = {
        "open": "🟢",
        "in_progress": "🟡",
        "replied_closed": "✅",
        "closed_no_reply": "🔴"
    }
    
    # Allowed groups (will be loaded from database)
    @property
    def ALLOWED_GROUPS(self) -> List[int]:
        # This will be populated from database
        return []

config = Config()
