from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
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
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
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
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

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
    
    await message.answer(
        "📧 <b>Please enter your email address:</b>\n\n"
        "Example: user@example.com",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TicketForm.entering_email)

@router.message(TicketForm.entering_email)
async def email_entered(message: Message, state: FSMContext):
    """Handle email input"""
    await state.update_data(email=message.text)
    
    await message.answer(
        "📱 <b>Please enter your phone number:</b>\n\n"
        "Example: +1234567890",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(TicketForm.entering_phone)

@router.message(TicketForm.entering_phone)
async def phone_entered(message: Message, state: FSMContext):
    """Handle phone input"""
    await state.update_data(phone=message.text)
    
    await message.answer(
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
        await session.refresh(ticket)
        
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
        
        # Import here to avoid circular import
        from keyboards.admin_keyboards import get_ticket_action_keyboard
        
        sent_message = await bot.send_message(
            Config.ADMIN_GROUP_ID,
            admin_message,
            reply_markup=get_ticket_action_keyboard(ticket_id)
        )
        
        # Save admin group message ID
        ticket.admin_group_message_id = sent_message.message_id
        await session.commit()
    
    await message.answer(
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

@router.callback_query(F.data == "my_tickets")
async def my_tickets(callback: CallbackQuery):
    """Show user's tickets"""
    async for session in get_db():
        result = await session.execute(
            select(Ticket).where(Ticket.user_id == callback.from_user.id)
        )
        tickets = result.scalars().all()
        
        if not tickets:
            await callback.message.edit_text(
                "📭 You haven't created any tickets yet.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        response = "📋 <b>Your Tickets:</b>\n\n"
        for ticket in tickets[-5:]:  # Show last 5 tickets
            status_emoji = '🟢' if ticket.status == 'open' else '🟡' if ticket.status == 'in_progress' else '🔴'
            response += f"{status_emoji} <code>{ticket.ticket_id}</code> - {ticket.category}\n"
            response += f"   Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            if ticket.admin_answer:
                response += f"   ✓ Answered\n"
            response += "\n"
        
        await callback.message.edit_text(
            response,
            reply_markup=get_main_menu_keyboard()
        )

@router.callback_query(F.data == "help")
async def help_command(callback: CallbackQuery):
    """Show help message"""
    help_text = """
ℹ️ <b>Help & Support</b>

<b>How to create a ticket:</b>
1. Click "New Ticket"
2. Select category
3. Provide your details
4. Describe your issue
5. Submit

<b>Important Notes:</b>
• Each ticket is for one issue only
• Tickets close after admin reply
• Create new ticket for new questions
• Response Time: Within 24 hours 🚀

Need immediate assistance? Contact @ToonPaySupport
"""
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu_keyboard()
    )
