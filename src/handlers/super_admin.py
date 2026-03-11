# src/handlers/super_admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime
import io
import csv

from src.database import db
from src.config import config
from src.keyboards import (
    get_super_admin_keyboard, get_export_keyboard,
    get_admin_management_keyboard, get_group_management_keyboard
)
from src.utils import (
    format_statistics, create_excel_export, escape_html
)
from src.backup import BackupManager

logger = logging.getLogger(__name__)

# Conversation states
ADD_ADMIN_ID = 0
REMOVE_ADMIN_ID = 1
ADD_GROUP_ID = 2
REMOVE_GROUP_ID = 3
BROADCAST_TEXT = 4

class SuperAdminHandlers:
    
    @staticmethod
    async def check_super_admin(update: Update) -> bool:
        """Check if user is super admin"""
        user_id = update.effective_user.id
        return user_id in config.SUPER_ADMIN_IDS or db.is_super_admin(user_id)
    
    @staticmethod
    async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /panel command - Super admin panel"""
        if not await SuperAdminHandlers.check_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        await update.message.reply_text(
            "👑 <b>Super Admin Control Panel</b>\n\n"
            "Welcome to the master control panel. Select an option below:",
            reply_markup=get_super_admin_keyboard(),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle super admin callback queries"""
        query = update.callback_query
        await query.answer()
        
        if not await SuperAdminHandlers.check_super_admin(update):
            await query.edit_message_text("❌ You are not authorized.")
            return
        
        data = query.data
        
        if data == 'sa_stats':
            stats = db.get_statistics()
            text = format_statistics(stats)
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data='sa_back')
                ]]),
                parse_mode='HTML'
            )
        
        elif data == 'sa_all_tickets':
            tickets = db.get_all_tickets(limit=100)
            
            if tickets:
                text = "📋 <b>All Tickets (Last 100)</b>\n\n"
                for ticket in tickets:
                    status_emoji = config.STATUS_EMOJIS.get(ticket.status, '⚪')
                    user = db.get_user(ticket.user_id)
                    username = f"@{user.username}" if user and user.username else "N/A"
                    text += f"{status_emoji} <code>{ticket.ticket_id}</code> - {username}\n"
                    text += f"   Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            else:
                text = "📭 No tickets found."
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data='sa_back')
                ]]),
                parse_mode='HTML'
            )
        
        elif data == 'sa_manage_admins':
            admins = db.get_all_admins()
            
            text = "👥 <b>Admin List</b>\n\n"
            for admin in admins:
                text += f"• ID: <code>{admin.user_id}</code>\n"
                text += f"  Username: @{admin.username}\n"
                text += f"  Added: {admin.added_at.strftime('%Y-%m-%d')}\n"
                text += f"  Super: {'✅' if admin.is_super_admin else '❌'}\n"
                text += f"  Tickets: {admin.tickets_handled}\n\n"
            
            await query.edit_message_text(
                text,
                reply_markup=get_admin_management_keyboard(),
                parse_mode='HTML'
            )
        
        elif data == 'sa_manage_groups':
            groups = db.get_allowed_groups()
            
            text = "👥 <b>Allowed Groups</b>\n\n"
            for group in groups:
                text += f"• Group ID: <code>{group.group_id}</code>\n"
                text += f"  Title: {escape_html(group.group_title)}\n"
                text += f"  Added: {group.added_at.strftime('%Y-%m-%d')}\n\n"
            
            await query.edit_message_text(
                text,
                reply_markup=get_group_management_keyboard(),
                parse_mode='HTML'
            )
        
        elif data == 'add_admin':
            await query.edit_message_text(
                "📝 <b>Add New Admin</b>\n\n"
                "Send me the user ID of the new admin:",
                parse_mode='HTML'
            )
            return ADD_ADMIN_ID
        
        elif data == 'remove_admin':
            await query.edit_message_text(
                "📝 <b>Remove Admin</b>\n\n"
                "Send me the user ID of the admin to remove:",
                parse_mode='HTML'
            )
            return REMOVE_ADMIN_ID
        
        elif data == 'list_admins':
            admins = db.get_all_admins()
            
            text = "👥 <b>Admin List</b>\n\n"
            for admin in admins:
                text += f"• ID: <code>{admin.user_id}</code> - @{admin.username}\n"
                text += f"  Added: {admin.added_at.strftime('%Y-%m-%d')}\n"
                text += f"  Status: {'✅ Active' if admin.is_active else '❌ Inactive'}\n\n"
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data='sa_manage_admins')
                ]]),
                parse_mode='HTML'
            )
        
        elif data == 'add_group':
            await query.edit_message_text(
                "📝 <b>Add Group</b>\n\n"
                "Send me the group ID to add:",
                parse_mode='HTML'
            )
            return ADD_GROUP_ID
        
        elif data == 'remove_group':
            await query.edit_message_text(
                "📝 <b>Remove Group</b>\n\n"
                "Send me the group ID to remove:",
                parse_mode='HTML'
            )
            return REMOVE_GROUP_ID
        
        elif data == 'list_groups':
            groups = db.get_allowed_groups()
            
            text = "👥 <b>Allowed Groups</b>\n\n"
            for group in groups:
                text += f"• Group ID: <code>{group.group_id}</code>\n"
                text += f"  Title: {escape_html(group.group_title)}\n"
                text += f"  Added: {group.added_at.strftime('%Y-%m-%d')}\n\n"
            
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data='sa_manage_groups')
                ]]),
                parse_mode='HTML'
            )
        
        elif data == 'sa_export':
            await query.edit_message_text(
                "📤 <b>Export Data</b>\n\n"
                "Select the type of data to export:",
                reply_markup=get_export_keyboard(),
                parse_mode='HTML'
            )
        
        elif data == 'export_users':
            users = db.get_all_users()
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['User ID', 'Username', 'Full Name', 'Email', 'Phone', 'Registered', 'Total Tickets'])
            
            for user in users:
                writer.writerow([
                    user.user_id,
                    user.username,
                    user.full_name,
                    user.email,
                    user.phone,
                    user.registered_at,
                    user.total_tickets
                ])
            
            output.seek(0)
            
            await query.message.reply_document(
                document=io.BytesIO(output.getvalue().encode()),
                filename=f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                caption="✅ Users export completed!"
            )
        
        elif data == 'export_tickets':
            tickets = db.get_all_tickets(limit=5000)
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Ticket ID', 'User ID', 'Category', 'Question', 'Admin Reply', 
                           'Status', 'Created', 'Closed', 'Assigned To'])
            
            for ticket in tickets:
                writer.writerow([
                    ticket.ticket_id,
                    ticket.user_id,
                    ticket.category,
                    ticket.question,
                    ticket.admin_reply,
                    ticket.status,
                    ticket.created_at,
                    ticket.closed_at,
                    ticket.assigned_to
                ])
            
            output.seek(0)
            
            await query.message.reply_document(
                document=io.BytesIO(output.getvalue().encode()),
                filename=f'tickets_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                caption="✅ Tickets export completed!"
            )
        
        elif data == 'export_complete':
            users = db.get_all_users()
            tickets = db.get_all_tickets(limit=5000)
            
            excel_data = create_excel_export(users, tickets)
            
            await query.message.reply_document(
                document=io.BytesIO(excel_data),
                filename=f'complete_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                caption="✅ Complete export completed!"
            )
        
        elif data == 'sa_broadcast':
            await query.edit_message_text(
                "📢 <b>Broadcast Message</b>\n\n"
                "Send me the message you want to broadcast to all users:",
                parse_mode='HTML'
            )
            return BROADCAST_TEXT
        
        elif data == 'sa_backup':
            await query.edit_message_text(
                "💾 <b>Creating backup...</b>\n\n"
                "Please wait, this may take a moment.",
                parse_mode='HTML'
            )
            
            # Create backup
            backup_file = BackupManager.create_backup()
            
            if backup_file:
                await query.message.reply_document(
                    document=open(backup_file, 'rb'),
                    filename=f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql',
                    caption="✅ Backup created successfully!"
                )
                
                # Save backup record
                import os
                db.save_backup_record(
                    filename=os.path.basename(backup_file),
                    size=os.path.getsize(backup_file)
                )
            else:
                await query.message.reply_text("❌ Backup failed.")
        
        elif data == 'sa_settings':
            settings_text = f"""
⚙️ <b>System Settings</b>

<b>Bot Configuration:</b>
• Bot Username: {config.BOT_USERNAME}
• Admin Group: <code>{config.ADMIN_GROUP_ID}</code>
• Backup Group: <code>{config.BACKUP_GROUP_ID}</code>

<b>Backup Settings:</b>
• Auto Backup: {'✅ Enabled' if config.ENABLE_AUTO_BACKUP else '❌ Disabled'}
• Backup Interval: {config.BACKUP_INTERVAL_HOURS} hours

<b>Support Settings:</b>
• Company: {config.COMPANY_NAME}
• Support Email: {config.SUPPORT_EMAIL}
"""
            
            await query.edit_message_text(
                settings_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data='sa_back')
                ]]),
                parse_mode='HTML'
            )
        
        elif data == 'sa_back':
            await query.edit_message_text(
                "👑 <b>Super Admin Control Panel</b>\n\n"
                "Welcome back to the master control panel.",
                reply_markup=get_super_admin_keyboard(),
                parse_mode='HTML'
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def handle_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle adding new admin"""
        if not await SuperAdminHandlers.check_super_admin(update):
            return ConversationHandler.END
        
        try:
            admin_id = int(update.message.text.strip())
            
            # Get user info
            try:
                chat = await context.bot.get_chat(admin_id)
                username = chat.username or "NoUsername"
            except:
                username = "Unknown"
            
            db.add_admin(admin_id, username, update.effective_user.id)
            
            await update.message.reply_text(
                f"✅ Admin {admin_id} (@{username}) added successfully!"
            )
            
            # Log action
            db.log_action(
                update.effective_user.id,
                'add_admin',
                {'admin_id': admin_id, 'username': username}
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please send a number.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
        return ConversationHandler.END
    
    @staticmethod
    async def handle_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle removing admin"""
        if not await SuperAdminHandlers.check_super_admin(update):
            return ConversationHandler.END
        
        try:
            admin_id = int(update.message.text.strip())
            
            if admin_id in config.SUPER_ADMIN_IDS:
                await update.message.reply_text("❌ Cannot remove super admin.")
                return ConversationHandler.END
            
            db.remove_admin(admin_id)
            
            await update.message.reply_text(
                f"✅ Admin {admin_id} removed successfully."
            )
            
            # Log action
            db.log_action(
                update.effective_user.id,
                'remove_admin',
                {'admin_id': admin_id}
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please send a number.")
        
        return ConversationHandler.END
    
    @staticmethod
    async def handle_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle adding group"""
        if not await SuperAdminHandlers.check_super_admin(update):
            return ConversationHandler.END
        
        try:
            group_id = int(update.message.text.strip())
            
            # Try to get group info
            try:
                chat = await context.bot.get_chat(group_id)
                group_title = chat.title or "Unknown Group"
            except:
                group_title = "Unknown Group"
            
            db.add_allowed_group(group_id, group_title, update.effective_user.id)
            
            await update.message.reply_text(
                f"✅ Group {group_id} ({group_title}) added successfully!"
            )
            
            # Log action
            db.log_action(
                update.effective_user.id,
                'add_group',
                {'group_id': group_id, 'title': group_title}
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Please send a number.")
        
        return ConversationHandler.END
    
    @staticmethod
    async def handle_remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle removing group"""
        if not await SuperAdminHandlers.check_super_admin(update):
            return ConversationHandler.END
        
        try:
            group_id = int(update.message.text.strip())
            
            db.remove_allowed_group(group_id)
            
            await update.message.reply_text(
                f"✅ Group {group_id} removed successfully."
            )
            
            # Log action
            db.log_action(
                update.effective_user.id,
                'remove_group',
                {'group_id': group_id}
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Please send a number.")
        
        return ConversationHandler.END
    
    @staticmethod
    async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast message"""
        if not await SuperAdminHandlers.check_super_admin(update):
            return ConversationHandler.END
        
        message = update.message.text
        users = db.get_all_users()
        
        await update.message.reply_text(
            f"📢 Broadcasting to {len(users)} users...\n\n"
            f"This may take a while."
        )
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.user_id,
                    text=message,
                    parse_mode='HTML'
                )
                success += 1
            except:
                failed += 1
            
            # Small delay to avoid flood limits
            import asyncio
            await asyncio.sleep(0.05)
        
        await update.message.reply_text(
            f"✅ Broadcast completed!\n"
            f"✓ Sent: {success}\n"
            f"✗ Failed: {failed}"
        )
        
        # Log action
        db.log_action(
            update.effective_user.id,
            'broadcast',
            {'total': len(users), 'success': success, 'failed': failed}
        )
        
        return ConversationHandler.END
