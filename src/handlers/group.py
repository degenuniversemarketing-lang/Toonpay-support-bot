from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_db
from models import AdminGroup
from keyboards.user_keyboards import get_main_menu_keyboard
from config import Config

router = Router()

@router.message(F.chat.type.in_({'group', 'supergroup'}), Command("support"))
async def group_support(message: Message):
    """Handle /support command in groups"""
    # Check if bot is activated in this group
    async for session in get_db():
        admin_group = await session.get(AdminGroup, message.chat.id)
        
        if not admin_group or not admin_group.is_active:
            return  # Bot not activated in this group
    
    # Reply with support button
    support_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📩 Submit Ticket",
            url=f"https://t.me/{(await message.bot.me()).username}?start=from_group"
        )]
    ])
    
    await message.reply(
        "🎫 <b>Need help from ToonPay Support?</b>\n\n"
        "Click the button below to open a private chat with our support bot and create a ticket.",
        reply_markup=support_button
    )
