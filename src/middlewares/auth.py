from telegram import Update
from telegram.ext import ContextTypes
from src.models import Group
from src.database import db_session

class AuthMiddleware:
    """Middleware to check if bot is active in group"""
    
    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Skip if not in group
        if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
            return True
        
        # Check if group is active
        group = db_session.query(Group).filter_by(
            group_id=update.effective_chat.id, 
            is_active=True
        ).first()
        
        if not group:
            # Bot not active in this group, ignore message
            return False
        
        return True
