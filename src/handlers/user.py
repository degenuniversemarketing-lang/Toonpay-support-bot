from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters
)
from src.database import db_session
from src.models import User, Ticket, TicketReply
from src.utils.helpers import generate_ticket_number, format_user_info, format_ticket_info
from src.keyboards.user_keyboards import get_start_keyboard, get_category_keyboard, get_ticket_action_keyboard
from src.utils.decorators import private_chat_only
import logging

# States
SELECTING_CATEGORY, ENTERING_NAME, ENTERING_EMAIL, ENTERING_PHONE, ENTERING_QUESTION, ENTERING_REPLY = range(6)

logger = logging.getLogger(__name__)

@private_chat_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command in private chat"""
    user = update.effective_user
    
    # Get or create user
    db_user = db_session.query(User).filter_by(user_id=user.id).first()
    if not db_user:
        db_user = User(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        db_session.add(db_user)
        db_session.commit()
    
    # Check if this is from support button
    args = context.args
    if args and args[0] == "support":
        context.user_data['from_group'] = True
    
    welcome_text = (
        f"👋 Welcome to ToonPay Support, {user.first_name}!\n\n"
        "How can we help you today? Please select an option below:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=get_start_keyboard())
    return ConversationHandler.END

@private_chat_only
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "new_ticket":
        await query.edit_message_text(
            "Please select the category of your issue:",
            reply_markup=get_category_keyboard()
        )
        return SELECTING_CATEGORY
    
    elif data == "my_tickets":
        user_id = update.effective_user.id
        tickets = db_session.query(Ticket).filter_by(user_id=user_id).order_by(Ticket.created_at.desc()).limit(10).all()
        
        if not tickets:
            await query.edit_message_text(
                "You haven't created any tickets yet.",
                reply_markup=get_start_keyboard()
            )
            return
        
        text = "📋 **Your Recent Tickets:**\n\n"
        keyboard = []
        
        for ticket in tickets:
            # FIXED: Using string values instead of TicketStatus enum
            status_emoji = {
                'open': '🟢',
                'in_progress': '🟡',
                'closed': '🔴',
                'pending': '⏳'
            }.get(ticket.status, '⚪')
            
            text += f"{status_emoji} Ticket #{ticket.ticket_number}\n"
            text += f"Category: {ticket.category}\n"
            text += f"Status: {ticket.status}\n"
            text += f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"View #{ticket.ticket_number}",
                callback_data=f"view_ticket_{ticket.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        context.user_data['ticket_category'] = category
        await query.edit_message_text(
            "Please enter your full name:"
        )
        return ENTERING_NAME
    
    elif data.startswith("view_ticket_"):
        ticket_id = int(data.replace("view_ticket_", ""))
        ticket = db_session.query(Ticket).get(ticket_id)
        
        if not ticket:
            await query.edit_message_text("Ticket not found.", reply_markup=get_start_keyboard())
            return
        
        text = format_ticket_info(ticket)
        await query.edit_message_text(
            text,
            reply_markup=get_ticket_action_keyboard(ticket.ticket_number),
            parse_mode='Markdown'
        )
    
    elif data.startswith("reply_"):
        ticket_number = data.replace("reply_", "")
        context.user_data['reply_ticket'] = ticket_number
        await query.edit_message_text(
            "Please type your reply message:"
        )
        return ENTERING_REPLY
    
    elif data == "back_to_main":
        await query.edit_message_text(
            "Main Menu:",
            reply_markup=get_start_keyboard()
        )
    
    elif data == "help":
        help_text = (
            "📚 **How to Use ToonPay Support Bot**\n\n"
            "• Click 'New Ticket' to create a support ticket\n"
            "• Select the appropriate category for your issue\n"
            "• Provide your details and describe your problem\n"
            "• You'll receive updates when admins respond\n"
            "• Each ticket is for one issue only\n"
            "• Tickets close after admin reply\n"
            "• Response time: Within 24 hours 🚀\n\n"
            "For urgent issues, please contact support@toonpay.com"
        )
        await query.edit_message_text(help_text, reply_markup=get_start_keyboard(), parse_mode='Markdown')

@private_chat_only
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user name input"""
    name = update.message.text
    context.user_data['ticket_name'] = name
    
    await update.message.reply_text("Please enter your email address:")
    return ENTERING_EMAIL

@private_chat_only
async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user email input"""
    email = update.message.text
    context.user_data['ticket_email'] = email
    
    await update.message.reply_text("Please enter your phone number (with country code):")
    return ENTERING_PHONE

@private_chat_only
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user phone input"""
    phone = update.message.text
    context.user_data['ticket_phone'] = phone
    
    await update.message.reply_text(
        "Please describe your issue in detail:\n"
        "Include any relevant information that might help us assist you better."
    )
    return ENTERING_QUESTION

