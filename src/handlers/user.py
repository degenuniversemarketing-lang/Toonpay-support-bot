# src/handlers/user.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime

from src.database import db
from src.config import config
from src.keyboards import (
    get_main_keyboard, get_categories_keyboard,
    get_confirmation_keyboard, get_user_tickets_keyboard
)
from src.utils import (
    validate_email, validate_phone, format_ticket_info,
    format_ticket_list, escape_html
)

logger = logging.getLogger(__name__)

# Conversation states
NAME, EMAIL, PHONE, QUESTION, CONFIRM = range(5)

class UserHandlers:
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - only works in private"""
        # Check if in private chat
        if update.effective_chat.type != 'private':
            # Delete message in groups
            try:
                await update.message.delete()
            except:
                pass
            return
        
        user = update.effective_user
        
        # Check if started from group
        if context.args and context.args[0] == 'group':
            welcome_text = f"""
👋 Welcome to {config.COMPANY_NAME} Support!

You've been redirected from a group. Please create a ticket below and our support team will assist you.

{config.SUPPORT_MESSAGE}
"""
        else:
            welcome_text = f"""
👋 Welcome to {config.COMPANY_NAME} Support!

I'm here to help you with any issues you're experiencing.

{config.SUPPORT_MESSAGE}

Choose an option below to get started:
"""
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard()
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'new_ticket':
            # Start new ticket creation
            context.user_data.clear()
            await query.edit_message_text(
                "📝 <b>Please enter your full name:</b>\n\n"
                "Example: John Doe",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data='cancel')
                ]])
            )
            return NAME
        
        elif data == 'my_tickets':
            # Show user's tickets
            user_id = update.effective_user.id
            tickets = db.get_user_tickets(user_id, limit=10)
            
            if tickets:
                text = format_ticket_list(tickets, "📋 Your Tickets")
                await query.edit_message_text(
                    text,
                    reply_markup=get_user_tickets_keyboard(tickets),
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    "📭 You haven't created any tickets yet.\n\n"
                    "Click 'New Ticket' to create your first ticket.",
                    reply_markup=get_main_keyboard()
                )
        
        elif data == 'help':
            help_text = f"""
ℹ️ <b>Help & Support</b>

<b>How to create a ticket:</b>
1. Click 'New Ticket'
2. Select issue category
3. Provide your details
4. Describe your issue
5. Submit

<b>Important Notes:</b>
• Each ticket is for one issue only
• Tickets close after admin reply
• Create new ticket for new questions
• Response Time: Within 24 hours

