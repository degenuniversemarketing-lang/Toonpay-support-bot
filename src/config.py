# src/config.py
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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
    try:
        ADMIN_GROUP_ID: int = int(os.getenv("ADMIN_GROUP_ID", "0"))
        BACKUP_GROUP_ID: int = int(os.getenv("BACKUP_GROUP_ID", "0"))
    except ValueError:
        logger.error("Invalid group ID format in environment variables")
        ADMIN_GROUP_ID = 0
        BACKUP_GROUP_ID = 0
    
    # Super Admins
    try:
        SUPER_ADMIN_IDS: List[int] = [
            int(id.strip()) for id in os.getenv("SUPER_ADMIN_IDS", "").split(",") 
            if id.strip()
        ]
    except ValueError:
        logger.error("Invalid super admin ID format")
        SUPER_ADMIN_IDS = []
    
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
    
    # Backup settings
    ENABLE_AUTO_BACKUP: bool = os.getenv("ENABLE_AUTO_BACKUP", "true").lower() == "true"
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.BOT_TOKEN:
            logger.error("BOT_TOKEN is not set!")
        if not self.ADMIN_GROUP_ID:
            logger.warning("ADMIN_GROUP_ID is not set!")
        if not self.SUPER_ADMIN_IDS:
            logger.warning("SUPER_ADMIN_IDS is not set!")

config = Config()
