from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select
from database import get_db
from database import AdminGroup
import logging

logger = logging.getLogger(__name__)
router = Router()

# ONLY /support COMMAND WORKS IN GROUPS
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("support"))
async def group_support(message: Message):
    """Handle /support command in groups - ONLY command that works"""
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
        
        await message.reply(
            "🎫 <b>Need help from ToonPay Support?</b>\n\n"
            "Click the button below to open a private chat with our support bot and create a ticket.\n\n"
            "⏱️ <b>ToonPay Support Available 24/7</b>",
            reply_markup=support_button
        )
        
        # Delete the original /support command
        try:
            await message.delete()
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error in group support: {e}")

# DELETE ALL OTHER COMMANDS IN GROUPS
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("start"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("new_ticket"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("my_tickets"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("help"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("profile"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("update_email"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("update_phone"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("tickets"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("search"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("reply"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("data"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("getdata"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("stats"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("panel"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("addgroup"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("removegroup"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("listgroups"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("broadcast"))
@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("editcmd"))
async def delete_other_commands(message: Message):
    """Delete any other command in groups - only /support works"""
    try:
        await message.delete()
    except:
        pass

# Ignore all other messages in groups
@router.message(F.chat.type.in_({'group', 'supergroup'}))
async def ignore_other_messages(message: Message):
    """Ignore all other messages in groups"""
    pass
