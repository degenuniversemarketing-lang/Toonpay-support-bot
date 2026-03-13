from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import db_session
from src.models import User, Ticket, TicketReply
from src.utils.helpers import format_user_info, format_ticket_info
from src.keyboards.admin_keyboards import get_ticket_admin_keyboard, get_admin_main_keyboard
from src.config import Config
import logging
from datetime import datetime
import pandas as pd
from io import BytesIO

logger = logging.getLogger(__name__)

# Helper function to check if message is from admin group
def is_admin_group(update: Update) -> bool:
    """Check if the message is from the admin group"""
    if not update.effective_chat:
        return False
    chat_id = update.effective_chat.id
    return chat_id == Config.ADMIN_GROUP_ID

# Admin commands
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel start command"""
    if not is_admin_group(update):
        return
    
    try:
        logger.info(f"Admin start command received from chat {update.effective_chat.id}")
        await update.message.reply_text(
            "👨‍💼 **Admin Control Panel**\n\n"
            "Available commands:\n"
            "/stats - View statistics\n"
            "/pending - View pending tickets\n"
            "/search <term> - Search users/tickets\n"
            "/getdata - Download all data\n\n"
            "Or use the buttons below:",
            parse_mode='Markdown',
            reply_markup=get_admin_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in admin_start: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    if not is_admin_group(update):
        return
    
    try:
        logger.info(f"Admin stats command received from chat {update.effective_chat.id}")
        
        # Get counts
        total_users = db_session.query(User).count()
        total_tickets = db_session.query(Ticket).count()
        open_tickets = db_session.query(Ticket).filter_by(status='open').count()
        in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
        closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
        
        # Today's tickets
        today = datetime.utcnow().date()
        today_tickets = db_session.query(Ticket).filter(
            Ticket.created_at >= today
        ).count()
        
        stats_text = (
            f"📊 **Support Statistics**\n\n"
            f"**Users:**\n"
            f"Total Users: {total_users}\n\n"
            f"**Tickets:**\n"
            f"Total: {total_tickets}\n"
            f"🟢 Open: {open_tickets}\n"
            f"🟡 In Progress: {in_progress}\n"
            f"🔴 Closed: {closed_tickets}\n"
            f"📅 Today: {today_tickets}\n\n"
            f"⏱ Response Time: Within 24 hours"
        )
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in admin_stats: {e}")
        await update.message.reply_text(f"Error getting statistics: {str(e)}")

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets"""
    if not is_admin_group(update):
        return
    
    try:
        logger.info(f"Admin pending command received from chat {update.effective_chat.id}")
        
        # Get pending tickets
        tickets = db_session.query(Ticket).filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).order_by(Ticket.created_at.desc()).limit(10).all()
        
        if not tickets:
            await update.message.reply_text("No pending tickets found.")
            return
        
        text = "⏳ **Recent Pending Tickets:**\n\n"
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            status_emoji = '🟡' if ticket.status == 'in_progress' else '🟢'
            text += f"{status_emoji} **#{ticket.ticket_number}**\n"
            text += f"User: {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
            text += f"Category: {ticket.category}\n"
            text += f"Status: {ticket.status}\n"
            text += f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            text += f"Question: {ticket.question[:50]}...\n\n"
            
            # Add reply button for each ticket
            keyboard = [[InlineKeyboardButton(
                f"📝 Reply to #{ticket.ticket_number}", 
                callback_data=f"admin_reply_{ticket.ticket_number}"
            )]]
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            text = ""  # Reset text for next ticket
        
    except Exception as e:
        logger.error(f"Error in admin_pending: {e}")
        await update.message.reply_text(f"Error showing pending tickets: {str(e)}")

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search users or tickets"""
    if not is_admin_group(update):
        return
    
    try:
        if not context.args:
            await update.message.reply_text(
                "Usage: /search <term>\n"
                "Search by: username, user ID, email, or ticket number"
            )
            return
        
        search_term = ' '.join(context.args).strip()
        logger.info(f"Admin search command: '{search_term}' from chat {update.effective_chat.id}")
        
        # Search users
        users = db_session.query(User).filter(
            (User.username.ilike(f"%{search_term}%")) |
            (User.email.ilike(f"%{search_term}%")) |
            (User.name.ilike(f"%{search_term}%")) |
            (User.user_id == (int(search_term) if search_term.isdigit() else 0))
        ).all()
        
        # Search tickets
        tickets = db_session.query(Ticket).filter(
            Ticket.ticket_number.ilike(f"%{search_term}%")
        ).all()
        
        if not users and not tickets:
            await update.message.reply_text("No results found.")
            return
        
        text = f"🔍 **Search Results for '{search_term}'**\n\n"
        
        if users:
            text += "**Users Found:**\n"
            for user in users[:5]:
                text += f"• {user.name or 'N/A'} (@{user.username or 'N/A'}) - ID: `{user.user_id}`\n"
            text += "\n"
        
        if tickets:
            text += "**Tickets Found:**\n"
            for ticket in tickets[:5]:
                user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
                text += f"• #{ticket.ticket_number} - {ticket.category} - {user.name or 'N/A'}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in admin_search: {e}")
        await update.message.reply_text(f"Error searching: {str(e)}")

async def admin_getdata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download all tickets data"""
    if not is_admin_group(update):
        return
    
    try:
        await update.message.reply_text("📥 Generating data export, please wait...")
        logger.info(f"Admin getdata command from chat {update.effective_chat.id}")
        
        # Get all tickets with user info
        tickets = db_session.query(Ticket).order_by(Ticket.created_at.desc()).all()
        
        data = []
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            last_reply = ticket.replies[-1] if ticket.replies else None
            
            data.append({
                'Ticket Number': ticket.ticket_number,
                'User Name': user.name if user else 'N/A',
                'Username': user.username if user else 'N/A',
                'User ID': ticket.user_id,
                'Email': user.email if user else 'N/A',
                'Phone': user.phone if user else 'N/A',
                'Category': ticket.category,
                'Question': ticket.question,
                'Status': ticket.status,
                'Admin Answer': last_reply.message if last_reply else '',
                'Admin Username': last_reply.admin_username if last_reply else '',
                'Created At': ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Updated At': ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Generate CSV
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        await update.message.reply_document(
            document=output,
            filename=f"tickets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            caption="✅ Tickets data export"
        )
    except Exception as e:
        logger.error(f"Error in admin_getdata: {e}")
        await update.message.reply_text(f"Error generating data: {str(e)}")

# Callback handler for admin buttons
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callback queries"""
    query = update.callback_query
    await query.answer()
    
    # Only allow from admin group
    if query.message.chat.id != Config.ADMIN_GROUP_ID:
        await query.edit_message_text("This action is only allowed in the admin group.")
        return
    
    data = query.data
    logger.info(f"Admin callback: {data} from user {update.effective_user.id}")
    
    try:
        if data.startswith("admin_reply_"):
            ticket_number = data.replace("admin_reply_", "")
            context.user_data['replying_to_ticket'] = ticket_number
            await query.edit_message_text(
                f"Please type your reply for ticket #{ticket_number}:"
            )
            
        elif data.startswith("progress_"):
            ticket_number = data.replace("progress_", "")
            ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
            if ticket:
                ticket.status = 'in_progress'
                db_session.commit()
                
                await query.edit_message_text(
                    f"✅ Ticket #{ticket_number} marked as in progress by @{update.effective_user.username}"
                )
                
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=ticket.user_id,
                        text=f"🟡 Your ticket #{ticket_number} is now being reviewed by our support team."
                    )
                except:
                    pass
        
        elif data.startswith("close_"):
            ticket_number = data.replace("close_", "")
            ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
            if ticket:
                ticket.status = 'closed'
                db_session.commit()
                
                await query.edit_message_text(
                    f"✅ Ticket #{ticket_number} closed by @{update.effective_user.username}"
                )
                
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=ticket.user_id,
                        text=f"🔴 Your ticket #{ticket_number} has been closed. If you need further assistance, please create a new ticket."
                    )
                except:
                    pass
        
        elif data.startswith("view_user_"):
            user_id = int(data.replace("view_user_", ""))
            user = db_session.query(User).filter_by(user_id=user_id).first()
            if user:
                tickets = db_session.query(Ticket).filter_by(user_id=user_id).order_by(Ticket.created_at.desc()).all()
                text = format_user_info(user, tickets)
                await query.edit_message_text(text, parse_mode='Markdown')
        
        elif data == "admin_stats":
            stats_text = await get_stats_text()
            await query.edit_message_text(stats_text, parse_mode='Markdown')
        
        elif data == "admin_pending":
            await query.edit_message_text("Use /pending command to see pending tickets.")
        
        elif data == "admin_search":
            await query.edit_message_text("Use /search command with your search term.")
        
        elif data == "admin_download":
            await query.edit_message_text("Use /getdata command to download data.")
        
        elif data == "admin_back":
            await query.edit_message_text(
                "Admin Menu:",
                reply_markup=get_admin_main_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error in admin_callback_handler: {e}")
        await query.edit_message_text(f"Error: {str(e)}")

# Handler for admin replies
async def admin_handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reply to ticket"""
    # Only allow from admin group
    if update.effective_chat.id != Config.ADMIN_GROUP_ID:
        return
    
    ticket_number = context.user_data.get('replying_to_ticket')
    if not ticket_number:
        return
    
    try:
        reply_text = update.message.text
        logger.info(f"Admin reply to ticket {ticket_number}: {reply_text[:50]}...")
        
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        
        if not ticket:
            await update.message.reply_text("Ticket not found.")
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
        
        # Send to user
        try:
            user_text = (
                f"📨 **Reply to your ticket #{ticket_number}**\n\n"
                f"Support Team: {reply_text}\n\n"
                f"This ticket is now closed. If you have more questions, please create a new ticket."
            )
            await context.bot.send_message(
                chat_id=ticket.user_id,
                text=user_text,
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(f"✅ Reply sent to user. Ticket #{ticket_number} closed.")
        except Exception as e:
            logger.error(f"Failed to send reply to user: {e}")
            await update.message.reply_text(f"Reply saved but failed to send to user. Error: {e}")
        
        context.user_data.pop('replying_to_ticket', None)
        
    except Exception as e:
        logger.error(f"Error in admin_handle_reply: {e}")
        await update.message.reply_text(f"Error sending reply: {str(e)}")

# Helper function
async def get_stats_text():
    """Generate statistics text"""
    total_users = db_session.query(User).count()
    total_tickets = db_session.query(Ticket).count()
    open_tickets = db_session.query(Ticket).filter_by(status='open').count()
    in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
    closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
    
    today = datetime.utcnow().date()
    today_tickets = db_session.query(Ticket).filter(
        Ticket.created_at >= today
    ).count()
    
    return (
        f"📊 **Support Statistics**\n\n"
        f"**Users:**\n"
        f"Total Users: {total_users}\n\n"
        f"**Tickets:**\n"
        f"Total: {total_tickets}\n"
        f"🟢 Open: {open_tickets}\n"
        f"🟡 In Progress: {in_progress}\n"
        f"🔴 Closed: {closed_tickets}\n"
        f"📅 Today: {today_tickets}\n\n"
        f"⏱ Response Time: Within 24 hours"
    )