{config.SUPPORT_MESSAGE}
"""
            await query.edit_message_text(
                help_text,
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
        
        elif data == 'main_menu':
            await query.edit_message_text(
                f"👋 Welcome back!\n\n{config.SUPPORT_MESSAGE}",
                reply_markup=get_main_keyboard()
            )
        
        elif data == 'cancel':
            context.user_data.clear()
            await query.edit_message_text(
                "❌ Operation cancelled.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
        
        elif data.startswith('cat_'):
            # Category selected
            category = data.replace('cat_', '')
            context.user_data['category'] = category
            
            category_info = config.CATEGORIES.get(category, {'name': category})
            
            await query.edit_message_text(
                f"📝 <b>Describe your issue</b>\n\n"
                f"Category: {category_info['name']}\n\n"
                f"Please provide details about your issue:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data='cancel')
                ]])
            )
            return QUESTION
        
        elif data.startswith('view_ticket_'):
            # View specific ticket
            ticket_id = data.replace('view_ticket_', '')
            ticket = db.get_ticket(ticket_id)
            
            if ticket:
                text = format_ticket_info(ticket, include_admin=True)
                keyboard = [[
                    InlineKeyboardButton("🔙 Back to Tickets", callback_data='my_tickets')
                ]]
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
    
    @staticmethod
    async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user's full name"""
        # Delete user's message for privacy
        try:
            await update.message.delete()
        except:
            pass
        
        name = update.message.text.strip()
        
        if len(name) < 2:
            await update.message.reply_text(
                "❌ Please enter a valid name (minimum 2 characters):"
            )
            return NAME
        
        context.user_data['full_name'] = name
        
        await update.message.reply_text(
            "📧 <b>Please enter your email address:</b>\n\n"
            "Example: user@example.com",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data='cancel')
            ]])
        )
        return EMAIL
    
    @staticmethod
    async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user's email"""
        try:
            await update.message.delete()
        except:
            pass
        
        email = update.message.text.strip()
        
        if not validate_email(email):
            await update.message.reply_text(
                "❌ Invalid email format. Please enter a valid email:"
            )
            return EMAIL
        
        context.user_data['email'] = email
        
        await update.message.reply_text(
            "📱 <b>Please enter your phone number:</b>\n\n"
            "Example: +1234567890",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data='cancel')
            ]])
        )
        return PHONE
    
    @staticmethod
    async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user's phone number"""
        try:
            await update.message.delete()
        except:
            pass
        
        phone = update.message.text.strip()
        
        if not validate_phone(phone):
            await update.message.reply_text(
                "❌ Invalid phone format. Please enter a valid phone number:"
            )
            return PHONE
        
        context.user_data['phone'] = phone
        
        # Show categories
        await update.message.reply_text(
            "📋 <b>Select Issue Category:</b>",
            parse_mode='HTML',
            reply_markup=get_categories_keyboard()
        )
        return ConversationHandler.END
    
    @staticmethod
    async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get user's question and confirm"""
        try:
            await update.message.delete()
        except:
            pass
        
        question = update.message.text.strip()
        
        if len(question) < 10:
            await update.message.reply_text(
                "❌ Please provide more details (minimum 10 characters):"
            )
            return QUESTION
        
        context.user_data['question'] = question
        
        # Show confirmation
        category = context.user_data.get('category', 'other')
        category_info = config.CATEGORIES.get(category, {'name': category})
        
        confirm_text = f"""
✅ <b>Please confirm your ticket details:</b>

<b>Name:</b> {escape_html(context.user_data['full_name'])}
<b>Email:</b> {escape_html(context.user_data['email'])}
<b>Phone:</b> {escape_html(context.user_data['phone'])}
<b>Category:</b> {category_info['name']}

<b>Question:</b>
{escape_html(question)}

Is everything correct?
"""
        
        await update.message.reply_text(
            confirm_text,
            parse_mode='HTML',
            reply_markup=get_confirmation_keyboard()
        )
        return CONFIRM
    
    @staticmethod
    async def confirm_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and create ticket"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'confirm_yes':
            # Create ticket
            user = update.effective_user
            user_id = user.id
            username = user.username or "NoUsername"
            
            # Save user to database
            db.get_or_create_user(
                user_id=user_id,
                username=username,
                full_name=context.user_data['full_name'],
                email=context.user_data['email'],
                phone=context.user_data['phone']
            )
            
            # Create ticket
            ticket = db.create_ticket(
                user_id=user_id,
                category=context.user_data['category'],
                question=context.user_data['question']
            )
            
            # Send confirmation to user
            await query.edit_message_text(
                f"✅ <b>Ticket Created Successfully!</b>\n\n"
                f"Your ticket ID: <code>{ticket.ticket_id}</code>\n\n"
                f"We'll get back to you soon.\n\n"
                f"{config.SUPPORT_MESSAGE}",
                parse_mode='HTML',
                reply_markup=get_main_keyboard()
            )
            
            # Notify admin group
            await UserHandlers.notify_admin_group(context, ticket, user)
            
            # Clear user data
            context.user_data.clear()
            
        else:
            await query.edit_message_text(
                "❌ Ticket creation cancelled.",
                reply_markup=get_main_keyboard()
            )
            context.user_data.clear()
        
        return ConversationHandler.END
    
    @staticmethod
    async def notify_admin_group(context: ContextTypes.DEFAULT_TYPE, ticket, user):
        """Notify admin group about new ticket"""
        try:
            from src.keyboards import get_ticket_action_keyboard
            
            user_info = db.get_user(user.id)
            category_info = config.CATEGORIES.get(ticket.category, {'name': ticket.category, 'emoji': '📌'})
            
            admin_text = f"""
🎫 <b>NEW TICKET</b>

<b>Ticket ID:</b> <code>{ticket.ticket_id}</code>
<b>Status:</b> 🟢 Open

👤 <b>User Details:</b>
• ID: <code>{user.id}</code>
• Username: @{user.username if user.username else 'N/A'}
• Name: {escape_html(user_info.full_name)}
• Email: {escape_html(user_info.email)}
• Phone: {escape_html(user_info.phone)}

📋 <b>Ticket Details:</b>
• Category: {category_info['emoji']} {category_info['name']}
• Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}

📝 <b>Issue Description:</b>
{escape_html(ticket.question)}

<b>Response Time:</b> Within 24 hours
"""
            
            await context.bot.send_message(
                chat_id=config.ADMIN_GROUP_ID,
                text=admin_text,
                reply_markup=get_ticket_action_keyboard(ticket.ticket_id, ticket.status),
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Failed to notify admin group: {e}")
