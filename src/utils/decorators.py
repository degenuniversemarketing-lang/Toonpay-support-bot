from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.config import Config
from src.models import AllowedGroup
from src.database import db_session

def super_admin_only(func):
    """Decorator to restrict command to super admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in Config.SUPER_ADMIN_IDS:
            await update.message.reply_text("⛔ This command is only for super admins.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def admin_group_only(func):
    """Decorator to restrict command to admin group only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_chat or update.effective_chat.id != Config.ADMIN_GROUP_ID:
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def private_chat_only(func):
    """Decorator to restrict command to private chat only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat and update.effective_chat.type != 'private':
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def group_command_only(func):
    """Decorator for commands that work only in allowed groups"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_chat or update.effective_chat.type == 'private':
            return
        
        # Check if group is allowed
        allowed_group = db_session.query(AllowedGroup).filter_by(
            group_id=update.effective_chat.id, 
            is_active=True
        ).first()
        
        if not allowed_group:
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper
