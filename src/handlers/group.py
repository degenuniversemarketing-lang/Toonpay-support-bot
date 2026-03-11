from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select
from database import get_db
from database import AdminGroup

router = Router()

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("support"))
async def group_support(message: Message):
    """Handle /support command in groups"""
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
            return  # Bot not activated in this group
    
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
        "⏱️ Response time: Within 24 hours",
        reply_markup=support_button
    )
