from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from utils.helpers import create_excel_sheet
import logging
from config import Config

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def is_admin_group(self, update: Update) -> bool:
        """Check if command is from an admin group"""
        chat_id = update.effective_chat.id
        # Since we're using a single admin group from config, just check that
        return chat_id == Config.ADMIN_GROUP_ID
    
    async def handle_admin_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin button actions (reply, progress, spam)"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_admin_group(update):
            await query.edit_message_text("❌ This command is only available in admin groups.")
            return
        
        data = query.data
        admin = query.from_user
        
        # Extract ticket ID from callback data
        if data.startswith('reply_'):
            ticket_id = int(data.split('_')[1])
            context.user_data['replying_to'] = ticket_id
            await query.edit_message_text(
                f"✏️ **Replying to Ticket #{ticket_id}**\n\n"
                f"Please type your reply below:",
                parse_mode='Markdown'
            )
        
        elif data.startswith('progress_'):
            ticket_id = int(data.split('_')[1])
            success = self.db.update_ticket_status(ticket_id, 'in_progress', admin.id, admin.username)
            
            if success:
                await query.edit_message_text(
                    f"✅ **Ticket #{ticket_id}**\n\n"
                    f"Status: 🔄 In Progress\n"
                    f"Admin: @{admin.username}\n\n"
                    f"The ticket has been marked as in progress.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    f"❌ **Failed to update Ticket #{ticket_id}**\n\n"
                    f"Please try again or check if ticket exists.",
                    parse_mode='Markdown'
                )
        
        elif data.startswith('spam_'):
            ticket_id = int(data.split('_')[1])
            success = self.db.update_ticket_status(ticket_id, 'spam', admin.id, admin.username)
            
            if success:
                await query.edit_message_text(
                    f"🚫 **Ticket #{ticket_id}**\n\n"
                    f"Status: ❌ Closed as Spam\n"
                    f"Admin: @{admin.username}\n\n"
                    f"This ticket has been marked as spam and closed.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    f"❌ **Failed to mark Ticket #{ticket_id} as spam**\n\n"
                    f"Please try again or check if ticket exists.",
                    parse_mode='Markdown'
                )
    
    async def handle_admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin reply to a ticket"""
        if not await self.is_admin_group(update):
            return
        
        if 'replying_to' not in context.user_data:
            return
        
        ticket_id = context.user_data['replying_to']
        reply_text = update.message.text
        admin = update.effective_user
        
        # Save reply
        if self.db.reply_to_ticket(ticket_id, reply_text, admin.id, admin.username):
            # Get ticket info to notify user
            ticket = self.db.get_ticket(ticket_id)
            
            if ticket:
                user_id = ticket['user_id']
                question = ticket['question']
                
                # Notify user
                try:
                    await context.bot.send_message(
                        user_id,
                        f"✅ **Your ticket #{ticket_id} has been answered!**\n\n"
                        f"**Your question:**\n{question[:200]}{'...' if len(question) > 200 else ''}\n\n"
                        f"**Answer:**\n{reply_text}\n\n"
                        f"Thank you for contacting ToonPay Support!\n"
                        f"Need more help? Create a new ticket with /start",
                        parse_mode='Markdown'
                    )
                    logger.info(f"User {user_id} notified about ticket #{ticket_id}")
                except Exception as e:
                    logger.error(f"Failed to notify user: {e}")
            
            await update.message.reply_text(
                f"✅ **Reply sent for Ticket #{ticket_id}**\n\n"
                f"Admin: @{admin.username}\n"
                f"Reply: {reply_text[:100]}{'...' if len(reply_text) > 100 else ''}",
                parse_mode='Markdown'
            )
            
            # Update the original admin group message if possible
            if update.effective_message and update.effective_message.reply_to_message:
                try:
                    await update.effective_message.reply_to_message.edit_text(
                        f"✅ **Ticket #{ticket_id}**\n\n"
                        f"Status: ✅ Closed\n"
                        f"Replied by: @{admin.username}\n"
                        f"Reply: {reply_text[:100]}{'...' if len(reply_text) > 100 else ''}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to update original message: {e}")
        else:
            await update.message.reply_text(
                f"❌ **Failed to reply to Ticket #{ticket_id}**\n\n"
                f"Ticket may be already closed or doesn't exist.",
                parse_mode='Markdown'
            )
        
        del context.user_data['replying_to']
    
    async def pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending tickets"""
        if not await self.is_admin_group(update):
            return
        
        tickets = self.db.get_pending_tickets()
        
        if not tickets:
            await update.message.reply_text("✅ No pending tickets.")
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
            message = f"👤 **User:** {user['first_name']} {user.get('last_name', '')}\n"
            message += f"📝 **Username:** @{user['username'] or 'N/A'}\n"
            message += f"🆔 **User ID:** `{user_id}`\n\n"
            
            for ticket in user_tickets[:3]:  # Show max 3 tickets per user
                status_emoji = '⏳' if ticket['status'] == 'pending' else '🔄'
                message += f"{status_emoji} **Ticket #{ticket['ticket_id']}**\n"
                message += f"📅 {ticket['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                message += f"📧 {ticket.get('email', 'N/A')}\n"
                message += f"❓ {ticket['question'][:100]}...\n\n"
                
                # Add action buttons for each ticket
                keyboard = [[
                    InlineKeyboardButton("💬 Reply", callback_data=f"reply_{ticket['ticket_id']}"),
                    InlineKeyboardButton("🔄 In Progress", callback_data=f"progress_{ticket['ticket_id']}")
                ]]
                keyboard.append([InlineKeyboardButton("❌ Spam", callback_data=f"spam_{ticket['ticket_id']}")])
                
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                message = ""  # Reset for next ticket
            
            if len(user_tickets) > 3:
                await update.message.reply_text(
                    f"... and {len(user_tickets) - 3} more tickets from this user"
                )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show statistics"""
        if not await self.is_admin_group(update):
            return
        
        stats = self.db.get_stats()
        
        message = "📊 **Support Bot Statistics**\n\n"
        message += f"📈 **Total Tickets:** {stats['total']}\n"
        message += f"✅ **Closed:** {stats['closed']}\n"
        message += f"🔄 **In Progress:** {stats['in_progress']}\n"
        message += f"⏳ **Pending:** {stats['pending']}\n"
        message += f"🚫 **Spam:** {stats.get('spam', 0)}\n\n"
        message += "👨‍💼 **Admin Performance:**\n"
        
        if stats['admin_stats']:
            for admin, solved, closed in stats['admin_stats']:
                message += f"• @{admin}: {solved} tickets solved ({closed} closed)\n"
        else:
            message += "• No tickets solved yet\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search users"""
        if not await self.is_admin_group(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔍 **Usage:** `/search <name/username/user_id/email>`\n\n"
                "Examples:\n"
                "• `/search john`\n"
                "• `/search @username`\n"
                "• `/search 123456789`\n"
                "• `/search user@example.com`",
                parse_mode='Markdown'
            )
            return
        
        query = ' '.join(context.args)
        results = self.db.search_user(query)
        
        if not results:
            await update.message.reply_text(f"❌ No users found matching: `{query}`", parse_mode='Markdown')
            return
        
        for user in results:
            message = f"👤 **User Information**\n\n"
            message += f"**Name:** {user['first_name']} {user.get('last_name', '')}\n"
            message += f"**Username:** @{user['username'] or 'N/A'}\n"
            message += f"**User ID:** `{user['user_id']}`\n"
            message += f"**Email:** {user.get('email', 'N/A')}\n"
            message += f"**Phone:** {user.get('phone', 'N/A')}\n"
            message += f"**Registered:** {user['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
            
            if user.get('tickets'):
                message += f"**Tickets ({len(user['tickets'])}):**\n"
                for ticket in user['tickets'][:3]:
                    status_emoji = {
                        'pending': '⏳',
                        'in_progress': '🔄',
                        'closed': '✅',
                        'spam': '🚫'
                    }.get(ticket['status'], '❓')
                    
                    message += f"{status_emoji} #{ticket['ticket_id']} - {ticket['created_at'].strftime('%Y-%m-%d')}\n"
                
                if len(user['tickets']) > 3:
                    message += f"... and {len(user['tickets']) - 3} more\n"
            else:
                message += "**No tickets found**\n"
            
            # Split long messages
            if len(message) > 4000:
                for i in range(0, len(message), 3500):
                    await update.message.reply_text(message[i:i+3500], parse_mode='Markdown')
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
    
    async def download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Download tickets as Excel"""
        if not await self.is_admin_group(update):
            return
        
        tickets = self.db.export_all_tickets()
        
        if not tickets:
            await update.message.reply_text("📭 No tickets to export.")
            return
        
        # Create Excel file
        excel_file = create_excel_sheet(tickets)
        
        await update.message.reply_document(
            document=excel_file,
            filename=f"support_tickets_{update.effective_date.strftime('%Y%m%d')}.xlsx",
            caption=f"📊 **Support Tickets Export**\n"
                    f"📅 {update.effective_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"📈 Total: {len(tickets)} tickets"
        )
