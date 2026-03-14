from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from utils.helpers import parse_time_string
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class SuperAdminHandlers:
    def __init__(self, db: Database):
        self.db = db
        # Store filters and preset links
        self.filters = {}  # Dictionary to store custom commands
    
    async def is_super_admin(self, update: Update) -> bool:
        from config import Config
        return update.effective_user.id == Config.SUPER_ADMIN_ID
    
    # Existing methods...
    async def activate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activate a group for /support command"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Usage:** `/activate <group_id>`\n\n"
                "Get group ID by:\n"
                "1. Add @getidsbot to your group\n"
                "2. Send any message\n"
                "3. Bot will show group ID",
                parse_mode='Markdown'
            )
            return
        
        try:
            group_id = int(context.args[0])
            
            # Test if bot can send message to the group
            try:
                await context.bot.send_message(
                    group_id,
                    "✅ **This group has been activated for ToonPay Support!**\n\n"
                    "Users can now use /support command here.",
                    parse_mode='Markdown'
                )
                
                # Save to database
                self.db.activate_group(group_id, update.effective_user.id)
                
                await update.message.reply_text(
                    f"✅ Group `{group_id}` activated successfully!\n\n"
                    f"Users can now use /support in that group.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ **Failed to activate group**\n\n"
                    f"Make sure I'm an admin in that group!\n"
                    f"Error: {str(e)}",
                    parse_mode='Markdown'
                )
                
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    
    async def deactivate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deactivate a group"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("📝 **Usage:** `/deactivate <group_id>`", parse_mode='Markdown')
            return
        
        try:
            group_id = int(context.args[0])
            self.db.deactivate_group(group_id)
            await update.message.reply_text(
                f"✅ Group `{group_id}` deactivated successfully.",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    
    async def list_activated_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all activated groups"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        groups = self.db.get_activated_groups()
        if groups:
            message = "📋 **Activated Groups:**\n\n"
            for group_id in groups:
                message += f"• `{group_id}`\n"
            message += f"\nTotal: {len(groups)} groups"
        else:
            message = "📭 No activated groups.\n\nUse `/activate <group_id>` to add one."
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    # NEW: Updated delete_data method with minutes support
    async def delete_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete old ticket data (supports days, hours, minutes)"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Usage:** `/deletedata <value><unit>`\n\n"
                "Examples:\n"
                "• `/deletedata 30d` - deletes tickets older than 30 days\n"
                "• `/deletedata 12h` - deletes tickets older than 12 hours\n"
                "• `/deletedata 45m` - deletes tickets older than 45 minutes\n"
                "• `/deletedata 7 days` - also works with full words",
                parse_mode='Markdown'
            )
            return
        
        try:
            time_input = ' '.join(context.args)
            delta = parse_time_string(time_input)
            
            # Convert to days for database (with decimal support)
            days = delta.total_seconds() / 86400  # Convert to days
            
            deleted = self.db.delete_old_data(days)
            
            # Format output nicely
            if delta.days > 0:
                time_str = f"{delta.days} days"
            elif delta.seconds >= 3600:
                time_str = f"{delta.seconds // 3600} hours"
            else:
                time_str = f"{delta.seconds // 60} minutes"
            
            await update.message.reply_text(
                f"✅ Deleted `{deleted}` tickets older than {time_str}.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error deleting data: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # NEW: Add custom filter/command
    async def add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a custom command that returns a link or text"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "📝 **Usage:** `/addfilter <command> <link or text>`\n\n"
                "Examples:\n"
                "• `/addfilter presale https://t.me/presale_link`\n"
                "• `/addfilter rules Please read our rules...`\n"
                "• `/addfilter website https://toonpay.com`",
                parse_mode='Markdown'
            )
            return
        
        command = context.args[0].lower().strip('/')
        content = ' '.join(context.args[1:])
        
        # Store in database (you'll need to add this method)
        self.db.add_custom_command(command, content, update.effective_user.id)
        
        await update.message.reply_text(
            f"✅ **Custom command added!**\n\n"
            f"Command: `/{command}`\n"
            f"Content: {content[:100]}{'...' if len(content) > 100 else ''}",
            parse_mode='Markdown'
        )
    
    # NEW: Remove custom filter
    async def remove_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a custom command"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Usage:** `/removefilter <command>`\n\n"
                "Example: `/removefilter presale`",
                parse_mode='Markdown'
            )
            return
        
        command = context.args[0].lower().strip('/')
        
        if self.db.remove_custom_command(command):
            await update.message.reply_text(
                f"✅ Command `/{command}` removed successfully.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Command `/{command}` not found.",
                parse_mode='Markdown'
            )
    
    # NEW: List all custom filters
    async def list_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all custom commands"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        commands = self.db.get_custom_commands()
        
        if not commands:
            await update.message.reply_text("📭 No custom commands added yet.")
            return
        
        message = "📋 **Custom Commands:**\n\n"
        for cmd in commands:
            message += f"• `/{cmd['command']}` - {cmd['content'][:50]}...\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    # NEW: Broadcast message to all users
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to all users"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast` to send it to all users.\n\n"
                "You can broadcast:\n"
                "• Text messages\n"
                "• Images with captions\n"
                "• Videos with captions\n"
                "• GIFs\n"
                "• Any media type",
                parse_mode='Markdown'
            )
            return
        
        # Get all users
        users = self.db.get_all_users()
        if not users:
            await update.message.reply_text("📭 No users found to broadcast to.")
            return
        
        status_msg = await update.message.reply_text(
            f"📤 **Broadcasting to {len(users)} users...**\n"
            f"⏳ Please wait...",
            parse_mode='Markdown'
        )
        
        success_count = 0
        fail_count = 0
        
        # Get the message to broadcast
        broadcast_msg = update.message.reply_to_message
        
        for user in users:
            try:
                if broadcast_msg.photo:
                    # Send photo with caption
                    await context.bot.send_photo(
                        chat_id=user['user_id'],
                        photo=broadcast_msg.photo[-1].file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.video:
                    # Send video with caption
                    await context.bot.send_video(
                        chat_id=user['user_id'],
                        video=broadcast_msg.video.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.animation:
                    # Send GIF/animation
                    await context.bot.send_animation(
                        chat_id=user['user_id'],
                        animation=broadcast_msg.animation.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.document:
                    # Send document
                    await context.bot.send_document(
                        chat_id=user['user_id'],
                        document=broadcast_msg.document.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                else:
                    # Send text message
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=broadcast_msg.text or "Broadcast message"
                    )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user['user_id']}: {e}")
                fail_count += 1
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(0.05)
        
        await status_msg.edit_text(
            f"📊 **Broadcast Complete**\n\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {fail_count}\n"
            f"📈 Total: {len(users)}",
            parse_mode='Markdown'
        )
    
    # NEW: Comprehensive statistics
    async def all_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get comprehensive statistics about all users"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Get all users with their ticket stats
        users_stats = self.db.get_all_users_with_stats()
        
        # Overall statistics
        total_users = len(users_stats)
        total_tickets = sum(u['total_tickets'] for u in users_stats)
        total_solved = sum(u['solved_tickets'] for u in users_stats)
        total_in_progress = sum(u['in_progress_tickets'] for u in users_stats)
        total_spam = sum(u['spam_tickets'] for u in users_stats)
        
        # Users who only started bot but never created ticket
        inactive_users = [u for u in users_stats if u['total_tickets'] == 0]
        
        # Overall stats message
        overall = f"""📊 **Complete Bot Statistics**

**Overview:**
👥 **Total Users:** {total_users}
🎫 **Total Tickets:** {total_tickets}
✅ **Solved Tickets:** {total_solved}
🔄 **In Progress:** {total_in_progress}
🚫 **Spam Tickets:** {total_spam}
📭 **Inactive Users:** {len(inactive_users)} (started bot but no tickets)

"""
        
        await update.message.reply_text(overall, parse_mode='Markdown')
        
        # Individual user stats
        if users_stats:
            await update.message.reply_text(
                "📋 **User Details:**\n\n"
                "_(Sending detailed list...)_",
                parse_mode='Markdown'
            )
            
            # Send users in batches to avoid message too long error
            batch = ""
            for user in users_stats:
                user_info = f"""**Name:** {user['name']}
**Username:** @{user['username'] or 'N/A'}
**User ID:** `{user['user_id']}`
**Registered:** {user['created_at'].strftime('%Y-%m-%d %H:%M')}
**Status:** {'✅ Active' if user['total_tickets'] > 0 else '📭 Inactive'}
**Tickets:** Total: {user['total_tickets']} | ✅ Solved: {user['solved_tickets']} | 🔄 In Progress: {user['in_progress_tickets']} | 🚫 Spam: {user['spam_tickets']}
─────────────────────
"""
                
                if len(batch) + len(user_info) > 4000:
                    await update.message.reply_text(batch, parse_mode='Markdown')
                    batch = user_info
                else:
                    batch += user_info
            
            if batch:
                await update.message.reply_text(batch, parse_mode='Markdown')
        else:
            await update.message.reply_text("📭 No users found.")
