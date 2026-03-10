from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_db
from models import User, Ticket
from keyboards.user_keyboards import *
from utils.helpers import generate_ticket_id, format_ticket_for_admin
from config import Config
import logging

router = Router()

class TicketForm(StatesGroup):
    choosing_category = State()
    entering_name = State()
    entering_email = State()
    entering_phone = State()
    entering_description = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    # Save or update user in database
    async for session in get_db():
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            session.add(user)
            await session.commit()
    
    welcome_text = """
🎫 <b>Welcome to ToonPay Support Bot!</b>

I'm here to help you with any issues you might have.

<b>How to create a ticket:</b>
1️⃣ Click 'New Ticket'
2️⃣ Select your issue category
3️⃣ Provide your details
4️⃣ Describe your issue
5️⃣ Submit

⏱️ Response time: Within 24 hours

Click the button below to start!
"""
    await message.reply(welcome_text, reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "new_ticket")
async def new_ticket(callback: CallbackQuery, state: FSMContext):
    """Start new ticket creation"""
    await callback.message.edit_text(
        "📋 <b>Select your issue category:</b>",
        reply_markup=get_categories_keyboard()
    )
    await state.set_state(TicketForm.choosing_category)

@router.callback_query(TicketForm.choosing_category, F.data.startswith("cat_"))
async def category_chosen(callback: CallbackQuery, state: FSMContext):
    """Handle category selection"""
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    
    await callback.message.edit_text(
        "👤 <b>Please enter your full name:</b>\n\n"
        "Example: John Doe",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TicketForm.entering_name)

@router.message(TicketForm.entering_name)
async def name_entered(message: Message, state: FSMContext):
    """Handle name input"""
    await state.update_data(name=message.text)
    
    await message.reply(
        "📧 <b>Please enter your email address:</b>\n\n"
        "Example: user@example.com",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TicketForm.entering_email)

@router.message(TicketForm.entering_email)
async def email_entered(message: Message, state: FSMContext):
    """Handle email input"""
    await state.update_data(email=message.text)
    
    await message.reply(
        "📱 <b>Please enter your phone number:</b>\n\n"
        "Example: +1234567890",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TicketForm.entering_phone)

@router.message(TicketForm.entering_phone)
async def phone_entered(message: Message, state: FSMContext):
    """Handle phone input"""
    await state.update_data(phone=message.text)
    
    await message.reply(
        "📝 <b>Please describe your issue in detail:</b>\n\n"
        "Include all relevant information to help us assist you better.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TicketForm.entering_description)

@router.message(TicketForm.entering_description)
async def description_entered(message: Message, state: FSMContext):
    """Handle description and create ticket"""
    data = await state.get_data()
    
    # Generate ticket ID
    ticket_id = generate_ticket_id()
    
    # Save ticket to database
    async for session in get_db():
        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=message.from_user.id,
            user_name=message.from_user.full_name,
            category=data['category'],
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            description=message.text
        )
        session.add(ticket)
        await session.commit()
        
        # Send to admin group
        from bot import bot
        admin_message = format_ticket_for_admin({
            'ticket_id': ticket_id,
            'user_id': message.from_user.id,
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'category': data['category'],
            'description': message.text,
            'status': 'open',
            'created_at': ticket.created_at
        })
        
        sent_message = await bot.send_message(
            Config.ADMIN_GROUP_ID,
            admin_message,
            reply_markup=get_ticket_action_keyboard(ticket_id)
        )
        
        # Save admin group message ID
        ticket.admin_group_message_id = sent_message.message_id
        await session.commit()
    
    await message.reply(
        f"✅ <b>Ticket Created Successfully!</b>\n\n"
        f"Your ticket ID: <code>{ticket_id}</code>\n\n"
        f"We'll get back to you within 24 hours.\n"
        f"You can check your ticket status anytime.",
        reply_markup=get_main_menu_keyboard()
    )
    
    await state.clear()

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel current action"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Action cancelled. What would you like to do?",
        reply_markup=get_main_menu_keyboard()
    )
