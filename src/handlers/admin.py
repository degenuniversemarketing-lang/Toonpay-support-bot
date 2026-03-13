from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import db_session
from src.models import User, Ticket, TicketReply
from src.utils.helpers import format_user_info
from src.config import Config
import logging
from datetime import datetime
import pandas as pd
from io import BytesIO
import html
import traceback

logger = logging.getLogger(__name__)

# Simple check for admin group
def is_admin_group(chat_id: int) -> bool:
    return chat_id == Config.ADMIN_GROUP_ID

# Safe HTML escaping for all text
def safe_text(text):
    """Convert text to safe HTML format"""
    if text is None:
        return ""
    return html.escape(str(text))

async def admin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all admin commands"""
    try:
        # Check if this is the admin group
        if not is_admin_group(update.effective_chat.id):
            return
        
        command = update.message.text.split()[0].lower()
        logger.info(f"Admin command received: {command}")
        
        if command == "/admin":
            await show_admin_panel(update, context)
        elif command == "/stats":
            await show_stats(update, context)
        elif command == "/pending":
            await show_pending(update, context)
        elif command == "/search":
            await search_tickets(update, context)
        elif command == "/getdata":
            await export_data(update, context)
        elif command == "/reply":
            await quick_reply(update, context)
    except Exception as e:
        logger.error(f"Error in admin_command_handler: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    try:
        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("⏳ Pending Tickets", callback_data="admin_pending")],
            [InlineKeyboardButton("🔍 Search", callback_data="admin_search")],
            [InlineKeyboardButton("📥 Download Data", callback_data="admin_download")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "👨‍💼 <b>Admin Control Panel</b>\n\n"
            "Select an option below or use commands:\n"
            "/stats - View statistics\n"
            "/pending - View pending tickets\n"
            "/search &lt;term&gt; - Search\n"
            "/getdata - Download all data\n"
            "/reply &lt;ticket&gt; &lt;message&gt; - Quick reply"
        )
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in show_admin_panel: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    try:
        total_users = db_session.query(User).count()
        total_tickets = db_session.query(Ticket).count()
        open_tickets = db_session.query(Ticket).filter_by(status='open').count()
        in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
        closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
        
        today = datetime.utcnow().date()
        today_tickets = db_session.query(Ticket).filter(
            Ticket.created_at >= today
        ).count()
        
        text = (
            f"📊 <b>Support Statistics</b>\n\n"
            f"<b>Users:</b> {total_users}\n\n"
            f"<b>Tickets:</b>\n"
            f"Total: {total_tickets}\n"
            f"🟢 Open: {open_tickets}\n"
            f"🟡 In Progress: {in_progress}\n"
            f"🔴 Closed: {closed_tickets}\n"
            f"📅 Today: {today_tickets}"
        )
        
        await update.message.reply_text(text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in show_stats: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets"""
    try:
        tickets = db_session.query(Ticket).filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).order_by(Ticket.created_at.desc()).all()
        
        if not tickets:
            await update.message.reply_text("✅ No pending tickets found.")
            return
        
        await update.message.reply_text(f"📋 Found {len(tickets)} pending tickets:")
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            status_emoji = '🟡' if ticket.status == 'in_progress' else '🟢'
            
            username = safe_text(user.username) if user and user.username else 'N/A'
            name = safe_text(user.name) if user and user.name else 'N/A'
            
            text = (
                f"{status_emoji} <b>Ticket #{safe_text(ticket.ticket_number)}</b>\n"
                f"👤 <b>User:</b> {name} (@{username})\n"
                f"📂 <b>Category:</b> {safe_text(ticket.category)}\n"
                f"📊 <b>Status:</b> {safe_text(ticket.status)}\n"
                f"⏰ <b>Created:</b> {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"💬 <b>Question:</b> {safe_text(ticket.question[:150])}...\n"
            )
            
            keyboard = [[
                InlineKeyboardButton(
                    f"📝 Reply", 
                    callback_data=f"reply_{ticket.ticket_number}"
                ),
                InlineKeyboardButton(
                    "🟡 Mark In Progress",
                    callback_data=f"progress_{ticket.ticket_number}"
                ),
                InlineKeyboardButton(
                    "👤 View User",
                    callback_data=f"viewuser_{ticket.user_id}"
                )
            ]]
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error in show_pending: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Error showing pending tickets: {str(e)}")

