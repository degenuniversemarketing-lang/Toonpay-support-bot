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
import re

logger = logging.getLogger(__name__)

# Simple check for admin group
def is_admin_group(chat_id: int) -> bool:
    return chat_id == Config.ADMIN_GROUP_ID

async def admin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all admin commands"""
    # Check if this is the admin group
    if not is_admin_group(update.effective_chat.id):
        return
    
    command = update.message.text.split()[0].lower()
    logger.info(f"Admin command received: {command} in chat {update.effective_chat.id}")
    
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

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("⏳ Pending Tickets", callback_data="admin_pending")],
        [InlineKeyboardButton("🔍 Search", callback_data="admin_search")],
        [InlineKeyboardButton("📥 Download Data", callback_data="admin_download")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👨‍💼 **Admin Control Panel**\n\n"
        "Select an option below or use commands:\n"
        "/stats - View statistics\n"
        "/pending - View pending tickets\n"
        "/search <term> - Search users/tickets\n"
        "/reply <ticket#> <message> - Quick reply\n"
        "/getdata - Download all data",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

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
            f"📊 **Support Statistics**\n\n"
            f"**Users:** {total_users}\n\n"
            f"**Tickets:**\n"
            f"Total: {total_tickets}\n"
            f"🟢 Open: {open_tickets}\n"
            f"🟡 In Progress: {in_progress}\n"
            f"🔴 Closed: {closed_tickets}\n"
            f"📅 Today: {today_tickets}"
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in show_stats: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending tickets"""
    try:
        tickets = db_session.query(Ticket).filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).order_by(Ticket.created_at.desc()).all()
        
        if not tickets:
            await update.message.reply_text("✅ No pending tickets found.")
            return
        
        for ticket in tickets[:5]:  # Show only first 5 to avoid too many messages
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            status_emoji = '🟡' if ticket.status == 'in_progress' else '🟢'
            
            # Format question (truncate if too long)
            question = ticket.question[:100] + "..." if len(ticket.question) > 100 else ticket.question
            
            text = (
                f"{status_emoji} **Ticket #{ticket.ticket_number}**\n"
                f"👤 User: {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
                f"📋 Category: {ticket.category}\n"
                f"📊 Status: {ticket.status}\n"
                f"📅 Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"💬 Question: {question}\n"
            )
            
            keyboard = [[
                InlineKeyboardButton(
                    f"📝 Reply to #{ticket.ticket_number}", 
                    callback_data=f"reply_{ticket.ticket_number}"
                ),
                InlineKeyboardButton(
                    "🟡 Mark In Progress" if ticket.status == 'open' else "✅ Already In Progress",
                    callback_data=f"progress_{ticket.ticket_number}" if ticket.status == 'open' else "noop"
                )
            ]]
            
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in show_pending: {e}")
        await update.message.reply_text(f"Error showing pending tickets: {str(e)}")

