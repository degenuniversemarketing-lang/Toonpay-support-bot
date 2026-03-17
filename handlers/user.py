from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import Database
from utils.validators import validate_email, validate_phone, sanitize_input
from utils.languages import LANGUAGES, get_string, DEFAULT_LANGUAGE
from config import Config
import logging
import traceback

logger = logging.getLogger(__name__)

# States
LANGUAGE, CATEGORY, NAME, EMAIL, PHONE, QUESTION = range(6)

# Ticket categories with language support
def get_categories(user_lang):
    return {
        'technical': get_string(user_lang, 'category_technical'),
        'payment': get_string(user_lang, 'category_payment'),
        'account': get_string(user_lang, 'category_account'),
        'feature': get_string(user_lang, 'category_feature'),
        'other': get_string(user_lang, 'category_other')
    }

class UserHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Always show language selection first"""
        # Only work in private chat
        if update.effective_chat.type != 'private':
            return
        
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        # Clear any existing user data to force fresh start
        context.user_data.clear()
        
        # Always show language selection on /start
        keyboard = []
        # Create language selection buttons (2 per row)
        lang_items = list(LANGUAGES.items())
        for i in range(0, len(lang_items), 2):
            row = []
            row.append(InlineKeyboardButton(lang_items[i][1], callback_data=f"lang_{lang_items[i][0]}"))
            if i+1 < len(lang_items):
                row.append(InlineKeyboardButton(lang_items[i+1][1], callback_data=f"lang_{lang_items[i+1][0]}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            get_string(DEFAULT_LANGUAGE, 'select_language'),  # Use English as default for language selection
            reply_markup=reply_markup
        )
        return LANGUAGE
    
    async def language_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection"""
        query = update.callback_query
        await query.answer()
        
        lang_code = query.data.replace('lang_', '')
        context.user_data['language'] = lang_code
        
        # Save language preference to database
        user_id = update.effective_user.id
        self.db.update_user_language(user_id, lang_code)
        
        # Show confirmation and main menu
        await query.edit_message_text(
            get_string(lang_code, 'language_changed')
        )
        
        # Send main menu
        welcome_text = get_string(lang_code, 'welcome')
        keyboard = [
            [InlineKeyboardButton(get_string(lang_code, 'new_ticket'), callback_data="new_ticket")],
            [InlineKeyboardButton(get_string(lang_code, 'my_tickets_btn'), callback_data="my_tickets"),
             InlineKeyboardButton(get_string(lang_code, 'help_btn'), callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button presses"""
        query = update.callback_query
        await query.answer()
        
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        
        if query.data == "new_ticket":
            # Show categories
            categories = get_categories(user_lang)
            keyboard = []
            for key, value in categories.items():
                keyboard.append([InlineKeyboardButton(value, callback_data=f"cat_{key}")])
            keyboard.append([InlineKeyboardButton(get_string(user_lang, 'cancel_btn'), callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                get_string(user_lang, 'select_category'),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return CATEGORY
        
        elif query.data == "my_tickets":
            user_id = update.effective_user.id
            tickets = self.db.get_user_tickets(user_id)
            
            if not tickets:
                await query.edit_message_text(
                    get_string(user_lang, 'no_tickets'),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(get_string(user_lang, 'create_new'), callback_data="new_ticket")
                    ]])
                )
                return
            
            text = f"{get_string(user_lang, 'my_tickets')}\n\n"
            for ticket in tickets[:5]:
                status_emoji = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'closed': '✅',
                    'spam': '🚫'
                }.get(ticket['status'], '❓')
                
                status_text = {
                    'pending': get_string(user_lang, 'status_pending'),
                    'in_progress': get_string(user_lang, 'status_in_progress'),
                    'closed': get_string(user_lang, 'status_closed'),
                    'spam': get_string(user_lang, 'status_spam')
                }.get(ticket['status'], ticket['status'])
                
                text += f"{status_emoji} **Ticket #{ticket['ticket_id']}**\n"
                text += f"{status_text}\n"
                text += f"📅 {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                if ticket['admin_answer']:
                    text += f"💬 {ticket['admin_answer'][:50]}...\n"
                text += "─" * 20 + "\n"
            
            if len(tickets) > 5:
                text += f"\n... and {len(tickets) - 5} more tickets"
            
            keyboard = [[InlineKeyboardButton(get_string(user_lang, 'create_new'), callback_data="new_ticket")]]
            if tickets:
                keyboard.append([InlineKeyboardButton(get_string(user_lang, 'refresh'), callback_data="my_tickets")])
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        elif query.data == "help":
            help_text = get_string(user_lang, 'help')
            keyboard = [[InlineKeyboardButton(get_string(user_lang, 'new_ticket'), callback_data="new_ticket")]]
            await query.edit_message_text(
                help_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return
        
        elif query.data == "cancel":
            await query.edit_message_text(
                get_string(user_lang, 'cancel'),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(get_string(user_lang, 'new_ticket'), callback_data="new_ticket")
                ]])
            )
            context.user_data.clear()
            return ConversationHandler.END
    
    async def category_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle category selection"""
        query = update.callback_query
        await query.answer()
        
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        categories = get_categories(user_lang)
        
        category_key = query.data.replace('cat_', '')
        category_value = categories.get(category_key, get_string(user_lang, 'category_other'))
        context.user_data['category'] = category_value
        context.user_data['category_key'] = category_key
        
        await query.edit_message_text(
            get_string(user_lang, 'ask_name'),
            parse_mode='Markdown'
        )
        return NAME
    
    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate name"""
        name = sanitize_input(update.message.text.strip())
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        
        if len(name) < 2:
            await update.message.reply_text(
                "❌ **Please enter a valid name (at least 2 characters).**\n\n"
                "Try again:",
                parse_mode='Markdown'
            )
            return NAME
        
        context.user_data['name'] = name
        await update.message.reply_text(
            get_string(user_lang, 'name_saved') + "\n\n" + get_string(user_lang, 'ask_email'),
            parse_mode='Markdown'
        )
        return EMAIL
    
    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate email"""
        email = update.message.text.strip()
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        
        if not validate_email(email):
            await update.message.reply_text(
                get_string(user_lang, 'invalid_email'),
                parse_mode='Markdown'
            )
            return EMAIL
        
        context.user_data['email'] = email
        await update.message.reply_text(
            get_string(user_lang, 'email_saved') + "\n\n" + get_string(user_lang, 'ask_phone'),
            parse_mode='Markdown'
        )
        return PHONE
    
    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get and validate phone"""
        phone = update.message.text.strip()
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        
        if not validate_phone(phone):
            await update.message.reply_text(
                get_string(user_lang, 'invalid_phone'),
                parse_mode='Markdown'
            )
            return PHONE
        
        context.user_data['phone'] = phone
        await update.message.reply_text(
            get_string(user_lang, 'phone_saved') + "\n\n" + get_string(user_lang, 'ask_question'),
            parse_mode='Markdown'
        )
        return QUESTION
    
    async def get_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle question and create ticket"""
        try:
            question = sanitize_input(update.message.text)
            user = update.effective_user
            user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
            
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
            
            # Save user's language preference to database
            self.db.update_user_language(user.id, user_lang)
            
            # Create ticket with category
            category_display = context.user_data['category']
            full_question = f"[{category_display}]\n\n{question}"
            ticket_id = self.db.create_ticket(user.id, full_question)
            
            if ticket_id:
                # Notify admin group (always in English for admins)
                ticket_info = (
                    f"🎫 **New Ticket #{ticket_id}**\n\n"
                    f"**Category:** {category_display}\n"
                    f"**Name:** {context.user_data.get('name', user.first_name)}\n"
                    f"**From:** @{user.username or 'N/A'}\n"
                    f"**User ID:** `{user.id}`\n"
                    f"**Language:** {LANGUAGES.get(user_lang, 'English')}\n"
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
                
                # Confirm to user in their language
                success_text = get_string(
                    user_lang, 
                    'ticket_created',
                    ticket_id=ticket_id,
                    category=category_display,
                    name=context.user_data.get('name', user.first_name)
                )
                
                await update.message.reply_text(success_text, parse_mode='Markdown')
            else:
                # Ticket creation failed
                await update.message.reply_text(
                    get_string(user_lang, 'ticket_failed'),
                    parse_mode='Markdown'
                )
                # Notify super admin
                try:
                    await context.bot.send_message(
                        Config.SUPER_ADMIN_ID,
                        f"🚨 **Ticket Creation Failed**\n\n"
                        f"User: @{user.username} (ID: {user.id})\n"
                        f"Category: {context.user_data['category']}\n"
                        f"Language: {user_lang}\n"
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
            
            user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
            
            await update.message.reply_text(
                get_string(user_lang, 'ticket_error'),
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
    
    async def custom_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom commands added by super admin"""
        command = update.message.text.split()[0][1:].lower()
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        
        # Skip built-in commands
        built_in = ['start', 'new', 'cancel', 'support', 'pending', 'stats', 
                   'search', 'download', 'download_solved', 'download_pending',
                   'activate', 'deactivate', 'listactivated', 'deletedata',
                   'addfilter', 'removefilter', 'listfilters', 'broadcast', 'allstats']
        
        if command in built_in:
            return False
        
        # Get custom command from database
        cmd_data = self.db.get_custom_command(command)
        
        if cmd_data:
            content = cmd_data['content']
            # Check if content is a link
            if content.startswith(('http://', 'https://', 't.me/', 'www.')):
                if content.startswith('t.me/'):
                    content = 'https://' + content
                elif content.startswith('www.'):
                    content = 'https://' + content
                
                keyboard = [[InlineKeyboardButton(get_string(user_lang, 'click_here'), url=content)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    get_string(user_lang, 'here_link'),
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(content)
            return True
        return False
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        user_lang = context.user_data.get('language', DEFAULT_LANGUAGE)
        await update.message.reply_text(
            get_string(user_lang, 'cancel'),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
