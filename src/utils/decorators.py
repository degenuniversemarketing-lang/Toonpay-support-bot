from functools import wraps
from aiogram.types import Message
from config import Config

def super_admin_only():
    """Decorator to restrict access to super admin only"""
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if message.from_user.id != Config.SUPER_ADMIN_ID:
                await message.reply("⛔ You are not authorized to use this command.")
                return
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator

def admin_group_only():
    """Decorator to restrict access to admin group only"""
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if message.chat.id != Config.ADMIN_GROUP_ID:
                # Don't reply if not in admin group
                return
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator

def private_chat_only():
    """Decorator to ensure command works only in private chat"""
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if message.chat.type != 'private':
                return
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator
