from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select
from database import get_db
from database import AdminGroup
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("support"))
async def group_support(message: Message):
    """Handle /support command in groups - ONLY command that works in groups"""
    try:
        # Check if bot is activated in this group
        async for session in get_db():
            result = await session.execute(
                select(AdminGroup).where(
                    AdminGroup.group_id == message.chat.id,
                    AdminGroup.is_active == True
                )
            )
            admin_group = result.scalar_one_or_none()
            
            if not admin_group:
                # Try to delete the command message if bot not activated
                try:
                    await message.delete()
                except:
                    pass
                return
        
        # Get bot username
        bot_me = await message.bot.me()
        
        # Reply with support button
        support_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📩 Submit Ticket",
                url=f"https://t.me/{bot_me.username}?start=from_group"
            )]
        ])
        
        # Send response
        await message.reply(
            "🎫 <b>Need help from ToonPay Support?</b>\n\n"
            "Click the button below to open a private chat with our support bot and create a ticket.\n\n"
            "⏱️ <b>ToonPay Support Available 24/7</b>",
            reply_markup=support_button
        )
        
        # Try to delete the original /support command
        try:
            await message.delete()
        except Exception as e:
            logger.debug(f"Could not delete message: {e}")
            
    except Exception as e:
        logger.error(f"Error in group support: {e}")

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("start"))
async def group_start(message: Message):
    """Handle /start command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("new_ticket"))
async def group_new_ticket(message: Message):
    """Handle /new_ticket command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("my_tickets"))
async def group_my_tickets(message: Message):
    """Handle /my_tickets command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("help"))
async def group_help(message: Message):
    """Handle /help command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("profile"))
async def group_profile(message: Message):
    """Handle /profile command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("update_email"))
async def group_update_email(message: Message):
    """Handle /update_email command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("update_phone"))
async def group_update_phone(message: Message):
    """Handle /update_phone command in groups - delete it"""
    try:
        await message.delete()
    except:
        pass

# Ignore all other commands in groups
@router.message(F.chat.type.in_({'group', 'supergroup'}))
async def ignore_other_commands(message: Message):
    """Ignore all other commands in groups - only /support works"""
    if message.text and message.text.startswith('/'):
        # Try to delete any other command
        try:
            await message.delete()
        except:
            pass
