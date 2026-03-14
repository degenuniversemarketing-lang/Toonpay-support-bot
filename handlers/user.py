from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import Database
from utils.validators import validate_email, validate_phone, sanitize_input
from config import Config
import logging

logger = logging.getLogger(__name__)

# States
CATEGORY, EMAIL, PHONE, QUESTION = range(4)

# Ticket categories
CATEGORIES = {
    'technical': '🛠️ Technical Issue',
    'payment': '💰 Payment Problem',
    'account': '👤 Account Issue',
    'feature': '✨ Feature Request',
    'other': '❓ Other'
}

class UserHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with enhanced UI"""
        # Only work in private chat
        if update.effective_chat.type != 'private':
            return
        
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = """🎫 **Welcome to ToonPay Support Bot!**

I'm here to help you with any issues you might have.

**How to create a ticket:**
1️⃣ Click 'New Ticket'
2️⃣ Select your issue category
3️⃣ Provide your details
4️⃣ Describe your issue
5️⃣ Submit

⏱️ **ToonPay Support Available 24/7**

Click the button below to start!"""
        
        keyboard = [
            [InlineKeyboardButton("📝 New Ticket", callback_data="new_ticket")],
            [InlineKeyboardButton("📋 My Tickets", callback_data="my_tickets"),
             InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button presses"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "new_ticket":
            # Show categories
            keyboard = []
            for key, value in CATEGORIES.items():
                keyboard.append([InlineKeyboardButton(value, callback_data=f"cat_{key}")])
            keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📋 **Select your issue category:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return CATEGORY
        
        elif query.data == "my_tickets":
            user_id = update.effective_user.id
            tickets = self.db.get_user_tickets(user_id)
            
            if not tickets:
                await query.edit_message_text(
                    "📭 You don't have any tickets yet.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📝 Create New Ticket", callback_data="new_ticket")
                    ]])
                )
                return
            
            text = "📋 **Your Tickets:**\n\n"
            for ticket in tickets[:5]:  # Show last 5 tickets
                status_emoji = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'closed': '✅',
                    'spam': '🚫'
                }.get(ticket['status'], '❓')
                
                text += f"{status_emoji} **Ticket #{ticket['ticket_id']}**\n"
                text += f"Status: {ticket['status'].title()}\n"
                text += f"Date: {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                if ticket['admin_answer']:
                    text += f"Reply: {ticket['admin_answer'][:50]}...\n"
                text += "─" * 20 + "\n"
            
            if len(tickets) > 5:
                text += f"\n... and {len(tickets) - 5} more tickets"
            
            keyboard = [[InlineKeyboardButton("📝 New Ticket", callback_data="new_ticket")]]
            if tickets:
                keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="my_tickets")])
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        elif query.data == "help":
            help_text = """ℹ️ **Help & Support**

**How to create a ticket:**
1. Click "New Ticket"
2. Select category
3. Provide your details
4. Describe your issue
5. Submit

**Important Notes:**
• Each ticket is for one issue only
• Tickets close after admin reply
• Create new ticket for new questions
• Your email and phone are saved for faster support

⏱️ **ToonPay Support Available 24/7**

Need immediate assistance? Contact @ToonPaySupport"""
            
            keyboard = [[InlineKeyboardButton("📝 New Ticket", callback_data="new_ticket")]]
            await query.edit_message_text(
                help_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        elif query.data == "cancel":
            await query.edit_message_text(
                "❌ Operation cancelled.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📝 New Ticket", callback_data="new_ticket")
                ]])
            )
            context.user_data.clear()
            return ConversationHandler.END
    
    async def category_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category selection"""
        query = update.callback_query
        await query.answer()
        
        category = query.data.replace('cat_', '')
        context.user_data['category'] = CATEGORIES.get(category, 'Other')
        
        await query.edit_message_text(
            "📧 **Please enter your email address:**\n\n"
            "Example: `user@example.com`",
            parse_mode='Markdown'
        )
        return EMAIL
    
    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate email"""
        email = update.message.text.strip()
        
        if not validate_email(email):
            await update.message.reply_text(
                "❌ **Invalid email format!**\n\n"
                "Please send a valid email address.\n"
                "Example: `user@example.com`",
                parse_mode='Markdown'
            )
            return EMAIL
        
        context.user_data['email'] = email
        await update.message.reply_text(
            "✅ **Email saved!**\n\n"
            "📞 **Now send your phone number:**\n\n"
            "Example: `+1234567890` or `1234567890`"
        )
        return PHONE
    
    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate phone"""
        phone = update.message.text.strip()
        
        if not validate_phone(phone):
            await update.message.reply_text(
                "❌ **Invalid phone number!**\n\n"
                "Please send a valid phone number (10-15 digits).\n"
                "Example: `+1234567890` or `1234567890`"
            )
            return PHONE
        
        context.user_data['phone'] = phone
        await update.message.reply_text(
            "✅ **Phone saved!**\n\n"
            "📝 **Now describe your issue in detail:**\n\n"
            "Please include:\n"
            "• What happened?\n"
            "• When did it happen?\n"
            "• Any error messages?"
        )
        return QUESTION
    
    async def get_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle question and create ticket"""
        question = sanitize_input(update.message.text)
        user = update.effective_user
        
        # Update user contact info
        self.db.update_user_contact(user.id, context.user_data['email'], context.user_data['phone'])
        
        # Create ticket with category
        full_question = f"[{context.user_data['category']}]\n\n{question}"
        ticket_id = self.db.create_ticket(user.id, full_question)
        
        if ticket_id:
            # Notify admin groups
            admin_groups = self.db.get_admin_groups()
            ticket_info = (
                f"🎫 **New Ticket #{ticket_id}**\n\n"
                f"**Category:** {context.user_data['category']}\n"
                f"**From:** @{user.username or 'N/A'} ({user.first_name})\n"
                f"**User ID:** `{user.id}`\n"
                f"**Email:** `{context.user_data['email']}`\n"
                f"**Phone:** `{context.user_data['phone']}`\n\n"
                f"**Question:**\n{question}"
            )
            
            # Create inline buttons for admin
            keyboard = [
                [
                    InlineKeyboardButton("💬 Reply", callback_data=f"reply_{ticket_id}"),
                    InlineKeyboardButton("🔄 In Progress", callback_data=f"progress_{ticket_id}")
                ],
                [InlineKeyboardButton("❌ Close as Spam", callback_data=f"spam_{ticket_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to all admin groups
            for group_id in admin_groups:
                try:
                    await context.bot.send_message(
                        group_id, 
                        ticket_info,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send to group {group_id}: {e}")
            
            # Confirm to user
            success_text = f"""✅ **Your ticket has been created!**

**Ticket ID:** `#{ticket_id}`
**Category:** {context.user_data['category']}

We'll get back to you soon.

You can check your ticket status using /start and clicking 'My Tickets'."""
            
            await update.message.reply_text(success_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❌ **Failed to create ticket.**\n\n"
                "Please try again later or contact @ToonPaySupport"
            )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        await update.message.reply_text(
            "❌ **Ticket creation cancelled.**\n\n"
            "You can start again anytime with /start",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