@private_chat_only
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user question and create ticket"""
    question = update.message.text
    user = update.effective_user
    
    # Update user details in database
    db_user = db_session.query(User).filter_by(user_id=user.id).first()
    if db_user:
        db_user.name = context.user_data.get('ticket_name', db_user.name)
        db_user.email = context.user_data.get('ticket_email', db_user.email)
        db_user.phone = context.user_data.get('ticket_phone', db_user.phone)
        db_user.last_active = update.message.date
    
    # Create ticket - FIXED: using string 'open' instead of TicketStatus.OPEN
    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        user_id=user.id,
        category=context.user_data.get('ticket_category', 'other'),
        question=question,
        status='open'  # Changed from TicketStatus.OPEN
    )
    
    db_session.add(ticket)
    db_session.commit()
    
    # Send confirmation to user
    await update.message.reply_text(
        f"✅ **Ticket Created Successfully!**\n\n"
        f"Ticket Number: `{ticket.ticket_number}`\n"
        f"Category: {ticket.category}\n\n"
        f"Your ticket has been submitted. Our support team will get back to you within 24 hours.\n"
        f"You can check your ticket status anytime using 'My Tickets' option.",
        parse_mode='Markdown',
        reply_markup=get_start_keyboard()
    )
    
    # Forward to admin group
    try:
        admin_text = (
            f"🆕 **New Support Ticket**\n\n"
            f"Ticket: #{ticket.ticket_number}\n"
            f"User: {db_user.name or 'N/A'} (@{user.username or 'N/A'})\n"
            f"User ID: `{user.id}`\n"
            f"Category: {ticket.category}\n"
            f"Email: {db_user.email or 'N/A'}\n"
            f"Phone: {db_user.phone or 'N/A'}\n\n"
            f"**Question:**\n{question}\n\n"
            f"Time: {ticket.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        from src.keyboards.admin_keyboards import get_ticket_admin_keyboard
        await context.bot.send_message(
            chat_id=context.bot_data.get('admin_group_id'),
            text=admin_text,
            reply_markup=get_ticket_admin_keyboard(ticket.ticket_number, user.id),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to forward to admin group: {e}")
    
    # Clear user data
    for key in ['ticket_category', 'ticket_name', 'ticket_email', 'ticket_phone']:
        context.user_data.pop(key, None)
    
    return ConversationHandler.END

@private_chat_only
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user reply to ticket"""
    reply_text = update.message.text
    ticket_number = context.user_data.get('reply_ticket')
    
    if not ticket_number:
        await update.message.reply_text("Session expired. Please start over.")
        return ConversationHandler.END
    
    ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
    
    if not ticket:
        await update.message.reply_text("Ticket not found.")
        return ConversationHandler.END
    
    # Save reply
    reply = TicketReply(
        ticket_id=ticket.id,
        admin_id=update.effective_user.id,
        admin_username=update.effective_user.username or "User",
        message=reply_text
    )
    
    db_session.add(reply)
    # FIXED: using string 'open' instead of TicketStatus.OPEN
    ticket.status = 'open'  # Changed from TicketStatus.OPEN
    db_session.commit()
    
    await update.message.reply_text(
        f"✅ Your reply has been added to ticket #{ticket_number}.\n"
        f"Support team will get back to you soon.",
        reply_markup=get_start_keyboard()
    )
    
    # Notify admin group
    try:
        await context.bot.send_message(
            chat_id=context.bot_data.get('admin_group_id'),
            text=f"📝 User replied to ticket #{ticket_number}\n\nReply: {reply_text}"
        )
    except Exception as e:
        logger.error(f"Failed to notify admin group: {e}")
    
    context.user_data.pop('reply_ticket', None)
    return ConversationHandler.END

@private_chat_only
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("Operation cancelled.", reply_markup=get_start_keyboard())
    return ConversationHandler.END

# Conversation handler for ticket creation
ticket_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_callback, pattern="^new_ticket$")],
    states={
        SELECTING_CATEGORY: [CallbackQueryHandler(handle_callback, pattern="^cat_")],
        ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        ENTERING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        ENTERING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    name="ticket_creation",
    persistent=True,
    per_message=False,
    per_chat=True
)

# Conversation handler for replies
reply_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_callback, pattern="^reply_")],
    states={
        ENTERING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    name="user_reply",
    persistent=True,
    per_message=False,
    per_chat=True
)