async def search_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search tickets"""
    try:
        if not context.args:
            text = (
                "🔍 <b>Search Help</b>\n\n"
                "Usage: /search &lt;search term&gt;\n\n"
                "<b>Examples:</b>\n"
                "• /search TKT-20240313 - Search by ticket number\n"
                "• /search @username - Search by username\n"
                "• /search 123456789 - Search by user ID\n"
                "• /search john - Search by name"
            )
            await update.message.reply_text(text, parse_mode='HTML')
            return
        
        search_term = ' '.join(context.args).strip()
        await update.message.reply_text(f"🔍 Searching for: {safe_text(search_term)}...")
        
        results = []
        
        # Search by ticket number
        ticket = db_session.query(Ticket).filter_by(ticket_number=search_term).first()
        if ticket:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            username = safe_text(user.username) if user else 'N/A'
            name = safe_text(user.name) if user else 'N/A'
            
            text = (
                f"✅ <b>Ticket Found</b>\n\n"
                f"<b>Ticket #:</b> {safe_text(ticket.ticket_number)}\n"
                f"<b>User:</b> {name} (@{username})\n"
                f"<b>User ID:</b> <code>{ticket.user_id}</code>\n"
                f"<b>Category:</b> {safe_text(ticket.category)}\n"
                f"<b>Status:</b> {safe_text(ticket.status)}\n"
                f"<b>Created:</b> {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"<b>Question:</b> {safe_text(ticket.question)}"
            )
            
            keyboard = [[
                InlineKeyboardButton("📝 Reply", callback_data=f"reply_{ticket.ticket_number}")
            ]]
            
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            return
        
        # Search by username
        clean_username = search_term.replace('@', '')
        users = db_session.query(User).filter(
            User.username.ilike(f"%{clean_username}%")
        ).all()
        
        for user in users:
            results.append(f"👤 @{safe_text(user.username)} - ID: <code>{user.user_id}</code>")
        
        # Search by user ID
        if search_term.isdigit():
            user = db_session.query(User).filter_by(user_id=int(search_term)).first()
            if user:
                results.append(f"👤 @{safe_text(user.username)} - ID: <code>{user.user_id}</code>")
        
        # Search by name
        name_users = db_session.query(User).filter(
            User.name.ilike(f"%{search_term}%")
        ).all()
        
        for user in name_users:
            if user not in users:
                results.append(f"👤 {safe_text(user.name)} (@{safe_text(user.username)}) - ID: <code>{user.user_id}</code>")
        
        if results:
            text = "🔍 <b>Search Results:</b>\n\n" + "\n".join(results[:10])
            if len(results) > 10:
                text += f"\n\n... and {len(results) - 10} more"
            await update.message.reply_text(text, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ No results found.")
            
    except Exception as e:
        logger.error(f"Error in search_tickets: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Error searching: {str(e)}")

async def quick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick reply command: /reply TKT-12345 Your message here"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /reply &lt;ticket_number&gt; &lt;message&gt;\n"
                "Example: /reply TKT-20240313 Thank you for your message",
                parse_mode='HTML'
            )
            return
        
        ticket_number = context.args[0]
        reply_text = ' '.join(context.args[1:])
        
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if not ticket:
            await update.message.reply_text(f"❌ Ticket {safe_text(ticket_number)} not found.")
            return
        
        # Save reply
        reply = TicketReply(
            ticket_id=ticket.id,
            admin_id=update.effective_user.id,
            admin_username=update.effective_user.username or "Admin",
            message=reply_text
        )
        
        db_session.add(reply)
        ticket.status = 'closed'
        ticket.updated_at = datetime.utcnow()
        db_session.commit()
        
        # Notify user
        try:
            user_text = (
                f"📨 <b>Reply to your ticket #{ticket_number}</b>\n\n"
                f"<b>Support Team:</b> {safe_text(reply_text)}\n\n"
                f"This ticket is now closed. If you have more questions, please create a new ticket."
            )
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=user_text,
                parse_mode='HTML'
            )
            await update.message.reply_text(f"✅ Reply sent. Ticket #{ticket_number} closed.")
        except:
            await update.message.reply_text(f"✅ Reply saved but user cannot be notified.")
            
    except Exception as e:
        logger.error(f"Error in quick_reply: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all data"""
    try:
        msg = await update.message.reply_text("📥 Generating export...")
        
        tickets = db_session.query(Ticket).order_by(Ticket.created_at.desc()).all()
        data = []
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            replies = db_session.query(TicketReply).filter_by(ticket_id=ticket.id).all()
            last_reply = replies[-1] if replies else None
            
            data.append({
                'Ticket #': ticket.ticket_number,
                'User Name': user.name if user else 'N/A',
                'Username': user.username if user else 'N/A',
                'User ID': ticket.user_id,
                'Email': user.email if user else 'N/A',
                'Phone': user.phone if user else 'N/A',
                'Category': ticket.category,
                'Question': ticket.question,
                'Status': ticket.status,
                'Admin Reply': last_reply.message if last_reply else '',
                'Replied By': last_reply.admin_username if last_reply else '',
                'Created At': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Updated At': ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        filename = f"tickets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        await msg.delete()
        await update.message.reply_document(
            document=output,
            filename=filename,
            caption=f"✅ Exported {len(tickets)} tickets"
        )
    except Exception as e:
        logger.error(f"Error in export_data: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    
    try:
        await query.answer()
        
        if not is_admin_group(query.message.chat.id):
            await query.edit_message_text("⛔ This action is only allowed in the admin group.")
            return
        
        data = query.data
        logger.info(f"Admin callback: {data}")
        
        if data == "admin_stats":
            # Show stats
            total_users = db_session.query(User).count()
            total_tickets = db_session.query(Ticket).count()
            open_tickets = db_session.query(Ticket).filter_by(status='open').count()
            in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
            closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
            
            text = (
                f"📊 <b>Support Statistics</b>\n\n"
                f"<b>Users:</b> {total_users}\n\n"
                f"<b>Tickets:</b>\n"
                f"Total: {total_tickets}\n"
                f"🟢 Open: {open_tickets}\n"
                f"🟡 In Progress: {in_progress}\n"
                f"🔴 Closed: {closed_tickets}"
            )
            await query.edit_message_text(text, parse_mode='HTML')
        
        elif data == "admin_pending":
            # Show pending tickets in a new message
            await query.message.delete()
            await show_pending(update, context)
        
        elif data == "admin_search":
            text = (
                "🔍 <b>Search Help</b>\n\n"
                "Use /search command with your search term.\n\n"
                "<b>Examples:</b>\n"
                "• /search TKT-20240313\n"
                "• /search @username\n"
                "• /search 123456789"
            )
            await query.edit_message_text(text, parse_mode='HTML')
        
        elif data == "admin_download":
            await query.message.delete()
            await export_data(update, context)
        
        elif data.startswith("reply_"):
            ticket_number = data.replace("reply_", "")
            context.user_data['replying_to'] = ticket_number
            await query.edit_message_text(
                f"📝 Please type your reply for ticket #{safe_text(ticket_number)}:"
            )
        
        elif data.startswith("progress_"):
            ticket_number = data.replace("progress_", "")
            ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
            if ticket:
                ticket.status = 'in_progress'
                ticket.updated_at = datetime.utcnow()
                db_session.commit()
                
                await query.edit_message_text(
                    f"✅ Ticket #{safe_text(ticket_number)} marked as in progress by @{safe_text(update.effective_user.username or 'Admin')}"
                )
                
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=ticket.user_id,
                        text=f"🟡 Your ticket #{ticket_number} is now being reviewed by our support team."
                    )
                except:
                    pass
        
        elif data.startswith("viewuser_"):
            user_id = int(data.replace("viewuser_", ""))
            user = db_session.query(User).filter_by(user_id=user_id).first()
            if user:
                user_tickets = db_session.query(Ticket).filter_by(user_id=user_id).order_by(Ticket.created_at.desc()).all()
                
                text = (
                    f"👤 <b>User Details</b>\n"
                    f"Name: {safe_text(user.name)}\n"
                    f"Username: @{safe_text(user.username)}\n"
                    f"User ID: <code>{user.user_id}</code>\n"
                    f"Email: {safe_text(user.email)}\n"
                    f"Phone: {safe_text(user.phone)}\n"
                    f"Joined: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"📊 <b>Tickets: {len(user_tickets)}</b>\n"
                )
                
                for t in user_tickets[:5]:
                    emoji = '🟢' if t.status == 'open' else '🟡' if t.status == 'in_progress' else '🔴'
                    text += f"{emoji} #{t.ticket_number} - {t.status}\n"
                
                await query.edit_message_text(text, parse_mode='HTML')
        
        elif data.startswith("close_"):
            await query.delete_message()
    
    except Exception as e:
        logger.error(f"Error in admin_callback_handler: {e}\n{traceback.format_exc()}")
        await query.edit_message_text(f"❌ Error: {str(e)}")

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text replies to tickets"""
    try:
        if not is_admin_group(update.effective_chat.id):
            return
        
        ticket_number = context.user_data.get('replying_to')
        if not ticket_number:
            return
        
        reply_text = update.message.text
        logger.info(f"Processing reply to ticket {ticket_number}")
        
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if not ticket:
            await update.message.reply_text(f"❌ Ticket {safe_text(ticket_number)} not found.")
            context.user_data.pop('replying_to', None)
            return
        
        # Save reply
        reply = TicketReply(
            ticket_id=ticket.id,
            admin_id=update.effective_user.id,
            admin_username=update.effective_user.username or "Admin",
            message=reply_text
        )
        
        db_session.add(reply)
        ticket.status = 'closed'
        ticket.updated_at = datetime.utcnow()
        db_session.commit()
        
        # Notify user
        try:
            user_text = (
                f"📨 <b>Reply to your ticket #{ticket_number}</b>\n\n"
                f"<b>Support Team:</b> {safe_text(reply_text)}\n\n"
                f"This ticket is now closed. If you have more questions, please create a new ticket."
            )
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=user_text,
                parse_mode='HTML'
            )
            await update.message.reply_text(f"✅ Reply sent. Ticket #{ticket_number} closed.")
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
            await update.message.reply_text(f"✅ Reply saved but user cannot be notified.")
        
        context.user_data.pop('replying_to', None)
        
    except Exception as e:
        logger.error(f"Error in admin_reply_handler: {e}\n{traceback.format_exc()}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Function to send new ticket to admin group
async def send_ticket_to_admin_group(context, ticket, user, question):
    """Send new ticket notification to admin group"""
    try:
        username = safe_text(user.username) if user and user.username else 'N/A'
        name = safe_text(user.name) if user and user.name else 'N/A'
        email = safe_text(user.email) if user and user.email else 'N/A'
        phone = safe_text(user.phone) if user and user.phone else 'N/A'
        question_text = safe_text(question) if question else 'N/A'
        
        text = (
            f"🆕 <b>New Support Ticket</b>\n\n"
            f"<b>Ticket:</b> #{ticket.ticket_number}\n"
            f"<b>User:</b> {name} (@{username})\n"
            f"<b>User ID:</b> <code>{user.user_id}</code>\n"
            f"<b>Category:</b> {ticket.category}\n"
            f"<b>Email:</b> {email}\n"
            f"<b>Phone:</b> {phone}\n\n"
            f"<b>Question:</b>\n{question_text}\n\n"
            f"<b>Time:</b> {ticket.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        keyboard = [[
            InlineKeyboardButton("📝 Reply", callback_data=f"reply_{ticket.ticket_number}"),
            InlineKeyboardButton("🟡 In Progress", callback_data=f"progress_{ticket.ticket_number}"),
            InlineKeyboardButton("👤 View User", callback_data=f"viewuser_{user.user_id}"),
            InlineKeyboardButton("❌ Dismiss", callback_data=f"close_{ticket.ticket_number}")
        ]]
        
        await context.bot.send_message(
            chat_id=Config.ADMIN_GROUP_ID,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        logger.info(f"Ticket {ticket.ticket_number} sent to admin group")
        
    except Exception as e:
        logger.error(f"Failed to send to admin group: {e}\n{traceback.format_exc()}")
