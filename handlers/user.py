from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import Database
from utils.validators import validate_email, validate_phone, sanitize_input
from config import Config

# States
EMAIL, PHONE, QUESTION = range(3)

class UserHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Only work in private chat
        if update.effective_chat.type != 'private':
            return
        
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        keyboard = [[InlineKeyboardButton("📝 Submit Ticket", callback_data="new_ticket")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(Config.WELCOME_MESSAGE, reply_markup=reply_markup)
    
    async def new_ticket(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(Config.CONTACT_REQUEST)
        context.user_data['ticket_step'] = 'email'
        return EMAIL
    
    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        email = update.message.text.strip()
        
        if not validate_email(email):
            await update.message.reply_text("❌ Invalid email format. Please send a valid email address.")
            return EMAIL
        
        context.user_data['email'] = email
        await update.message.reply_text("✅ Email saved! Now send your phone number:")
        return PHONE
    
    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        phone = update.message.text.strip()
        
        if not validate_phone(phone):
            await update.message.reply_text("❌ Invalid phone number. Please send a valid phone number (10-15 digits).")
            return PHONE
        
        context.user_data['phone'] = phone
        await update.message.reply_text("✅ Phone saved! Now describe your issue:")
        return QUESTION
    
    async def get_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        question = sanitize_input(update.message.text)
        user = update.effective_user
        
        # Update user contact info
        self.db.update_user_contact(user.id, context.user_data['email'], context.user_data['phone'])
        
        # Create ticket
        ticket_id = self.db.create_ticket(user.id, question)
        
        # Notify admin groups
        admin_groups = self.db.get_admin_groups()
        ticket_info = (
            f"🎫 New Ticket #{ticket_id}\n"
            f"From: @{user.username or 'N/A'} ({user.first_name})\n"
            f"User ID: {user.id}\n"
            f"Email: {context.user_data['email']}\n"
            f"Phone: {context.user_data['phone']}\n\n"
            f"Question: {question}"
        )
        
        keyboard = [[
            InlineKeyboardButton("✅ Mark In Progress", callback_data=f"progress_{ticket_id}"),
            InlineKeyboardButton("💬 Reply", callback_data=f"reply_{ticket_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for group_id in admin_groups:
            try:
                await context.bot.send_message(
                    group_id, 
                    ticket_info, 
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Failed to send to group {group_id}: {e}")
        
        await update.message.reply_text(Config.TICKET_CREATED.format(ticket_id))
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Ticket creation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
