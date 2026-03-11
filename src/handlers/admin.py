# src/handlers/admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime

from src.database import db
from src.config import config
from src.keyboards import get_filter_keyboard, get_ticket_action_keyboard
from src.utils import (
    format_ticket_info, format_user_info, format_ticket_list,
    format_statistics, format_user_statistics, escape_html
)

logger = logging.getLogger(__name__)

# Conversation states
REPLY_TEXT = 0
SEARCH_QUERY = 1

class AdminHandlers:
    
    @staticmethod
    async def check_admin(update: Update) -> bool:
        """Check if user is admin and in admin group"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if in admin group
        if chat_id != config.ADMIN_GROUP_ID:
            return False
        
        # Check if user is admin
        return db.is_admin(user_id)
    
    @staticmethod
    async def tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tickets command"""
        if not await AdminHandlers.check_admin(update):
            return
        
        tickets = db.get_tickets_by_status('open')
        
        if tickets:
            text = format_ticket_list(tickets, "📋 Open Tickets")
        else:
            text = "📭 No open tickets at the moment."
        
        await update.message.reply_text(
            text,
            reply_markup=get_filter_keyboard(),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /data command - show statistics"""
        if not await AdminHandlers.check_admin(update):
            return
        
        stats = db.get_statistics()
        text = format_statistics(stats)
        
        await update.message.reply_text(
            text,
            parse_mode='HTML'
        )
    
    @staticmethod
    async def getdata(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /getdata command - search users"""
        if not await AdminHandlers.check_admin(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /getdata <user_id or username or email or phone>"
            )
            return
        
        search_term = ' '.join(context.args)
        users = db.search_users(search_term)
        
        if not users:
            await update.message.reply_text("❌ No user found.")
            return
        
        for user in users:
            # Get user tickets
            tickets = db.get_user_tickets(user.user_id, limit=10)
            stats = db.get_user_statistics(user.user_id)
            
            text = format_user_info(user)
            text += format_user_statistics(user.user_id, stats)
            
            if tickets:
                text += "\n📋 <b>Recent Tickets:</b>\n"
                for ticket in tickets[:5]:
                    status_emoji = config.STATUS_EMOJIS.get(ticket.status, '⚪')
                    category_info = config.CATEGORIES.get(ticket.category, {'emoji': '📌'})
                    text += f"\n{status_emoji} <code>{ticket.ticket_id}</code> {category_info['emoji']}"
                    text += f"\n   Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}"
                    if ticket.admin_reply:
                        text += f"\n   ✅ Replied"
                    text += "\n"
            
            await update.message.reply_text(
                text,
                parse_mode='HTML'
            )
    
    @staticmethod
    async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reply command"""
        if not await AdminHandlers.check_admin(update):
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /reply <ticket_id> <your reply message>"
            )
            return
        
        ticket_id = context.args[0]
        reply_text = ' '.join(context.args[1:])
        
        ticket = db.get_ticket(ticket_id)
        if not ticket:
            await update.message.reply_text("❌ Ticket not found.")
            return
        
        # Save reply
        db.reply_to_ticket(ticket_id, reply_text, update.effective_user.id)
        
        # Send reply to user
        try:
            user_message = f"""
📬 <b>Reply to your ticket #{ticket_id}</b>

<b>Support Team:</b>
{escape_html(reply_text)}

This ticket is now closed. Create a new ticket for any other questions.

{config.SUPPORT_MESSAGE}
"""
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=user_message,
                parse_mode='HTML'
            )
            
            # Log action
            db.log_action(
                update.effective_user.id,
                'reply_ticket',
                {'ticket_id': ticket_id, 'user_id': ticket.user_id}
            )
            
        except Exception as e:
            logger.error(f"Failed to send reply to user: {e}")
        
        await update.message.reply_text(
            f"✅ Reply sent for ticket {ticket_id}"
        )
    
    @staticmethod
    async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not await AdminHandlers.check_admin(update):
            return
        
        await update.message.reply_text(
            "🔍 <b>Enter search term</b> (user ID, username, email, or phone):",
            parse_mode='HTML'
        )
        return SEARCH_QUERY
    
    @staticmethod
    async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle search query"""
        if not await AdminHandlers.check_admin(update):
            return ConversationHandler.END
        
        query = update.message.text.strip()
        users = db.search_users(query)
        
        if not users:
            await update.message.reply_text("❌ No users found.")
            return ConversationHandler.END
        
        for user in users:
            tickets = db.get_user_tickets(user.user_id, limit=5)
            stats = db.get_user_statistics(user.user_id)
            
            text = format_user_info(user)
            text += format_user_statistics(user.user_id, stats)
            
            if tickets:
                text += "\n📋 <b>Recent Tickets:</b>\n"
                for ticket in tickets:
                    status_emoji = config.STATUS_EMOJIS.get(ticket.status, '⚪')
                    text += f"\n{status_emoji} <code>{ticket.ticket_id}</code>"
                    text += f"\n   Q: {escape_html(ticket.question[:50])}..."
                    if ticket.admin_reply:
                        text += f"\n   A: {escape_html(ticket.admin_reply[:50])}..."
                    text += "\n"
            
            await update.message.reply_text(
                text,
                parse_mode='HTML'
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if not db.is_admin(user_id):
            await query.edit_message_text("❌ You are not authorized.")
            return
        
        data = query.data
        
        if data.startswith('inprogress_'):
            ticket_id = data.replace('inprogress_', '')
            db.update_ticket_status(ticket_id, 'in_progress', user_id)
            
            await query.edit_message_text(
                f"✅ Ticket {ticket_id} marked as in progress."
            )
            
            # Update original message
            await AdminHandlers.update_ticket_message(context, ticket_id)
            
            # Log action
            db.log_action(user_id, 'mark_in_progress', {'ticket_id': ticket_id})
        
        elif data.startswith('close_'):
            ticket_id = data.replace('close_', '')
            ticket = db.get_ticket(ticket_id)
            
            if ticket:
                db.close_ticket_no_reply(ticket_id, user_id)
                
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=ticket.user_id,
                        text=f"""
🔴 <b>Ticket #{ticket_id} Closed</b>

Your ticket has been closed. If you still need assistance, please create a new ticket.

{config.SUPPORT_MESSAGE}
""",
                        parse_mode='HTML'
                    )
                except:
                    pass
                
                await query.edit_message_text(
                    f"✅ Ticket {ticket_id} closed without reply."
                )
                
                # Log action
                db.log_action(user_id, 'close_no_reply', {'ticket_id': ticket_id})
        
        elif data.startswith('reply_'):
            ticket_id = data.replace('reply_', '')
            context.user_data['reply_ticket_id'] = ticket_id
            
            await query.edit_message_text(
                f"📝 <b>Enter your reply for ticket {ticket_id}:</b>\n\n"
                f"(or /cancel to cancel)",
                parse_mode='HTML'
            )
            return REPLY_TEXT
        
        elif data.startswith('viewuser_'):
            ticket_id = data.replace('viewuser_', '')
            ticket = db.get_ticket(ticket_id)
            
            if ticket:
                user = db.get_user(ticket.user_id)
                if user:
                    tickets = db.get_user_tickets(user.user_id, limit=5)
                    stats = db.get_user_statistics(user.user_id)
                    
                    text = format_user_info(user)
                    text += format_user_statistics(user.user_id, stats)
                    
                    if tickets:
                        text += "\n📋 <b>Recent Tickets:</b>\n"
                        for t in tickets:
                            status_emoji = config.STATUS_EMOJIS.get(t.status, '⚪')
                            text += f"\n{status_emoji} <code>{t.ticket_id}</code>"
                            text += f"\n   Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}"
                            if t.status == 'open':
                                text += f"\n   [Reply to this ticket]"
                            text += "\n"
                    
                    keyboard = [[
                        InlineKeyboardButton("🔙 Back", callback_data=f'back_to_ticket_{ticket_id}')
                    ]]
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
        
        elif data.startswith('back_to_ticket_'):
            ticket_id = data.replace('back_to_ticket_', '')
            ticket = db.get_ticket(ticket_id)
            
            if ticket:
                text = format_ticket_info(ticket, include_admin=True)
                await query.edit_message_text(
                    text,
                    reply_markup=get_ticket_action_keyboard(ticket_id, ticket.status),
                    parse_mode='HTML'
                )
        
        elif data.startswith('filter_'):
            filter_type = data.replace('filter_', '')
            
            if filter_type == 'all':
                tickets = db.get_all_tickets(limit=50)
                title = "📋 All Tickets (Last 50)"
            elif filter_type == 'open':
                tickets = db.get_tickets_by_status('open', limit=50)
                title = "🟢 Open Tickets"
            elif filter_type == 'in_progress':
                tickets = db.get_tickets_by_status('in_progress', limit=50)
                title = "🟡 In Progress Tickets"
            elif filter_type == 'replied_closed':
                tickets = db.get_tickets_by_status('replied_closed', limit=50)
                title = "✅ Replied & Closed Tickets"
            elif filter_type == 'closed_no_reply':
                tickets = db.get_tickets_by_status('closed_no_reply', limit=50)
                title = "🔴 Closed (No Reply) Tickets"
            else:
                return
            
            text = format_ticket_list(tickets, title)
            await query.edit_message_text(
                text,
                reply_markup=get_filter_keyboard(),
                parse_mode='HTML'
            )
    
    @staticmethod
    async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin reply text"""
        if not await AdminHandlers.check_admin(update):
            return ConversationHandler.END
        
        reply_text = update.message.text
        ticket_id = context.user_data.get('reply_ticket_id')
        admin_id = update.effective_user.id
        
        if not ticket_id:
            return ConversationHandler.END
        
        # Delete admin's message for privacy
        try:
            await update.message.delete()
        except:
            pass
        
        # Save reply
        db.reply_to_ticket(ticket_id, reply_text, admin_id)
        
        # Get ticket info
        ticket = db.get_ticket(ticket_id)
        
        # Send reply to user
        try:
            user_message = f"""
📬 <b>Reply to your ticket #{ticket_id}</b>

<b>Support Team:</b>
{escape_html(reply_text)}

This ticket is now closed. Create a new ticket for any other questions.

{config.SUPPORT_MESSAGE}
"""
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=user_message,
                parse_mode='HTML'
            )
            
            # Log action
            db.log_action(admin_id, 'reply_ticket', {'ticket_id': ticket_id})
            
        except Exception as e:
            logger.error(f"Failed to send reply to user: {e}")
        
        # Confirm to admin
        await context.bot.send_message(
            chat_id=config.ADMIN_GROUP_ID,
            text=f"✅ Reply sent for ticket {ticket_id}"
        )
        
        context.user_data.pop('reply_ticket_id', None)
        return ConversationHandler.END
    
    @staticmethod
    async def update_ticket_message(context: ContextTypes.DEFAULT_TYPE, ticket_id: str):
        """Update ticket message in admin group"""
        # This would require storing message IDs - implement if needed
        pass
    
    @staticmethod
    async def cancel_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel reply"""
        if not await AdminHandlers.check_admin(update):
            return ConversationHandler.END
        
        await update.message.reply_text("❌ Reply cancelled.")
        context.user_data.pop('reply_ticket_id', None)
        return ConversationHandler.END
