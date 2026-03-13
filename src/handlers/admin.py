from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import db_session
from src.models import User, Ticket, TicketReply
from src.utils.helpers import format_user_info
from src.config import Config
import logging
from datetime import datetime
import pandas as pd
from io import BytesIO
import re

logger = logging.getLogger(__name__)

# Simple check for admin group
def is_admin_group(chat_id: int) -> bool:
    return chat_id == Config.ADMIN_GROUP_ID

# Helper function to escape markdown characters
def escape_markdown(text):
    """Escape markdown special characters"""
    if not text:
        return ""
    # Escape special characters: _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

# Helper function to reply properly based on context
async def reply_or_edit(update: Update, text: str, reply_markup=None, parse_mode='Markdown'):
    """Helper function to handle both message and callback contexts"""
    try:
        if update.callback_query:
            if reply_markup:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            else:
                await update.callback_query.edit_message_text(text, parse_mode=parse_mode)
        elif update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Error in reply_or_edit: {e}")
        # Fallback without markdown
        if update.callback_query:
            await update.callback_query.edit_message_text(text.replace('*', '').replace('_', ''))
        elif update.message:
            await update.message.reply_text(text.replace('*', '').replace('_', ''))

async def admin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all admin commands"""
    # Check if this is the admin group
    if not is_admin_group(update.effective_chat.id):
        return
    
    command = update.message.text.split()[0].lower()
    logger.info(f"Admin command received: {command} in chat {update.effective_chat.id}")
    
    if command == "/admin":
        await show_admin_panel(update, context)
    elif command == "/stats":
        await show_stats(update, context)
    elif command == "/pending":
        await show_pending(update, context)
    elif command == "/search":
        await search_tickets(update, context)
    elif command == "/getdata":
        await export_data(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("⏳ Pending Tickets", callback_data="admin_pending")],
        [InlineKeyboardButton("🔍 Search", callback_data="admin_search")],
        [InlineKeyboardButton("📥 Download Data", callback_data="admin_download")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "👨‍💼 **Admin Control Panel**\n\n"
        "Select an option below or use commands:\n"
        "/stats - View statistics\n"
        "/pending - View pending tickets\n"
        "/search <term> - Search\n"
        "/getdata - Download all data"
    )
    
    await reply_or_edit(update, text, reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    try:
        total_users = db_session.query(User).count()
        total_tickets = db_session.query(Ticket).count()
        open_tickets = db_session.query(Ticket).filter_by(status='open').count()
        in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
        closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
        
        today = datetime.utcnow().date()
        today_tickets = db_session.query(Ticket).filter(
            Ticket.created_at >= today
        ).count()
        
        text = (
            f"📊 **Support Statistics**\n\n"
            f"**Users:** {total_users}\n\n"
            f"**Tickets:**\n"
            f"Total: {total_tickets}\n"
            f"🟢 Open: {open_tickets}\n"
            f"🟡 In Progress: {in_progress}\n"
            f"🔴 Closed: {closed_tickets}\n"
            f"📅 Today: {today_tickets}"
        )
        
        await reply_or_edit(update, text)
    except Exception as e:
        logger.error(f"Error in show_stats: {e}")
        await reply_or_edit(update, f"Error: {str(e)}")

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets - FIXED Markdown parsing"""
    try:
        tickets = db_session.query(Ticket).filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).order_by(Ticket.created_at.desc()).all()
        
        if not tickets:
            await reply_or_edit(update, "No pending tickets found.")
            return
        
        # If this is a callback, delete the original message
        if update.callback_query:
            await update.callback_query.message.delete()
        
        # Send each ticket as a separate message
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            status_emoji = '🟡' if ticket.status == 'in_progress' else '🟢'
            
            # Escape special characters in username and name
            username = escape_markdown(user.username) if user and user.username else 'N/A'
            name = escape_markdown(user.name) if user and user.name else 'N/A'
            question_preview = escape_markdown(ticket.question[:100]) if ticket.question else 'N/A'
            
            text = (
                f"{status_emoji} *Ticket #{ticket.ticket_number}*\n"
                f"User: {name} (@{username})\n"
                f"Category: {ticket.category}\n"
                f"Status: {ticket.status}\n"
                f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"Question: {question_preview}...\n"
            )
            
            keyboard = [[
                InlineKeyboardButton(
                    f"📝 Reply to #{ticket.ticket_number}", 
                    callback_data=f"reply_{ticket.ticket_number}"
                ),
                InlineKeyboardButton(
                    "🟡 In Progress",
                    callback_data=f"progress_{ticket.ticket_number}"
                )
            ]]
            
            # Send to the appropriate chat
            if update.callback_query:
                await update.effective_chat.send_message(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
    except Exception as e:
        logger.error(f"Error in show_pending: {e}")
        await reply_or_edit(update, f"Error: {str(e)}")

async def search_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search tickets - FIXED VERSION"""
    if not context.args:
        help_text = (
            "🔍 **Search Help**\n\n"
            "Usage: /search <search term>\n\n"
            "Examples:\n"
            "/search john \(search by name\)\n"
            "/search @username \(search by username\)\n"
            "/search TKT\-20240313 \(search by ticket number\)\n"
            "/search 123456789 \(search by user ID\)"
        )
        await reply_or_edit(update, help_text)
        return
    
    search_term = ' '.join(context.args).strip()
    logger.info(f"Searching for: {search_term}")
    
    try:
        # Search by ticket number
        ticket = db_session.query(Ticket).filter_by(ticket_number=search_term).first()
        if ticket:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            username = escape_markdown(user.username) if user and user.username else 'N/A'
            name = escape_markdown(user.name) if user and user.name else 'N/A'
            question = escape_markdown(ticket.question) if ticket.question else 'N/A'
            
            text = (
                f"🎫 **Ticket Found**\n\n"
                f"**Ticket #:** {ticket.ticket_number}\n"
                f"**User:** {name} (@{username})\n"
                f"**User ID:** `{user.user_id if user else 'N/A'}`\n"
                f"**Category:** {ticket.category}\n"
                f"**Status:** {ticket.status}\n"
                f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"**Question:** {question}"
            )
            await reply_or_edit(update, text)
            return
        
        # Search by username
        clean_username = search_term.replace('@', '')
        user = db_session.query(User).filter(
            User.username.ilike(f"%{clean_username}%")
        ).first()
        
        if user:
            user_tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).all()
            text = format_user_info(user, user_tickets)
            # format_user_info already handles escaping? If not, we may need to escape here
            await reply_or_edit(update, text)
            return
        
        # Search by user ID
        if search_term.isdigit():
            user = db_session.query(User).filter_by(user_id=int(search_term)).first()
            if user:
                user_tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).all()
                text = format_user_info(user, user_tickets)
                await reply_or_edit(update, text)
                return
        
        await reply_or_edit(update, "No results found.")
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await reply_or_edit(update, f"Error searching: {str(e)}")

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all data"""
    try:
        await reply_or_edit(update, "📥 Generating export...")
        
        tickets = db_session.query(Ticket).all()
        data = []
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            last_reply = ticket.replies[-1] if ticket.replies else None
            
            data.append({
                'Ticket #': ticket.ticket_number,
                'User Name': user.name if user else 'N/A',
                'Username': user.username if user else 'N/A',
                'User ID': ticket.user_id,
                'Email': user.email if user else 'N/A',
                'Phone': user.phone if user else 'N/A',
                'Category': ticket.category,
                'Question': ticket.question,
                'Status': ticket.status,
                'Admin Reply': last_reply.message if last_reply else '',
                'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M'),
                'Updated': ticket.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Send document
        filename = f"tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if update.callback_query:
            await update.callback_query.message.reply_document(
                document=output,
                filename=filename,
                caption="✅ Tickets export completed"
            )
        else:
            await update.message.reply_document(
                document=output,
                filename=filename,
                caption="✅ Tickets export completed"
            )
    except Exception as e:
        logger.error(f"Error in export_data: {e}")
        await reply_or_edit(update, f"Error: {str(e)}")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin_group(query.message.chat.id):
        return
    
    data = query.data
    logger.info(f"Admin callback: {data}")
    
    try:
        if data == "admin_stats":
            await show_stats(update, context)
            await query.message.delete()
        
        elif data == "admin_pending":
            await show_pending(update, context)
        
        elif data == "admin_search":
            help_text = (
                "🔍 **Search Help**\n\n"
                "Use /search command with your search term.\n\n"
                "Examples:\n"
                "/search TKT\-20240313\n"
                "/search @username\n"
                "/search 123456789"
            )
            await query.edit_message_text(help_text, parse_mode='Markdown')
        
        elif data == "admin_download":
            await export_data(update, context)
        
        elif data.startswith("reply_"):
            ticket_number = data.replace("reply_", "")
            context.user_data['replying_to'] = ticket_number
            await query.edit_message_text(
                f"Please type your reply for ticket #{ticket_number}:"
            )
        
        elif data.startswith("progress_"):
            ticket_number = data.replace("progress_", "")
            ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
            if ticket:
                ticket.status = 'in_progress'
                db_session.commit()
                await query.edit_message_text(
                    f"✅ Ticket #{ticket_number} marked as in progress by @{escape_markdown(update.effective_user.username or 'Admin')}"
                )
                
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=ticket.user_id,
                        text=f"🟡 Your ticket #{ticket_number} is now being reviewed by our support team."
                    )
                except:
                    pass
        
        elif data.startswith("view_"):
            ticket_number = data.replace("view_", "")
            ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
            if ticket:
                user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
                username = escape_markdown(user.username) if user and user.username else 'N/A'
                name = escape_markdown(user.name) if user and user.name else 'N/A'
                email = escape_markdown(user.email) if user and user.email else 'N/A'
                phone = escape_markdown(user.phone) if user and user.phone else 'N/A'
                question = escape_markdown(ticket.question) if ticket.question else 'N/A'
                
                text = (
                    f"👤 **User Details**\n"
                    f"Name: {name}\n"
                    f"Username: @{username}\n"
                    f"User ID: `{user.user_id if user else 'N/A'}`\n"
                    f"Email: {email}\n"
                    f"Phone: {phone}\n\n"
                    f"🎫 **Ticket #{ticket.ticket_number}**\n"
                    f"Category: {ticket.category}\n"
                    f"Status: {ticket.status}\n"
                    f"Question: {question}"
                )
                await query.edit_message_text(text, parse_mode='Markdown')
        
        elif data.startswith("cancel_"):
            await query.delete_message()
    
    except Exception as e:
        logger.error(f"Error in admin_callback_handler: {e}")
        await query.edit_message_text(f"Error: {str(e)}")

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin replies to tickets"""
    if not is_admin_group(update.effective_chat.id):
        return
    
    ticket_number = context.user_data.get('replying_to')
    if not ticket_number:
        return
    
    reply_text = update.message.text
    logger.info(f"Admin reply to ticket {ticket_number}: {reply_text[:50]}...")
    
    try:
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        
        if not ticket:
            await update.message.reply_text("Ticket not found.")
            return
        
        # Save reply
        reply = TicketReply(
            ticket_id=ticket.id,
            admin_id=update.effective_user.id,
            admin_username=update.effective_user.username or "Admin",
            message=reply_text
        )
        
        db_session.add(reply)
        ticket.status = 'closed'
        ticket.updated_at = datetime.utcnow()
        db_session.commit()
        
        # Send to user
        try:
            user_text = (
                f"📨 **Reply to your ticket #{ticket_number}**\n\n"
                f"Support Team: {reply_text}\n\n"
                f"This ticket is now closed. If you have more questions, please create a new ticket."
            )
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=user_text,
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(f"✅ Reply sent to user. Ticket #{ticket_number} closed.")
        except Exception as e:
            logger.error(f"Failed to send reply to user: {e}")
            await update.message.reply_text(f"✅ Reply saved but couldn't notify user.")
        
        context.user_data.pop('replying_to', None)
        
    except Exception as e:
        logger.error(f"Error in admin_reply_handler: {e}")
        await update.message.reply_text(f"Error sending reply: {str(e)}")

# Function to send new ticket to admin group - WITH WORKING REPLY BUTTON
async def send_ticket_to_admin_group(context, ticket, user, question):
    """Send new ticket notification to admin group"""
    try:
        # Escape special characters
        username = escape_markdown(user.username) if user and user.username else 'N/A'
        name = escape_markdown(user.name) if user and user.name else 'N/A'
        email = escape_markdown(user.email) if user and user.email else 'N/A'
        phone = escape_markdown(user.phone) if user and user.phone else 'N/A'
        question_text = escape_markdown(question) if question else 'N/A'
        
        admin_text = (
            f"🆕 **New Support Ticket**\n\n"
            f"Ticket: #{ticket.ticket_number}\n"
            f"User: {name} (@{username})\n"
            f"User ID: `{user.user_id if user else 'N/A'}`\n"
            f"Category: {ticket.category}\n"
            f"Email: {email}\n"
            f"Phone: {phone}\n\n"
            f"**Question:**\n{question_text}\n\n"
            f"Time: {ticket.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        # Using the SAME reply button format that works in /pending
        keyboard = [[
            InlineKeyboardButton(
                f"📝 Reply to #{ticket.ticket_number}", 
                callback_data=f"reply_{ticket.ticket_number}"
            ),
            InlineKeyboardButton(
                "🟡 In Progress", 
                callback_data=f"progress_{ticket.ticket_number}"
            ),
            InlineKeyboardButton(
                "👤 View User", 
                callback_data=f"view_{ticket.ticket_number}"
            ),
            InlineKeyboardButton(
                "❌ Cancel", 
                callback_data=f"cancel_{ticket.ticket_number}"
            )
        ]]
        
        await context.bot.send_message(
            chat_id=Config.ADMIN_GROUP_ID,
            text=admin_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send to admin group: {e}")
        # Fallback without markdown
        try:
            admin_text_plain = (
                f"🆕 New Support Ticket\n\n"
                f"Ticket: #{ticket.ticket_number}\n"
                f"User: {user.name if user else 'N/A'} (@{user.username if user else 'N/A'})\n"
                f"User ID: {user.user_id if user else 'N/A'}\n"
                f"Category: {ticket.category}\n"
                f"Email: {user.email if user else 'N/A'}\n"
                f"Phone: {user.phone if user else 'N/A'}\n\n"
                f"Question:\n{question}\n\n"
                f"Time: {ticket.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
            )
            await context.bot.send_message(
                chat_id=Config.ADMIN_GROUP_ID,
                text=admin_text_plain,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            pass