async def search_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search tickets"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🔍 **Search Help**\n\n"
                "Usage: /search <search term>\n\n"
                "Examples:\n"
                "/search john (search by name)\n"
                "/search @username (search by username)\n"
                "/search TKT-20240313 (search by ticket number)\n"
                "/search 123456789 (search by user ID)",
                parse_mode='Markdown'
            )
            return
        
        search_term = ' '.join(context.args).strip()
        search_term_clean = search_term.replace('@', '').upper()
        
        results = []
        
        # Search by ticket number
        if search_term_clean.startswith('TKT-'):
            ticket = db_session.query(Ticket).filter_by(ticket_number=search_term_clean).first()
            if ticket:
                results.append(('ticket', ticket))
        
        # Search by user ID
        elif search_term.isdigit():
            user = db_session.query(User).filter_by(user_id=int(search_term)).first()
            if user:
                results.append(('user', user))
        
        # Search by username or name
        else:
            users = db_session.query(User).filter(
                (User.username.ilike(f"%{search_term_clean}%")) |
                (User.name.ilike(f"%{search_term}%")) |
                (User.email.ilike(f"%{search_term}%"))
            ).all()
            for user in users:
                results.append(('user', user))
        
        if not results:
            await update.message.reply_text(f"❌ No results found for '{search_term}'")
            return
        
        for result_type, item in results[:3]:  # Limit to 3 results
            if result_type == 'ticket':
                user = db_session.query(User).filter_by(user_id=item.user_id).first()
                text = (
                    f"🎫 **Ticket #{item.ticket_number}**\n"
                    f"👤 User: {user.name or 'N/A'} (@{user.username or 'N/A'})\n"
                    f"📋 Category: {item.category}\n"
                    f"📊 Status: {item.status}\n"
                    f"📅 Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"💬 Question: {item.question[:200]}"
                )
                keyboard = [[
                    InlineKeyboardButton("📝 Reply", callback_data=f"reply_{item.ticket_number}")
                ]]
                await update.message.reply_text(
                    text, 
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            
            else:  # user
                user_tickets = db_session.query(Ticket).filter_by(user_id=item.user_id).count()
                text = (
                    f"👤 **User: {item.name or 'N/A'}**\n"
                    f"🆔 ID: `{item.user_id}`\n"
                    f"📧 Email: {item.email or 'N/A'}\n"
                    f"📱 Phone: {item.phone or 'N/A'}\n"
                    f"🎫 Total Tickets: {user_tickets}\n"
                    f"📅 Joined: {item.created_at.strftime('%Y-%m-%d')}"
                )
                await update.message.reply_text(text, parse_mode='Markdown')
                
    except Exception as e:
        logger.error(f"Error in search_tickets: {e}")
        await update.message.reply_text(f"Error searching: {str(e)}")

async def quick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick reply to ticket using /reply command"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /reply <ticket_number> <message>\n"
                "Example: /reply TKT-20240313090956 Thank you for contacting support"
            )
            return
        
        ticket_number = context.args[0].upper()
        reply_text = ' '.join(context.args[1:])
        
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if not ticket:
            await update.message.reply_text(f"❌ Ticket #{ticket_number} not found.")
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
            logger.error(f"Failed to send to user: {e}")
            await update.message.reply_text(f"✅ Reply saved but user cannot be reached. Ticket #{ticket_number} closed.")
            
    except Exception as e:
        logger.error(f"Error in quick_reply: {e}")
        await update.message.reply_text(f"Error sending reply: {str(e)}")

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export all data"""
    try:
        await update.message.reply_text("📥 Generating export, please wait...")
        
        tickets = db_session.query(Ticket).order_by(Ticket.created_at.desc()).all()
        data = []
        
        for ticket in tickets:
            user = db_session.query(User).filter_by(user_id=ticket.user_id).first()
            last_reply = ticket.replies[-1] if ticket.replies else None
            
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
                'Last Reply': last_reply.message if last_reply else '',
                'Replied By': last_reply.admin_username if last_reply else '',
                'Created': ticket.created_at.strftime('%Y-%m-%d %H:%M'),
                'Updated': ticket.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        filename = f"tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        await update.message.reply_document(
            document=output,
            filename=filename,
            caption=f"✅ Exported {len(tickets)} tickets"
        )
    except Exception as e:
        logger.error(f"Error in export_data: {e}")
        await update.message.reply_text(f"Error exporting data: {str(e)}")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin_group(query.message.chat.id):
        await query.edit_message_text("This action is only allowed in admin group.")
        return
    
    data = query.data
    logger.info(f"Admin callback: {data}")
    
    try:
        if data == "admin_stats":
            await show_stats(update, context)
            await query.message.delete()
        
        elif data == "admin_pending":
            await show_pending(update, context)
            await query.message.delete()
        
        elif data == "admin_search":
            await query.edit_message_text(
                "🔍 Use /search command with your search term.\n\n"
                "Example: /search @username\n"
                "Example: /search TKT-20240313"
            )
        
        elif data == "admin_download":
            await export_data(update, context)
            await query.message.delete()
        
        elif data.startswith("reply_"):
            ticket_number = data.replace("reply_", "")
            context.user_data['replying_to_ticket'] = ticket_number
            await query.edit_message_text(
                f"📝 Please type your reply for ticket #{ticket_number}:\n\n"
                f"(Just send the message, no command needed)"
            )
        
        elif data.startswith("progress_"):
            ticket_number = data.replace("progress_", "")
            ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
            if ticket and ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.updated_at = datetime.utcnow()
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
            else:
                await query.edit_message_text(f"Ticket #{ticket_number} is already in progress or closed.")
        
        elif data == "noop":
            # Do nothing button
            pass
            
    except Exception as e:
        logger.error(f"Error in admin_callback_handler: {e}")
        await query.edit_message_text(f"Error: {str(e)}")

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin replies to tickets from button clicks"""
    if not is_admin_group(update.effective_chat.id):
        return
    
    ticket_number = context.user_data.get('replying_to_ticket')
    if not ticket_number:
        return
    
    try:
        reply_text = update.message.text
        logger.info(f"Admin replying to ticket {ticket_number}: {reply_text[:50]}...")
        
        ticket = db_session.query(Ticket).filter_by(ticket_number=ticket_number).first()
        if not ticket:
            await update.message.reply_text("❌ Ticket not found.")
            context.user_data.pop('replying_to_ticket', None)
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
            await update.message.reply_text(f"✅ Reply sent. Ticket #{ticket_number} closed.")
        except Exception as e:
            logger.error(f"Failed to send to user: {e}")
            await update.message.reply_text(f"✅ Reply saved but user cannot be reached. Ticket #{ticket_number} closed.")
        
        context.user_data.pop('replying_to_ticket', None)
        
    except Exception as e:
        logger.error(f"Error in admin_reply_handler: {e}")
        await update.message.reply_text(f"Error sending reply: {str(e)}")
        context.user_data.pop('replying_to_ticket', None)
