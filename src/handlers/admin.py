from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from src.database import db_session
from src.models import User, Ticket, TicketReply, TicketStatus, AllowedGroup
from src.utils.helpers import format_user_info, format_ticket_info, generate_csv_report, generate_excel_report
from src.keyboards.admin_keyboards import get_ticket_admin_keyboard, get_pagination_keyboard, get_admin_main_keyboard
from src.utils.decorators import admin_group_only, super_admin_only
from src.config import Config
import logging
from datetime import datetime, timedelta
import io

logger = logging.getLogger(__name__)

@admin_group_only
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel start command"""
    await update.message.reply_text(
        "👨‍💼 **Admin Control Panel**\n\n"
        "Available commands:\n"
        "/stats - View statistics\n"
        "/pending - View pending tickets\n"
        "/search <term> - Search users/tickets\n"
        "/getdata - Download all data\n"
        "/help - Show this help",
        parse_mode='Markdown',
        reply_markup=get_admin_main_keyboard()
    )

@admin_group_only
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    # Get counts
    total_users = db_session.query(User).count()
    total_tickets = db_session.query(Ticket).count()
    open_tickets = db_session.query(Ticket).filter_by(status=TicketStatus.OPEN).count()
    in_progress = db_session.query(Ticket).filter_by(status=TicketStatus.IN_PROGRESS).count()
    closed_tickets = db_session.query(Ticket).filter_by(status=TicketStatus.CLOSED).count()
    
    # Today's tickets
    today = datetime.utcnow().date()
    today_tickets = db_session.query(Ticket).filter(
        Ticket.created_at >= today
    ).count()
    
    # Response time stats (average)
    # This is simplified - you might want to calculate properly
    stats_text = (
        f"📊 **Support Statistics**\n\n"
        f"**Users:**\n"
        f"Total Users: {total_users}\n\n"
        f"**Tickets:**\n"
        f"Total: {total_tickets}\n"
        f"🟢 Open: {open_tickets}\n"
        f"🟡 In Progress: {in_progress}\n"
        f"🔴 Closed: {closed_tickets}\n"
        f"📅 Today: {today_tickets}\n\n"
        f"⏱ Response Time: Within 24 hours"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

@admin_group_only
async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets"""
    page = 1
    await show_pending_tickets(update, context, page)

async def show_pending_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int, search_term: str = None):
    """Show pending tickets with pagination"""
    query = db_session.query(Ticket).filter(
        Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS])
    ).order_by(Ticket.created_at.desc())
    
    total_tickets = query.count()
    total_pages = (total_tickets + Config.TICKETS_PER_PAGE - 1) // Config.TICKETS_PER_PAGE
    
    if total_tickets == 0:
        await update.message.reply_text("No pending tickets found.")
        return
    
    # Paginate
    tickets = query.offset((page - 1) * Config.TICKETS_PER_PAGE).limit(Config.TICKETS_PER_PAGE).all()
    
    text = f"⏳ **Pending Tickets (Page {page}/{total_pages})**\n\n"
    
    for ticket in tickets:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        status_emoji = '🟡' if ticket.status == TicketStatus.IN_PROGRESS else '🟢'
        text += f"{status_emoji} #{ticket.ticket_number}\n"
        text += f"User: {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
        text += f"Category: {ticket.category}\n"
        text += f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    keyboard = get_pagination_keyboard(page, total_pages, "pending", search_term)
    
    if isinstance(update, Update):
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

@admin_group_only
async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search users or tickets"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /search <term>\n"
            "Search by: username, user ID, email, or ticket number"
        )
        return
    
    search_term = ' '.join(context.args).strip()
    
    # Search users
    users = db_session.query(User).filter(
        (User.username.ilike(f"%{search_term}%")) |
        (User.email.ilike(f"%{search_term}%")) |
        (User.name.ilike(f"%{search_term}%")) |
        (User.user_id == (int(search_term) if search_term.isdigit() else 0))
    ).all()
    
    # Search tickets
    tickets = db_session.query(Ticket).filter(
        Ticket.ticket_number.ilike(f"%{search_term}%")
    ).all()
    
    if not users and not tickets:
        await update.message.reply_text("No results found.")
        return
    
    text = f"🔍 **Search Results for '{search_term}'**\n\n"
    
    if users:
        text += "**Users Found:**\n"
        for user in users[:5]:  # Limit to 5 users
            text += f"• {user.name or 'N/A'} (@{user.username or 'N/A'}) - ID: `{user.user_id}`\n"
        text += "\n"
    
    if tickets:
        text += "**Tickets Found:**\n"
        for ticket in tickets[:5]:  # Limit to 5 tickets
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            text += f"• #{ticket.ticket_number} - {ticket.category} - {user.name or 'N/A'}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

