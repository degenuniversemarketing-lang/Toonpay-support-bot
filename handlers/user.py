from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import Database
from utils.validators import validate_email, validate_phone, sanitize_input
from config import Config
import logging
import traceback

logger = logging.getLogger(__name__)

# States
CATEGORY, NAME, EMAIL, PHONE, QUESTION = range(5)

# Ticket categories
CATEGORIES = {
    'technical': '🛠️ Can't login to Account',
    'payment': '💰 Funds Missing',
    'account': '👤 KYC Related',
    'feature': '💳Card Issue',
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
3️⃣ Provide your name
4️⃣ Provide your email
5️⃣ Provide your phone number
6️⃣ Describe your issue
7️⃣ Submit

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
3. Provide your full name
4. Provide your email address
5. Provide your phone number
6. Describe your issue
7. Submit

**Important Notes:**
• Each ticket is for one issue only
• Tickets close after admin reply
• Create new ticket for new questions
• Your details are saved for faster support

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
            "👤 **Please enter your full name:**\n\n"
            "Example: `John Doe`",
            parse_mode='Markdown'
        )
        return NAME
    
    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate name"""
        name = sanitize_input(update.message.text.strip())
        
        if len(name) < 2:
            await update.message.reply_text(
                "❌ **Please enter a valid name (at least 2 characters).**\n\n"
                "Try again:",
                parse_mode='Markdown'
            )
            return NAME
        
        context.user_data['name'] = name
        await update.message.reply_text(
            "✅ **Name saved!**\n\n"
            "📧 **Now enter your email address:**\n\n"
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
            "Example: `+1234567890` or `1234567890`",
            parse_mode='Markdown'
        )
        return PHONE
    
    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate phone"""
        phone = update.message.text.strip()
        
        if not validate_phone(phone):
            await update.message.reply_text(
                "❌ **Invalid phone number!**\n\n"
                "Please send a valid phone number (10-15 digits).\n"
                "Example: `+1234567890` or `1234567890`",
                parse_mode='Markdown'
            )
            return PHONE
        
        context.user_data['phone'] = phone
        await update.message.reply_text(
            "✅ **Phone saved!**\n\n"
            "📝 **Now describe your issue in detail:**\n\n"
            "Please include:\n"
            "• What happened?\n"
            "• When did it happen?\n"
            "• Any error messages?",
            parse_mode='Markdown'
        )
        return QUESTION
    
    async def get_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle question and create ticket"""
        try:
            question = sanitize_input(update.message.text)
            user = update.effective_user
            
            if not question:
                await update.message.reply_text(
                    "❌ **Please describe your issue.**\n\n"
                    "Try again:",
                    parse_mode='Markdown'
                )
                return QUESTION
            
            # Update user contact info with name
            self.db.update_user_contact(
                user.id, 
                context.user_data['email'], 
                context.user_data['phone'],
                context.user_data.get('name', user.first_name)
            )
            
            # Create ticket with category
            full_question = f"[{context.user_data['category']}]\n\n{question}"
            ticket_id = self.db.create_ticket(user.id, full_question)
            
            if ticket_id:
                # Notify admin group
                ticket_info = (
                    f"🎫 **New Ticket #{ticket_id}**\n\n"
                    f"**Category:** {context.user_data['category']}\n"
                    f"**Name:** {context.user_data.get('name', user.first_name)}\n"
                    f"**From:** @{user.username or 'N/A'}\n"
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
                
                # Send to admin group
                try:
                    await context.bot.send_message(
                        Config.ADMIN_GROUP_ID, 
                        ticket_info,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Ticket #{ticket_id} sent to admin group")
                except Exception as e:
                    logger.error(f"Failed to send to admin group: {e}")
                    # Notify super admin
                    try:
                        await context.bot.send_message(
                            Config.SUPER_ADMIN_ID,
                            f"⚠️ **Failed to send Ticket #{ticket_id} to admin group!**\n\nError: {str(e)}",
                            parse_mode='Markdown'
                        )
                    except:
                        pass
                
                # Confirm to user
                success_text = f"""✅ **Your ticket has been created!**

**Ticket ID:** `#{ticket_id}`
**Category:** {context.user_data['category']}
**Name:** {context.user_data.get('name', user.first_name)}

We'll get back to you soon.

You can check your ticket status using /start and clicking 'My Tickets'."""
                
                await update.message.reply_text(success_text, parse_mode='Markdown')
            else:
                # Ticket creation failed
                await update.message.reply_text(
                    "❌ **Failed to create ticket.**\n\n"
                    "Please try again later or contact @ToonPaySupport",
                    parse_mode='Markdown'
                )
                # Notify super admin
                try:
                    await context.bot.send_message(
                        Config.SUPER_ADMIN_ID,
                        f"🚨 **Ticket Creation Failed**\n\n"
                        f"User: @{user.username} (ID: {user.id})\n"
                        f"Category: {context.user_data['category']}\n"
                        f"Error: Database returned None",
                        parse_mode='Markdown'
                    )
                except:
                    pass
            
            # Clear user data
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in ticket creation: {e}")
            logger.error(traceback.format_exc())
            
            await update.message.reply_text(
                "❌ **An error occurred while creating your ticket.**\n\n"
                "Please try again later or contact @ToonPaySupport",
                parse_mode='Markdown'
            )
            
            # Notify super admin
            try:
                await context.bot.send_message(
                    Config.SUPER_ADMIN_ID,
                    f"🚨 **Ticket Creation Error**\n\n"
                    f"User: @{update.effective_user.username} (ID: {update.effective_user.id})\n"
                    f"Error: {str(e)}\n\n"
                    f"Traceback:\n`{traceback.format_exc()[:500]}`",
                    parse_mode='Markdown'
                )
            except Exception as e2:
                logger.error(f"Failed to notify super admin: {e2}")
            
            context.user_data.clear()
            return ConversationHandler.END
    
    # NEW: Custom command handler for user commands
    async def custom_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom commands added by super admin"""
        command = update.message.text.split()[0][1:].lower()  # Remove / and get command
        
        # Skip built-in commands
        built_in = ['start', 'new', 'cancel', 'support', 'pending', 'stats', 
                   'search', 'download', 'download_solved', 'download_pending',
                   'activate', 'deactivate', 'listactivated', 'deletedata',
                   'addfilter', 'removefilter', 'listfilters', 'broadcast', 'allstats']
        
        if command in built_in:
            return False  # Let built-in handlers process it
        
        # Get custom command from database
        cmd_data = self.db.get_custom_command(command)
        
        if cmd_data:
            content = cmd_data['content']
            # Check if content is a link (starts with http)
            if content.startswith(('http://', 'https://', 't.me/', 'www.')):
                # Add http if missing
                if content.startswith('t.me/'):
                    content = 'https://' + content
                elif content.startswith('www.'):
                    content = 'https://' + content
                
                # Send as button
                keyboard = [[InlineKeyboardButton("🔗 Click Here", url=content)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"Here's your requested link:",
                    reply_markup=reply_markup
                )
            else:
                # Send as text
                await update.message.reply_text(content)
            return True
        return False
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        await update.message.reply_text(
            "❌ **Ticket creation cancelled.**\n\n"
            "You can start again anytime with /start",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
