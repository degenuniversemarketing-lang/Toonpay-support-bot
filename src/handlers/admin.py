from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, or_
from database import get_db
from models import Ticket, User
from keyboards.admin_keyboards import get_ticket_action_keyboard
from utils.decorators import admin_group_only
from config import Config
from datetime import datetime

router = Router()

class AdminReply(StatesGroup):
    waiting_for_reply = State()

@router.callback_query(F.data.startswith("reply_"))
async def admin_reply_start(callback: CallbackQuery, state: FSMContext):
    """Start admin reply process"""
    ticket_id = callback.data.replace("reply_", "")
    await state.update_data(ticket_id=ticket_id)
    
    await callback.message.edit_text(
        f"✏️ Type your reply for ticket {ticket_id}:\n"
        "(or /cancel to cancel)",
        reply_markup=None
    )
    await state.set_state(AdminReply.waiting_for_reply)

@router.message(AdminReply.waiting_for_reply)
async def admin_reply_send(message: Message, state: FSMContext):
    """Send admin reply to user"""
    data = await state.get_data()
    ticket_id = data['ticket_id']
    
    async for session in get_db():
        # Get ticket
        result = await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        
        if ticket:
            # Update ticket
            ticket.admin_answer = message.text
            ticket.answered_by = message.from_user.id
            ticket.answered_at = datetime.utcnow()
            ticket.status = 'closed'
            
            await session.commit()
            
            # Send reply to user
            await message.bot.send_message(
                ticket.user_id,
                f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n"
                f"<b>Support Team:</b>\n{message.text}\n\n"
                f"<i>This ticket is now closed. Create a new ticket for any other questions.</i>"
            )
            
            # Update admin group message
            await message.bot.edit_message_text(
                chat_id=Config.ADMIN_GROUP_ID,
                message_id=ticket.admin_group_message_id,
                text=f"✅ <b>Ticket {ticket_id} - Closed</b>\n\n"
                     f"<b>Reply sent by:</b> @{message.from_user.username}\n"
                     f"<b>Reply:</b> {message.text}",
                reply_markup=None
            )
            
            await message.reply(f"✅ Reply sent to user for ticket {ticket_id}")
    
    await state.clear()

@router.callback_query(F.data.startswith("progress_"))
async def ticket_in_progress(callback: CallbackQuery):
    """Mark ticket as in progress"""
    ticket_id = callback.data.replace("progress_", "")
    
    async for session in get_db():
        result = await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        
        if ticket:
            ticket.status = 'in_progress'
            ticket.in_progress_by = callback.from_user.id
            ticket.in_progress_at = datetime.utcnow()
            await session.commit()
            
            # Update message
            await callback.message.edit_text(
                f"{callback.message.text}\n\n"
                f"🟡 <b>Status: In Progress</b>\n"
                f"By: @{callback.from_user.username}",
                reply_markup=get_ticket_action_keyboard(ticket_id)
            )
            
            await callback.answer("Ticket marked as in progress")

@router.callback_query(F.data.startswith("close_"))
async def ticket_close(callback: CallbackQuery):
    """Close ticket without reply"""
    ticket_id = callback.data.replace("close_", "")
    
    async for session in get_db():
        result = await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        
        if ticket:
            ticket.status = 'closed'
            ticket.answered_by = callback.from_user.id
            ticket.answered_at = datetime.utcnow()
            await session.commit()
            
            # Notify user
            await callback.bot.send_message(
                ticket.user_id,
                f"🔴 <b>Ticket #{ticket_id} Closed</b>\n\n"
                f"Your ticket has been closed by support team.\n"
                f"Create a new ticket if you need further assistance."
            )
            
            # Update admin message
            await callback.message.edit_text(
                f"🔴 <b>Ticket {ticket_id} - Closed by @{callback.from_user.username}</b>\n\n"
                f"{callback.message.text}",
                reply_markup=None
            )
            
            await callback.answer("Ticket closed")

@router.message(Command("search"))
@admin_group_only()
async def search_user(message: Message):
    """Search user by username, ID, or email"""
    search_term = message.text.replace("/search", "").strip()
    
    if not search_term:
        await message.reply("Usage: /search <username/email/user_id>")
        return
    
    async for session in get_db():
        # Search users
        query = select(User).where(
            or_(
                User.username.ilike(f"%{search_term}%"),
                User.email.ilike(f"%{search_term}%"),
                User.telegram_id == (int(search_term) if search_term.isdigit() else 0)
            )
        )
        result = await session.execute(query)
        users = result.scalars().all()
        
        if not users:
            await message.reply("❌ No users found")
            return
        
        for user in users:
            # Get user's tickets
            tickets_query = select(Ticket).where(Ticket.user_id == user.telegram_id).order_by(Ticket.created_at.desc())
            tickets_result = await session.execute(tickets_query)
            tickets = tickets_result.scalars().all()
            
            # Format response
            response = f"""
<b>👤 User Found:</b>
• ID: <code>{user.telegram_id}</code>
• Username: @{user.username if user.username else 'N/A'}
• Name: {user.first_name} {user.last_name or ''}
• Email: {user.email or 'N/A'}
• Phone: {user.phone or 'N/A'}
• Registered: {user.registered_at.strftime('%Y-%m-%d %H:%M')}

<b>📊 Statistics:</b>
• Total Tickets: {len(tickets)}
• Open: {sum(1 for t in tickets if t.status == 'open')}
• In Progress: {sum(1 for t in tickets if t.status == 'in_progress')}
• Closed: {sum(1 for t in tickets if t.status == 'closed')}

<b>📋 Recent Tickets:</b>
"""
            for ticket in tickets[-3:]:  # Show last 3 tickets
                status_emoji = '🟢' if ticket.status == 'open' else '🟡' if ticket.status == 'in_progress' else '🔴'
                response += f"\n{status_emoji} {ticket.ticket_id} - {ticket.category[:30]}"
                response += f"\n   Created: {ticket.created_at.strftime('%Y-%m-%d')}"
                if ticket.admin_answer:
                    response += f"\n   ✓ Answered"
            
            await message.reply(response)
