import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.models import User, Ticket
from src.database import db_session
from src.keyboards.user_keyboards import *
from src.utils.helpers import generate_ticket_number, log_admin_action
from src.config import Config

logger = logging.getLogger(__name__)

# Conversation states
NAME, EMAIL, PHONE, USER_ID, ISSUE = range(5)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command in private chat"""
    user = update.effective_user
    
    # Save or update user in database
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
    
    welcome_text = (
        f"👋 Welcome to Toonpay Support Bot!\n\n"
        f"Hello {user.first_name}, I'm here to help you with any issues you're facing.\n\n"
        f"📋 Please select an option below:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace('cat_', '')
    context.user_data['category'] = category
    
    await query.edit_message_text(
        f"📝 Selected category: {category}\n\n"
        f"Please click the button below to create a new ticket:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Create New Ticket", callback_data="new_ticket")
        ]])
    )

async def start_ticket_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the ticket creation process"""
    query = update.callback_query
    await query.answer()
    
    if 'category' not in context.user_data:
        await query.edit_message_text(
            "Please select a category first:",
            reply_markup=get_categories_keyboard()
        )
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📝 Please enter your full name:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's name"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("📧 Please enter your email address:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's email"""
    context.user_data['email'] = update.message.text
    await update.message.reply_text("📞 Please enter your phone number:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's phone"""
    context.user_data['phone'] = update.message.text
    await update.message.reply_text(
        "🆔 Please enter your User ID (if any, or type 'skip'):"
    )
    return USER_ID

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's ID"""
    user_id_text = update.message.text
    if user_id_text.lower() == 'skip':
        context.user_data['user_id_input'] = 'Not provided'
    else:
        context.user_data['user_id_input'] = user_id_text
    
    await update.message.reply_text(
        "📝 Please describe your issue in detail:"
    )
    return ISSUE

async def get_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get issue description and create ticket"""
    user = update.effective_user
    issue = update.message.text
    
    # Generate ticket number
    ticket_number = generate_ticket_number()
    
    # Save ticket to database
    ticket = Ticket(
        ticket_number=ticket_number,
        user_id=user.id,
        category=context.user_data['category'],
        name=context.user_data['name'],
        email=context.user_data['email'],
        phone=context.user_data['phone'],
        question=issue,
        status='new'
    )
    db_session.add(ticket)
    db_session.commit()
    
    # Send confirmation to user
    await update.message.reply_text(
        f"✅ **Ticket Created Successfully!**\n\n"
        f"📋 **Ticket Number:** `{ticket_number}`\n"
        f"📂 **Category:** {context.user_data['category']}\n"
        f"⏱ **Response Time:** Within 24 hours\n\n"
        f"Our support team will get back to you soon. "
        f"You'll be notified when we reply.",
        parse_mode='Markdown'
    )
    
    # Send ticket to admin group
    await send_ticket_to_admin_group(update, context, ticket, user)
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

async def send_ticket_to_admin_group(update: Update, context: ContextTypes.DEFAULT_TYPE, ticket, user):
    """Send new ticket to admin group"""
    ticket_message = (
        f"🆕 **New Support Ticket**\n\n"
        f"**Ticket:** `{ticket.ticket_number}`\n"
        f"**User:** {ticket.name} (@{user.username if user.username else 'N/A'})\n"
        f"**User ID:** `{user.id}`\n"
        f"**Category:** {ticket.category}\n"
        f"**Email:** {ticket.email}\n"
        f"**Phone:** {ticket.phone}\n\n"
        f"**Question:**\n{ticket.question}\n\n"
        f"**Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
    )
    
    keyboard = get_admin_ticket_keyboard(ticket.ticket_number)
    
    await context.bot.send_message(
        chat_id=Config.ADMIN_GROUP_ID,
        text=ticket_message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text(
        "❌ Ticket creation cancelled. You can start again with /start"
    )
    return ConversationHandler.END
