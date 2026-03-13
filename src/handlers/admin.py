from telegram import Update
from telegram.ext import ContextTypes
from src.database import db_session
from src.models import User, Ticket, TicketReply
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
    if not update or not update.effective_chat:
        return
    
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
    """Show admin panel without buttons"""
    await update.message.reply_text(
        "👨‍💼 **Admin Control Panel**\n\n"
        "Available commands:\n"
        "/stats - View statistics\n"
        "/pending - View pending tickets\n"
        "/search <term> - Search users/tickets\n"
        "/getdata - Download all data",
        parse_mode='Markdown'
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
            "📊 **Support Statistics**\n\n"
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
        await update.message.reply_text(f"Error getting statistics: {str(e)}")

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets"""
    try:
        tickets = db_session.query(Ticket).filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).order_by(Ticket.created_at.desc()).limit(10).all()
        
        if not tickets:
            await update.message.reply_text("No pending tickets found.")
            return
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            status_emoji = '🟡' if ticket.status == 'in_progress' else '🟢'
            
            text = (
                f"{status_emoji} **Ticket #{ticket.ticket_number}**\n"
                f"**User:** {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
                f"**Category:** {ticket.category}\n"
                f"**Status:** {ticket.status}\n"
                f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"**Question:** {ticket.question[:100]}...\n"
                f"**To reply use:** /reply {ticket.ticket_number} your message"
            )
            
            await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in show_pending: {e}")
        await update.message.reply_text(f"Error showing pending tickets: {str(e)}")

async def search_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search users or tickets"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /search <search term>\n"
            "Examples:\n"
            "/search john\n"
            "/search @username\n"
            "/search TKT-20240313\n"
            "/search 123456789"
        )
        return
    
    search_term = ' '.join(context.args).strip()
    logger.info(f"Searching for: {search_term}")
    
    try:
        results_found = False
        
        # Search by ticket number
        ticket = db_session.query(Ticket).filter_by(ticket_number=search_term).first()
        if ticket:
            results_found = True
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            
            # Get admin reply if exists
            admin_reply = db_session.query(TicketReply).filter_by(ticket_id=ticket.id).first()
            admin_answer = admin_reply.message if admin_reply else "No reply yet"
            admin_by = f"by @{admin_reply.admin_username}" if admin_reply else ""
            
            text = (
                f"🎫 **Ticket Details**\n\n"
                f"**Ticket Number:** `{ticket.ticket_number}`\n"
                f"**User:** {user.name or 'N/A'}\n"
                f"**Username:** @{user.username or 'N/A'}\n"
                f"**User ID:** `{user.user_id}`\n"
                f"**Category:** {ticket.category}\n"
                f"**Status:** {ticket.status.upper()} {admin_by}\n"
                f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"**User Question:**\n{ticket.question}\n\n"
                f"**Admin Answer:**\n{admin_answer}"
            )
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        # Search by username
        username = search_term.replace('@', '')
        user = db_session.query(User).filter_by(username=username).first()
        
        if not user:
            # Search by user ID if it's a number
            if search_term.isdigit():
                user = db_session.query(User).filter_by(user_id=int(search_term)).first()
        
        if not user:
            # Search by name or email (partial match)
            user = db_session.query(User).filter(
                (User.name.ilike(f"%{search_term}%")) |
                (User.email.ilike(f"%{search_term}%"))
            ).first()
        
        if user:
            results_found = True
            tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).order_by(Ticket.created_at.desc()).all()
            
            text = (
                f"👤 **User Details**\n\n"
                f"**Name:** {user.name or 'N/A'}\n"
                f"**Username:** @{user.username or 'N/A'}\n"
                f"**User ID:** `{user.user_id}`\n"
                f"**Email:** {user.email or 'N/A'}\n"
                f"**Phone:** {user.phone or 'N/A'}\n"
                f"**Joined:** {user.created_at.strftime('%Y-%m-%d')}\n\n"
                f"**📊 Ticket History ({len(tickets)} total)**\n\n"
            )
            
            for t in tickets[:5]:  # Show last 5 tickets
                status_emoji = {
                    'open': '🟢',
                    'in_progress': '🟡',
                    'closed': '🔴'
                }.get(t.status, '⚪')
                
                # Get admin reply for this ticket
                reply = db_session.query(TicketReply).filter_by(ticket_id=t.id).first()
                admin_info = f" (replied by @{reply.admin_username})" if reply else ""
                
                text += (
                    f"{status_emoji} **#{t.ticket_number}**\n"
                    f"   Category: {t.category}\n"
                    f"   Status: {t.status}{admin_info}\n"
                    f"   Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"   Question: {t.question[:50]}...\n\n"
                )
            
            await update.message.reply_text(text, parse_mode='Markdown')
        
        if not results_found:
            await update.message.reply_text(f"❌ No results found for '{search_term}'")
            
    except Exception as e:
        logger.error(f"Error in search_tickets: {e}")
        await update.message.reply_text(f"Error searching: {str(e)}")

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all data"""
    try:
        await update.message.reply_text("📥 Generating export, please wait...")
        
        tickets = db_session.query(Ticket).order_by(Ticket.created_at.desc()).all()
        data = []
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            reply = db_session.query(TicketReply).filter_by(ticket_id=ticket.id).first()
            
            data.append({
                'Ticket Number': ticket.ticket_number,
                'User Name': user.name if user else 'N/A',
                'Username': user.username if user else 'N/A',
                'User ID': ticket.user_id,
                'Email': user.email if user else 'N/A',
                'Phone': user.phone if user else 'N/A',
                'Category': ticket.category,
                'Status': ticket.status,
                'Question': ticket.question,
                'Admin Answer': reply.message if reply else '',
                'Admin Username': reply.admin_username if reply else '',
                'Created At': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Closed At': ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.status == 'closed' else ''
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        await update.message.reply_document(
            document=output,
            filename=f"tickets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            caption="✅ Tickets data export"
        )
    except Exception as e:
        logger.error(f"Error in export_data: {e}")
        await update.message.reply_text(f"Error generating export: {str(e)}")

# Remove callback handler since we're not using buttons
