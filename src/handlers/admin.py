from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, or_, and_
from database import get_db
from database import Ticket, User
from keyboards.admin_keyboards import get_ticket_action_keyboard
from utils.decorators import admin_group_only
from config import Config
from datetime import datetime
import logging

router = Router()
logger = logging.getLogger(__name__)

class AdminReply(StatesGroup):
    waiting_for_reply = State()

@router.callback_query(F.data.startswith("reply_"))
async def admin_reply_start(callback: CallbackQuery, state: FSMContext):
    """Start admin reply process"""
    try:
        ticket_id = callback.data.replace("reply_", "")
        await state.update_data(ticket_id=ticket_id)
        await state.update_data(chat_id=callback.message.chat.id)
        await state.update_data(message_id=callback.message.message_id)
        
        await callback.message.edit_text(
            f"✏️ Type your reply for ticket {ticket_id}:\n"
            "(or /cancel to cancel)",
            reply_markup=None
        )
        await state.set_state(AdminReply.waiting_for_reply)
        await callback.answer("Please type your reply")
    except Exception as e:
        logger.error(f"Error in reply start: {e}")
        await callback.answer("Error starting reply")

@router.message(AdminReply.waiting_for_reply)
async def admin_reply_send(message: Message, state: FSMContext):
    """Send admin reply to user"""
    try:
        data = await state.get_data()
        ticket_id = data.get('ticket_id')
        original_chat_id = data.get('chat_id')
        original_message_id = data.get('message_id')
        
        if not ticket_id:
            await message.reply("❌ No ticket ID found. Please try again.")
            await state.clear()
            return
        
        async for session in get_db():
            # Get ticket
            result = await session.execute(
                select(Ticket).where(Ticket.ticket_id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                await message.reply(f"❌ Ticket {ticket_id} not found")
                await state.clear()
                return
            
            # Update ticket
            ticket.admin_answer = message.text
            ticket.answered_by = message.from_user.id
            ticket.answered_at = datetime.utcnow()
            ticket.status = 'closed'
            
            await session.commit()
            
            # Send reply to user
            try:
                await message.bot.send_message(
                    ticket.user_id,
                    f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n"
                    f"<b>Support Team:</b>\n{message.text}\n\n"
                    f"<i>This ticket is now closed. ToonPay Support available 24/7.</i>"
                )
                logger.info(f"Reply sent to user {ticket.user_id} for ticket {ticket_id}")
            except Exception as e:
                logger.error(f"Failed to send reply to user: {e}")
                await message.reply(f"⚠️ Reply saved but couldn't notify user. They might have blocked the bot.")
            
            # Update admin group message
            try:
                # Get admin username
                admin_username = message.from_user.username or f"Admin {message.from_user.id}"
                
                # Get user info for display
                user_result = await session.execute(
                    select(User).where(User.telegram_id == ticket.user_id)
                )
                user = user_result.scalar_one_or_none()
                user_display = user.first_name if user else "User"
                
                # Create updated message
                updated_text = f"""
<b>✅ Ticket {ticket_id} - Closed</b>

<b>👤 User:</b> {user_display}
<b>📧 Email:</b> {ticket.email}
<b>📱 Phone:</b> {ticket.phone}

<b>📝 Issue:</b>
{ticket.description}

<b>💬 Reply sent by:</b> @{admin_username}
<b>📨 Reply:</b> {message.text}

<b>📅 Closed:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
"""
                
                await message.bot.edit_message_text(
                    chat_id=original_chat_id or Config.ADMIN_GROUP_ID,
                    message_id=original_message_id,
                    text=updated_text,
                    reply_markup=None
                )
                logger.info(f"Admin group message updated for ticket {ticket_id}")
            except Exception as e:
                logger.error(f"Failed to update admin group message: {e}")
            
            await message.reply(f"✅ Reply sent for ticket {ticket_id}")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in reply send: {e}")
        await message.reply(f"❌ Error sending reply: {str(e)}")
        await state.clear()

@router.callback_query(F.data.startswith("progress_"))
async def ticket_in_progress(callback: CallbackQuery):
    """Mark ticket as in progress"""
    try:
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
                
                # Get admin username
                admin_username = callback.from_user.username or f"Admin {callback.from_user.id}"
                
                # Update message
                updated_text = callback.message.text + f"\n\n🟡 <b>Status: In Progress</b>\nBy: @{admin_username}"
                
                await callback.message.edit_text(
                    updated_text,
                    reply_markup=get_ticket_action_keyboard(ticket_id)
                )
                
                await callback.answer("Ticket marked as in progress")
            else:
                await callback.answer("Ticket not found")
    except Exception as e:
        logger.error(f"Error in progress: {e}")
        await callback.answer("Error updating ticket")

@router.callback_query(F.data.startswith("close_"))
async def ticket_close(callback: CallbackQuery):
    """Close ticket without reply"""
    try:
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
                
                # Get admin username
                admin_username = callback.from_user.username or f"Admin {callback.from_user.id}"
                
                # Notify user
                try:
                    await callback.bot.send_message(
                        ticket.user_id,
                        f"🔴 <b>Ticket #{ticket_id} Closed</b>\n\n"
                        f"Your ticket has been closed by support team.\n"
                        f"Create a new ticket if you need further assistance.\n\n"
                        f"⏱️ ToonPay Support Available 24/7"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user: {e}")
                
                # Update admin message
                await callback.message.edit_text(
                    f"🔴 <b>Ticket {ticket_id} - Closed by @{admin_username}</b>\n\n"
                    f"{callback.message.text}",
                    reply_markup=None
                )
                
                await callback.answer("Ticket closed")
            else:
                await callback.answer("Ticket not found")
    except Exception as e:
        logger.error(f"Error in close: {e}")
        await callback.answer("Error closing ticket")

@router.message(Command("reply"))
@admin_group_only()
async def reply_by_command(message: Message):
    """Reply to ticket using command: /reply TICKET_ID Your message"""
    try:
        # Parse command: /reply TICKET_ID Your message here
        text = message.text.replace("/reply", "").strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) != 2:
            await message.reply("❌ Usage: /reply TICKET_ID Your reply message")
            return
        
        ticket_id, reply_text = parts
        
        async for session in get_db():
            # Find ticket
            result = await session.execute(
                select(Ticket).where(Ticket.ticket_id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            
            if not ticket:
                await message.reply(f"❌ Ticket {ticket_id} not found")
                return
            
            # Update ticket
            ticket.admin_answer = reply_text
            ticket.answered_by = message.from_user.id
            ticket.answered_at = datetime.utcnow()
            ticket.status = 'closed'
            
            await session.commit()
            
            # Send reply to user
            try:
                await message.bot.send_message(
                    ticket.user_id,
                    f"📬 <b>Reply to your ticket #{ticket_id}</b>\n\n"
                    f"<b>Support Team:</b>\n{reply_text}\n\n"
                    f"<i>This ticket is now closed. ToonPay Support available 24/7.</i>"
                )
            except Exception as e:
                logger.error(f"Failed to send reply to user: {e}")
            
            # Update admin group message if exists
            if ticket.admin_group_message_id:
                try:
                    await message.bot.edit_message_text(
                        chat_id=Config.ADMIN_GROUP_ID,
                        message_id=ticket.admin_group_message_id,
                        text=f"✅ <b>Ticket {ticket_id} - Closed</b>\n\n"
                             f"<b>Reply sent by:</b> @{message.from_user.username}\n"
                             f"<b>Reply:</b> {reply_text}",
                        reply_markup=None
                    )
                except:
                    pass
            
            await message.reply(f"✅ Reply sent for ticket {ticket_id}")
            
    except Exception as e:
        logger.error(f"Error in reply command: {e}")
        await message.reply(f"❌ Error: {str(e)}")
