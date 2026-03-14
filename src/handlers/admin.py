import logging
import pandas as pd
import io
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.models import User, Ticket, AdminAction
from src.database import db_session
from src.keyboards.admin_keyboards import *
from src.utils.helpers import format_ticket_details, export_data_to_excel
from src.config import Config

logger = logging.getLogger(__name__)

async def pending_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets (new and in progress)"""
    # Get last 300 tickets that are new or in progress
    pending = db_session.query(Ticket).filter(
        Ticket.status.in_(['new', 'in_progress'])
    ).order_by(Ticket.created_at.desc()).limit(300).all()
    
    if not pending:
        await update.message.reply_text("✅ No pending tickets!")
        return
    
    await update.message.reply_text(f"📋 Found {len(pending)} pending tickets. Sending one by one...")
    
    for ticket in pending:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        
        ticket_text = format_ticket_details(ticket, user)
        
        # Add reply button for pending tickets
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📝 Reply", callback_data=f"pending_reply_{ticket.ticket_number}")
        ]])
        
        await update.message.reply_text(
            ticket_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

async def get_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all ticket data as Excel file"""
    tickets = db_session.query(Ticket).all()
    
    if not tickets:
        await update.message.reply_text("No data available!")
        return
    
    # Prepare data for export
    data = []
    for ticket in tickets:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        data.append({
            'User Name': ticket.name,
            'Username': f"@{user.username if user and user.username else 'N/A'}",
            'User ID': ticket.user_id,
            'Phone Number': ticket.phone,
            'Email': ticket.email,
            'Category': ticket.category,
            'Question': ticket.question,
            'Status': ticket.status,
            'Admin Reply': ticket.admin_reply or 'No reply yet',
            'Replied By': ticket.admin_username or 'N/A',
            'Ticket Created': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Reply Time': ticket.replied_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.replied_at else 'N/A'
        })
    
    # Create Excel file
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tickets')
    
    output.seek(0)
    
    await update.message.reply_document(
        document=output,
        filename=f'tickets_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        caption=f"✅ Exported {len(tickets)} tickets"
    )

async def search_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for users/tickets"""
    if not context.args:
        await update.message.reply_text(
            "🔍 **Search Help**\n\n"
            "Usage: /search <search term>\n\n"
            "Examples:\n"
            "/search john (search by name)\n"
            "/search @username (search by username)\n"
            "/search TKT-20240313 (search by ticket number)\n"
            "/search 123456789 (search by user ID)",
            parse_mode='Markdown'
        )
        return
    
    search_term = ' '.join(context.args)
    
    results = []
    
    # Search by ticket number
    if search_term.startswith('TKT-'):
        ticket = db_session.query(Ticket).filter_by(ticket_number=search_term).first()
        if ticket:
            results.append(ticket)
    else:
        # Search by user ID
        if search_term.isdigit():
            user_id = int(search_term)
            tickets = db_session.query(Ticket).filter_by(user_id=user_id).all()
            results.extend(tickets)
        
        # Search by username or name
        if search_term.startswith('@'):
            username = search_term[1:]
            users = db_session.query(User).filter(User.username.ilike(f'%{username}%')).all()
            for user in users:
                user_tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).all()
                results.extend(user_tickets)
        else:
            # Search by name or email
            tickets = db_session.query(Ticket).filter(
                (Ticket.name.ilike(f'%{search_term}%')) |
                (Ticket.email.ilike(f'%{search_term}%')) |
                (Ticket.phone.ilike(f'%{search_term}%'))
            ).all()
            results.extend(tickets)
    
    if not results:
        await update.message.reply_text("❌ No results found!")
        return
    
    # Remove duplicates by ticket number
    unique_results = {}
    for ticket in results:
        unique_results[ticket.ticket_number] = ticket
    
    await update.message.reply_text(f"📊 Found {len(unique_results)} tickets:")
    
    for ticket in list(unique_results.values())[:10]:  # Limit to 10 results
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        ticket_text = format_ticket_details(ticket, user)
        await update.message.reply_text(ticket_text, parse_mode='Markdown')
    
    if len(unique_results) > 10:
        await update.message.reply_text(f"... and {len(unique_results) - 10} more results")

async def reply_to_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply to a ticket via command"""
    if not context.args:
        await update.message.reply_text("Usage: /reply TICKET_NUMBER your reply")
        return
    
    ticket_number = context.args[0]
    reply_text = ' '.join(context.args[1:])
    
    if not reply_text:
        await update.message.reply_text("Please provide your reply message!")
        return
    
    ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
    if not ticket:
        await update.message.reply_text("❌ Ticket not found!")
        return
    
    admin = update.effective_user
    
    # Update ticket
    ticket.status = 'closed'
    ticket.admin_reply = reply_text
    ticket.admin_username = admin.username or admin.full_name
    ticket.replied_at = datetime.utcnow()
    db_session.commit()
    
    # Log action
    log_action = AdminAction(
        admin_id=admin.id,
        admin_username=admin.username,
        action='reply',
        ticket_number=ticket_number,
        details=f'Replied: {reply_text[:50]}...'
    )
    db_session.add(log_action)
    db_session.commit()
    
    # Send reply to user
    try:
        user_message = (
            f"📬 **Reply to your ticket #{ticket_number}**\n\n"
            f"**Your question:**\n{ticket.question}\n\n"
            f"**Support Team Reply:**\n{reply_text}\n\n"
            f"✅ This ticket is now closed. If you have another question, please create a new ticket."
        )
        
        await context.bot.send_message(
            chat_id=ticket.user_id,
            text=user_message,
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(f"✅ Reply sent to user for ticket {ticket_number}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending reply: {str(e)}")
