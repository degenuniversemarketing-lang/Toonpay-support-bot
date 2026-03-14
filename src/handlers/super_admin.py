import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.models import User, Ticket, Group, AdminAction
from src.database import db_session
from src.config import Config
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a group for bot support (super admin only)"""
    if not context.args:
        await update.message.reply_text("Usage: /add <group_id>")
        return
    
    try:
        group_id = int(context.args[0])
        
        # Check if group already exists
        group = db_session.query(Group).filter_by(group_id=group_id).first()
        if group:
            group.is_active = True
            group.added_by = update.effective_user.id
            group.added_at = datetime.utcnow()
            await update.message.reply_text(f"✅ Group {group_id} reactivated!")
        else:
            # Get group info
            try:
                chat = await context.bot.get_chat(group_id)
                group_title = chat.title
            except:
                group_title = "Unknown"
            
            group = Group(
                group_id=group_id,
                group_title=group_title,
                is_active=True,
                added_by=update.effective_user.id
            )
            db_session.add(group)
            await update.message.reply_text(f"✅ Group {group_id} ({group_title}) added successfully!")
        
        db_session.commit()
        
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID. Please provide a numeric ID.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a group (super admin only)"""
    if not context.args:
        await update.message.reply_text("Usage: /remove <group_id>")
        return
    
    try:
        group_id = int(context.args[0])
        
        group = db_session.query(Group).filter_by(group_id=group_id).first()
        if group:
            group.is_active = False
            db_session.commit()
            await update.message.reply_text(f"✅ Group {group_id} removed successfully!")
        else:
            await update.message.reply_text("❌ Group not found!")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID. Please provide a numeric ID.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def get_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get bot statistics (super admin only)"""
    total_users = db_session.query(User).count()
    total_tickets = db_session.query(Ticket).count()
    new_tickets = db_session.query(Ticket).filter_by(status='new').count()
    in_progress = db_session.query(Ticket).filter_by(status='in_progress').count()
    closed_tickets = db_session.query(Ticket).filter_by(status='closed').count()
    
    # Tickets in last 24 hours
    last_24h = datetime.utcnow() - timedelta(days=1)
    recent_tickets = db_session.query(Ticket).filter(Ticket.created_at >= last_24h).count()
    
    # Active groups
    active_groups = db_session.query(Group).filter_by(is_active=True).count()
    
    stats_text = (
        "📊 **Bot Statistics**\n\n"
        f"👥 **Total Users:** {total_users}\n"
        f"🎫 **Total Tickets:** {total_tickets}\n"
        f"🆕 **New Tickets:** {new_tickets}\n"
        f"⏳ **In Progress:** {in_progress}\n"
        f"✅ **Closed Tickets:** {closed_tickets}\n"
        f"📈 **Tickets (24h):** {recent_tickets}\n"
        f"👥 **Active Groups:** {active_groups}\n\n"
        f"Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot settings panel for super admin"""
    keyboard = [
        [InlineKeyboardButton("📊 View Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Manage Groups", callback_data="admin_groups")],
        [InlineKeyboardButton("📝 Edit Categories", callback_data="admin_categories")],
        [InlineKeyboardButton("📤 Export All Data", callback_data="admin_export")],
        [InlineKeyboardButton("🔧 Bot Configuration", callback_data="admin_config")]
    ]
    
    await update.message.reply_text(
        "⚙️ **Super Admin Panel**\n\n"
        "Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
