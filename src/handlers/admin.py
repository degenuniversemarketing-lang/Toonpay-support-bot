import logging
import pandas as pd
import io
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.models import User, Ticket, AdminAction
from src.database import db_session
from src.keyboards.admin_keyboards import get_admin_ticket_keyboard, get_pending_ticket_keyboard
from src.utils.helpers import format_ticket_details, log_admin_action
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
            InlineKeyboardButton("📝 Reply to this ticket", callback_data=f"pending_reply_{ticket.ticket_number}")
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
        
        # Search by username
        if search_term.startswith('@'):
            username = search_term[1:]
            users = db_session.query(User).filter(User.username.ilike(f'%{username}%')).all()
            for user in users:
                user_tickets = db_session.query(Ticket).filter_by(user_id=user.user_id).all()
                results.extend(user_tickets)
        else:
            # Search by name, email, or phone
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
    log_admin_action(
        admin.id,
        admin.username,
        'reply',
        ticket_number,
        f'Replied: {reply_text[:50]}...'
    )
    
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

async def handle_admin_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reply button click from new ticket notification"""
    query = update.callback_query
    await query.answer()
    
    ticket_number = query.data.replace('reply_', '')
    context.user_data['replying_to'] = ticket_number
    context.user_data['reply_source'] = 'new_ticket'
    
    # Delete the original message with buttons
    await query.delete_message()
    
    # Send a new message asking for reply
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📝 Please type your reply for ticket `{ticket_number}`\n\n"
             f"Your reply will be sent to the user and the ticket will be closed.\n"
             f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )

async def handle_admin_in_progress_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin in progress button click"""
    query = update.callback_query
    await query.answer()
    
    ticket_number = query.data.replace('progress_', '')
    admin = query.from_user
    
    ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
    if ticket:
        ticket.status = 'in_progress'
        db_session.commit()
        
        # Log action
        log_admin_action(
            admin.id,
            admin.username,
            'mark_in_progress',
            ticket_number
        )
        
        # Update the message to show it's in progress
        await query.edit_message_text(
            text=query.message.text + f"\n\n⏳ **Marked as in progress by @{admin.username}**",
            parse_mode='Markdown'
        )
        
        # Send confirmation
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ Ticket {ticket_number} marked as in progress by @{admin.username}"
        )

async def handle_admin_view_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin view button click"""
    query = update.callback_query
    await query.answer()
    
    ticket_number = query.data.replace('view_', '')
    
    ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
    if ticket:
        user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
        ticket_text = format_ticket_details(ticket, user)
        
        # Send as new message instead of editing
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=ticket_text,
            parse_mode='Markdown'
        )

async def handle_admin_cancel_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin cancel button click"""
    query = update.callback_query
    await query.answer()
    
    ticket_number = query.data.replace('cancel_', '')
    admin = query.from_user
    
    ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
    if ticket:
        ticket.status = 'closed'
        db_session.commit()
        
        # Log action
        log_admin_action(
            admin.id,
            admin.username,
            'cancel_ticket',
            ticket_number
        )
        
        # Update the message
        await query.edit_message_text(
            text=query.message.text + f"\n\n❌ **Cancelled by @{admin.username}**",
            parse_mode='Markdown'
        )
        
        # Send confirmation
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Ticket {ticket_number} has been cancelled by @{admin.username}"
        )

async def handle_pending_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reply button from pending tickets list"""
    query = update.callback_query
    await query.answer()
    
    ticket_number = query.data.replace('pending_reply_', '')
    context.user_data['replying_to'] = ticket_number
    context.user_data['reply_source'] = 'pending'
    
    # Delete the original message
    await query.delete_message()
    
    # Send a new message asking for reply
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📝 Please type your reply for ticket `{ticket_number}`\n\n"
             f"Your reply will be sent to the user and the ticket will be closed.\n"
             f"Type /cancel to cancel.",
        parse_mode='Markdown'
    )

async def handle_admin_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reply message after clicking any reply button"""
    if 'replying_to' not in context.user_data:
        return
    
    ticket_number = context.user_data['replying_to']
    reply_text = update.message.text
    admin = update.effective_user
    
    # Check if user wants to cancel
    if reply_text.lower() == '/cancel':
        await update.message.reply_text("❌ Reply cancelled.")
        del context.user_data['replying_to']
        if 'reply_source' in context.user_data:
            del context.user_data['reply_source']
        return
    
    ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
    if not ticket:
        await update.message.reply_text("❌ Ticket not found!")
        del context.user_data['replying_to']
        if 'reply_source' in context.user_data:
            del context.user_data['reply_source']
        return
    
    # Update ticket
    ticket.status = 'closed'
    ticket.admin_reply = reply_text
    ticket.admin_username = admin.username or admin.full_name
    ticket.replied_at = datetime.utcnow()
    db_session.commit()
    
    # Log action
    log_admin_action(
        admin.id,
        admin.username,
        'reply',
        ticket_number,
        f'Replied: {reply_text[:50]}...'
    )
    
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
        
        # Also notify the admin
        await update.message.reply_text(
            f"✅ Reply sent to user for ticket {ticket_number}\n\n"
            f"**Your reply:**\n{reply_text}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending reply: {str(e)}")
    
    # Clear user data
    del context.user_data['replying_to']
    if 'reply_source' in context.user_data:
        del context.user_data['reply_source']