@admin_group_only
async def admin_getdata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download all tickets data"""
    await update.message.reply_text("📥 Generating data export, please wait...")
    
    # Get all tickets with user info
    tickets = db_session.query(Ticket).order_by(Ticket.created_at.desc()).all()
    
    data = []
    for ticket in tickets:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        last_reply = ticket.replies[-1] if ticket.replies else None
        
        data.append({
            'Ticket Number': ticket.ticket_number,
            'User Name': user.name if user else 'N/A',
            'Username': user.username if user else 'N/A',
            'User ID': ticket.user_id,
            'Email': user.email if user else 'N/A',
            'Phone': user.phone if user else 'N/A',
            'Category': ticket.category,
            'Question': ticket.question,
            'Status': ticket.status.value,
            'Admin Answer': last_reply.message if last_reply else '',
            'Admin Username': last_reply.admin_username if last_reply else '',
            'Created At': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Closed At': ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.status == TicketStatus.CLOSED else ''
        })
    
    # Generate CSV
    csv_file = await generate_csv_report(data)
    
    await update.message.reply_document(
        document=csv_file,
        filename=f"tickets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        caption="✅ Tickets data export"
    )

@admin_group_only
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("admin_reply_"):
        ticket_number = data.replace("admin_reply_", "")
        context.user_data['replying_to_ticket'] = ticket_number
        await query.edit_message_text(
            f"Please type your reply for ticket #{ticket_number}:"
        )
        return
    
    elif data.startswith("progress_"):
        ticket_number = data.replace("progress_", "")
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if ticket:
            ticket.status = TicketStatus.IN_PROGRESS
            db_session.commit()
            
            await query.edit_message_text(
                f"✅ Ticket #{ticket_number} marked as in progress by @{update.effective_user.username}"
            )
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=ticket.user_id,
                    text=f"🟡 Your ticket #{ticket_number} is now being reviewed by our support team."
                )
            except:
                pass
    
    elif data.startswith("close_"):
        ticket_number = data.replace("close_", "")
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if ticket:
            ticket.status = TicketStatus.CLOSED
            db_session.commit()
            
            await query.edit_message_text(
                f"✅ Ticket #{ticket_number} closed by @{update.effective_user.username}"
            )
            
            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=ticket.user_id,
                    text=f"🔴 Your ticket #{ticket_number} has been closed. If you need further assistance, please create a new ticket."
                )
            except:
                pass
    
    elif data.startswith("view_user_"):
        user_id = int(data.replace("view_user_", ""))
        user = db_session.query(User).filter_by(user_id=user_id).first()
        if user:
            tickets = db_session.query(Ticket).filter_by(user_id=user_id).order_by(Ticket.created_at.desc()).all()
            text = format_user_info(user, tickets)
            await query.edit_message_text(text, parse_mode='Markdown')
    
    elif data.startswith("pending_page_"):
        parts = data.split('_')
        page = int(parts[2])
        search_term = parts[3] if len(parts) > 3 else None
        await show_pending_tickets(update, context, page, search_term)
    
    elif data == "admin_back":
        await query.edit_message_text(
            "Admin Menu:",
            reply_markup=get_admin_main_keyboard()
        )
    
    elif data == "admin_stats":
        await admin_stats(update, context)
    
    elif data == "admin_pending":
        await admin_pending(update, context)
    
    elif data == "admin_search":
        await query.edit_message_text("Please use /search command with your search term.")

@admin_group_only
async def admin_handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reply to ticket"""
    ticket_number = context.user_data.get('replying_to_ticket')
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
    ticket.status = TicketStatus.CLOSED  # Close after admin reply
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
        await update.message.reply_text(f"Reply saved but failed to send to user. Error: {e}")
    
    # Confirm in admin group
    await context.bot.send_message(
        chat_id=Config.ADMIN_GROUP_ID,
        text=f"✅ Admin @{update.effective_user.username} replied to ticket #{ticket_number}\n\nReply: {reply_text}"
    )
    
    context.user_data.pop('replying_to_ticket', None)
