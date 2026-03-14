from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from database import Database
from utils.helpers import create_excel_sheet
import io

class AdminHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def is_admin_group(self, update: Update) -> bool:
        """Check if command is from an admin group"""
        chat_id = update.effective_chat.id
        admin_groups = self.db.get_admin_groups()
        return chat_id in admin_groups
    
    async def pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin_group(update):
            return
        
        tickets = self.db.get_pending_tickets()
        
        if not tickets:
            await update.message.reply_text("No pending tickets.")
            return
        
        # Group tickets by user
        users_tickets = {}
        for ticket in tickets:
            user_id = ticket['user_id']
            if user_id not in users_tickets:
                users_tickets[user_id] = []
            users_tickets[user_id].append(ticket)
        
        for user_id, user_tickets in users_tickets.items():
            user = user_tickets[0]
            message = f"👤 Name: {user['first_name']} {user.get('last_name', '')}\n"
            message += f"📝 Username: @{user['username'] or 'N/A'}\n"
            message += f"🆔 User ID: {user_id}\n\n"
            
            for ticket in user_tickets:
                message += f"🎫 Ticket #{ticket['ticket_id']}\n"
                message += f"📊 Status: {ticket['status']}\n"
                message += f"📅 Date: {ticket['created_at']}\n"
                message += f"📧 Email: {ticket.get('email', 'N/A')}\n"
                message += f"❓ Question: {ticket['question']}\n"
                if ticket['admin_answer']:
                    message += f"💬 Answer: {ticket['admin_answer']}\n"
                if ticket['replied_by_username']:
                    message += f"👨‍💼 Replied by: @{ticket['replied_by_username']}\n"
                message += "─" * 30 + "\n"
            
            # Add reply button for each ticket
            keyboard = []
            for ticket in user_tickets[:5]:  # Limit to 5 tickets per message
                if ticket['status'] in ['pending', 'in_progress']:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"💬 Reply to Ticket #{ticket['ticket_id']}", 
                            callback_data=f"reply_{ticket['ticket_id']}"
                        )
                    ])
            
            if len(user_tickets) > 5:
                message += f"\n... and {len(user_tickets) - 5} more tickets"
            
            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message)
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin_group(update):
            return
        
        stats = self.db.get_stats()
        
        message = "📊 **Support Bot Statistics**\n\n"
        message += f"📈 Total Tickets: {stats['total']}\n"
        message += f"✅ Closed: {stats['closed']}\n"
        message += f"🔄 In Progress: {stats['in_progress']}\n"
        message += f"⏳ Pending: {stats['pending']}\n\n"
        message += "👨‍💼 **Admin Performance:**\n"
        
        for admin, solved, closed in stats['admin_stats']:
            message += f"@{admin}: {solved} tickets solved\n"
        
        await update.message.reply_text(message)
    
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin_group(update):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /search <name/username/user_id/email>")
            return
        
        query = ' '.join(context.args)
        results = self.db.search_user(query)
        
        if not results:
            await update.message.reply_text("No users found.")
            return
        
        for user in results:
            message = f"👤 Name: {user['first_name']} {user.get('last_name', '')}\n"
            message += f"📝 Username: @{user['username'] or 'N/A'}\n"
            message += f"🆔 User ID: {user['user_id']}\n"
            message += f"📧 Email: {user.get('email', 'N/A')}\n"
            message += f"📞 Phone: {user.get('phone', 'N/A')}\n\n"
            
            if user['tickets']:
                message += "**Tickets:**\n"
                for ticket in user['tickets']:
                    message += f"🎫 Ticket #{ticket['ticket_id']}\n"
                    message += f"📊 Status: {ticket['status']}\n"
                    message += f"📅 Date: {ticket['created_at']}\n"
                    message += f"❓ Q: {ticket['question']}\n"
                    if ticket['admin_answer']:
                        message += f"💬 A: {ticket['admin_answer']}\n"
                    message += "─" * 20 + "\n"
            
            await update.message.reply_text(message)
    
    async def download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin_group(update):
            return
        
        # Get all tickets
        tickets = self.db.export_all_tickets()
        
        if not tickets:
            await update.message.reply_text("No tickets to export.")
            return
        
        # Create Excel file
        excel_file = create_excel_sheet(tickets)
        
        await update.message.reply_document(
            document=excel_file,
            filename="support_tickets.xlsx",
            caption="📊 Support Tickets Export"
        )
    
    async def handle_reply_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if not await self.is_admin_group(update):
            return
        
        data = query.data
        if data.startswith('reply_'):
            ticket_id = int(data.split('_')[1])
            context.user_data['replying_to'] = ticket_id
            await query.edit_message_text(
                f"Please send your reply for Ticket #{ticket_id}:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_reply")
                ]])
            )
        
        elif data.startswith('progress_'):
            ticket_id = int(data.split('_')[1])
            admin = query.from_user
            self.db.update_ticket_status(ticket_id, 'in_progress', admin.id, admin.username)
            await query.edit_message_text(f"✅ Ticket #{ticket_id} marked as in progress.")
    
    async def handle_admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_admin_group(update):
            return
        
        if 'replying_to' not in context.user_data:
            return
        
        ticket_id = context.user_data['replying_to']
        reply_text = update.message.text
        admin = update.effective_user
        
        # Save reply
        if self.db.reply_to_ticket(ticket_id, reply_text, admin.id, admin.username):
            # Get ticket info
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT user_id, question FROM tickets WHERE ticket_id = %s
            ''', (ticket_id,))
            user_id, question = cursor.fetchone()
            cursor.close()
            
            # Notify user
            try:
                await context.bot.send_message(
                    user_id,
                    f"✅ Your ticket #{ticket_id} has been answered!\n\n"
                    f"Your question: {question}\n"
                    f"Answer: {reply_text}\n\n"
                    f"Thank you for contacting support!"
                )
            except Exception as e:
                print(f"Failed to notify user: {e}")
            
            await update.message.reply_text(f"✅ Reply sent for Ticket #{ticket_id}")
            
            # Update the original admin group message
            if update.effective_message:
                await update.effective_message.edit_text(
                    f"✅ Ticket #{ticket_id} has been replied by @{admin.username}"
                )
        else:
            await update.message.reply_text(f"❌ Ticket #{ticket_id} is already closed.")
        
        del context.user_data['replying_to']
