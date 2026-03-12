from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from src.database import db_session
from src.models import AllowedGroup, User, Ticket
from src.utils.decorators import super_admin_only, private_chat_only
from src.config import Config
import logging
import asyncio  # FIXED: Added missing import
from datetime import datetime, timedelta
import json
from io import BytesIO

logger = logging.getLogger(__name__)

@super_admin_only
@private_chat_only
async def super_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Super admin control panel"""
    text = (
        "👑 **Super Admin Control Panel**\n\n"
        "**Group Management:**\n"
        "/addgroup <group_id> - Add allowed group\n"
        "/removegroup <group_id> - Remove allowed group\n"
        "/listgroups - List all allowed groups\n\n"
        "**Bot Management:**\n"
        "/broadcast <message> - Send message to all users\n"
        "/superstats - Detailed statistics\n"
        "/backup - Backup database\n\n"
        "**Category Management:**\n"
        "/categories - List all categories"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

@super_admin_only
@private_chat_only
async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a group to allowed list"""
    if not context.args:
        await update.message.reply_text("Usage: /addgroup <group_id>")
        return
    
    try:
        group_id = int(context.args[0])
        
        # Check if already exists
        existing = db_session.query(AllowedGroup).filter_by(group_id=group_id).first()
        if existing:
            if not existing.is_active:
                existing.is_active = True
                db_session.commit()
                await update.message.reply_text(f"✅ Group {group_id} reactivated.")
            else:
                await update.message.reply_text(f"⚠️ Group {group_id} is already allowed.")
            return
        
        # Get group info
        try:
            chat = await context.bot.get_chat(group_id)
            group_title = chat.title
        except:
            group_title = "Unknown"
        
        new_group = AllowedGroup(
            group_id=group_id,
            group_title=group_title,
            added_by=update.effective_user.id
        )
        
        db_session.add(new_group)
        db_session.commit()
        
        await update.message.reply_text(f"✅ Group '{group_title}' ({group_id}) added to allowed list.")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

@super_admin_only
@private_chat_only
async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a group from allowed list"""
    if not context.args:
        await update.message.reply_text("Usage: /removegroup <group_id>")
        return
    
    try:
        group_id = int(context.args[0])
        group = db_session.query(AllowedGroup).filter_by(group_id=group_id).first()
        
        if group:
            group.is_active = False
            db_session.commit()
            await update.message.reply_text(f"✅ Group {group_id} removed from allowed list.")
        else:
            await update.message.reply_text(f"❌ Group {group_id} not found in allowed list.")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID. Must be a number.")

@super_admin_only
@private_chat_only
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all allowed groups"""
    groups = db_session.query(AllowedGroup).filter_by(is_active=True).all()
    
    if not groups:
        await update.message.reply_text("No groups are currently allowed.")
        return
    
    text = "📋 **Allowed Groups:**\n\n"
    for group in groups:
        text += f"• {group.group_title} - `{group.group_id}`\n"
        text += f"  Added: {group.added_at.strftime('%Y-%m-%d')}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

@super_admin_only
@private_chat_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    
    # Get all users
    users = db_session.query(User).all()
    total = len(users)
    successful = 0
    failed = 0
    
    await update.message.reply_text(f"📢 Broadcasting to {total} users...")
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.user_id,
                text=f"📢 **Announcement:**\n\n{message}"
            )
            successful += 1
        except:
            failed += 1
        
        # Small delay to avoid flood limits
        await asyncio.sleep(0.05)
    
    await update.message.reply_text(
        f"✅ Broadcast complete!\n"
        f"Total: {total}\n"
        f"Success: {successful}\n"
        f"Failed: {failed}"
    )

@super_admin_only
@private_chat_only
async def super_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed statistics for super admin"""
    from datetime import datetime, timedelta
    
    # Basic counts
    total_users = db_session.query(User).count()
    total_tickets = db_session.query(Ticket).count()
    
    # Active users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = db_session.query(User).filter(User.last_active >= week_ago).count()
    
    # Tickets by status
    open_tickets = db_session.query(Ticket).filter_by(status='open').count()
    in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
    closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
    
    # Tickets by category
    categories = {}
    for cat_key, cat_name in Config.CATEGORIES.items():
        count = db_session.query(Ticket).filter_by(category=cat_key).count()
        categories[cat_name] = count
    
    # Daily ticket stats (last 7 days)
    daily_stats = []
    for i in range(7):
        day = datetime.utcnow().date() - timedelta(days=i)
        count = db_session.query(Ticket).filter(
            Ticket.created_at >= day,
            Ticket.created_at < day + timedelta(days=1)
        ).count()
        daily_stats.append(f"{day.strftime('%m/%d')}: {count}")
    
    text = (
        f"📊 **Super Admin Statistics**\n\n"
        f"**Users:**\n"
        f"Total: {total_users}\n"
        f"Active (7d): {active_users}\n\n"
        f"**Tickets:**\n"
        f"Total: {total_tickets}\n"
        f"🟢 Open: {open_tickets}\n"
        f"🟡 In Progress: {in_progress}\n"
        f"🔴 Closed: {closed_tickets}\n\n"
        f"**Categories:**\n"
    )
    
    for cat_name, count in categories.items():
        text += f"• {cat_name}: {count}\n"
    
    text += f"\n**Daily Tickets (Last 7 days):**\n"
    text += '\n'.join(reversed(daily_stats))
    
    await update.message.reply_text(text, parse_mode='Markdown')

@super_admin_only
@private_chat_only
async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create database backup"""
    await update.message.reply_text("🔄 Creating backup...")
    
    # Export users
    users = db_session.query(User).all()
    users_data = []
    for user in users:
        users_data.append({
            'user_id': user.user_id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    
    # Export tickets
    tickets = db_session.query(Ticket).all()
    tickets_data = []
    for ticket in tickets:
        tickets_data.append({
            'ticket_number': ticket.ticket_number,
            'user_id': ticket.user_id,
            'category': ticket.category,
            'question': ticket.question,
            'status': ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status),
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None
        })
    
    backup_data = {
        'users': users_data,
        'tickets': tickets_data,
        'backup_date': datetime.utcnow().isoformat()
    }
    
    # Create file
    backup_file = BytesIO()
    backup_file.write(json.dumps(backup_data, indent=2).encode())
    backup_file.seek(0)
    
    await update.message.reply_document(
        document=backup_file,
        filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        caption="✅ Database backup completed"
    )

@super_admin_only
@private_chat_only
async def manage_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage ticket categories"""
    if not context.args:
        text = "**Category Management:**\n\n"
        text += "Current categories:\n"
        for key, value in Config.CATEGORIES.items():
            text += f"• {key}: {value}\n"
        text += "\nCommands:\n"
        text += "/categories list - List all categories"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    command = context.args[0].lower()
    
    if command == "list":
        text = "**Current Categories:**\n\n"
        for key, value in Config.CATEGORIES.items():
            text += f"• {key}: {value}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("Unknown command. Use /categories to see options.")
