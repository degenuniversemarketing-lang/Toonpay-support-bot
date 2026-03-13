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

logger = logging.getLogger(__name__)

# Simple check for admin group
def is_admin_group(chat_id: int) -> bool:
    return chat_id == Config.ADMIN_GROUP_ID

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
    
    await update.message.reply_text(
        "👨‍💼 **Admin Control Panel**\n\n"
        "Select an option below or use commands:\n"
        "/stats - View statistics\n"
        "/pending - View pending tickets\n"
        "/search <term> - Search\n"
        "/getdata - Download all data",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

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
        
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in show_stats: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets"""
    try:
        tickets = db_session.query(Ticket).filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).order_by(Ticket.created_at.desc()).limit(5).all()
        
        if not tickets:
            await update.message.reply_text("No pending tickets found.")
            return
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            status_emoji = '🟡' if ticket.status == 'in_progress' else '🟢'
            
            text = (
                f"{status_emoji} **Ticket #{ticket.ticket_number}**\n"
                f"User: {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
                f"Category: {ticket.category}\n"
                f"Status: {ticket.status}\n"
                f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"Question: {ticket.question[:100]}...\n"
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
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in show_pending: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

async def search_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search tickets"""
    if not context.args:
        await update.message.reply_text("Usage: /search <ticket_number or username>")
        return
    
    search_term = ' '.join(context.args)
    
    # Search by ticket number
    ticket = db_session.query(Ticket).filter_by(ticket_number=search_term).first()
    if ticket:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        text = (
            f"🎫 **Ticket #{ticket.ticket_number}**\n"
            f"User: {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
            f"Category: {ticket.category}\n"
            f"Status: {ticket.status}\n"
            f"Question: {ticket.question}\n"
        )
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    # Search by username
    user = db_session.query(User).filter_by(username=search_term.replace('@', '')).first()
    if user:
        user_tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).all()
        text = format_user_info(user, user_tickets)
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    await update.message.reply_text("No results found.")

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all data"""
    try:
        await update.message.reply_text("📥 Generating export...")
        
        tickets = db_session.query(Ticket).all()
        data = []
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            data.append({
                'Ticket #': ticket.ticket_number,
                'User': user.name if user else 'N/A',
                'Username': user.username if user else 'N/A',
                'User ID': ticket.user_id,
                'Email': user.email if user else 'N/A',
                'Phone': user.phone if user else 'N/A',
                'Category': ticket.category,
                'Question': ticket.question,
                'Status': ticket.status,
                'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        await update.message.reply_document(
            document=output,
            filename=f"tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
    except Exception as e:
        logger.error(f"Error in export_data: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin_group(query.message.chat.id):
        return
    
    data = query.data
    logger.info(f"Admin callback: {data}")
    
    if data == "admin_stats":
        await show_stats(update, context)
        await query.message.delete()
    
    elif data == "admin_pending":
        await show_pending(update, context)
        await query.message.delete()
    
    elif data == "admin_search":
        await query.edit_message_text("Use /search command with your search term.")
    
    elif data == "admin_download":
        await export_data(update, context)
        await query.message.delete()
    
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
                f"✅ Ticket #{ticket_number} marked as in progress by @{update.effective_user.username}"
            )

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin replies to tickets"""
    if not is_admin_group(update.effective_chat.id):
        return
    
    ticket_number = context.user_data.get('replying_to')
    if not ticket_number:
        return
    
    reply_text = update.message.text
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
    db_session.commit()
    
    # Send to user
    try:
        await context.bot.send_message(
            chat_id=ticket.user_id,
            text=f"📨 **Reply to #{ticket_number}**\n\nSupport: {reply_text}\n\nTicket closed.",
            parse_mode='Markdown'
        )
        await update.message.reply_text(f"✅ Reply sent. Ticket #{ticket_number} closed.")
    except:
        await update.message.reply_text(f"✅ Reply saved but couldn't notify user.")
    
    context.user_data.pop('replying_to', None)
