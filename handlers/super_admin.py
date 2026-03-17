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
    
    # ==================== GROUP MANAGEMENT ====================
    
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
                "3. Bot will show group ID"
            )
            return
        
        try:
            group_id = int(context.args[0])
            
            # Test if bot can send message to the group
            try:
                await context.bot.send_message(
                    group_id,
                    "✅ **This group has been activated for ToonPay Support!**\n\n"
                    "Users can now use /support command here."
                )
                
                # Save to database
                self.db.activate_group(group_id, update.effective_user.id)
                
                await update.message.reply_text(
                    f"✅ Group `{group_id}` activated successfully!\n\n"
                    f"Users can now use /support in that group."
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ **Failed to activate group**\n\n"
                    f"Make sure I'm an admin in that group!\n"
                    f"Error: {str(e)}"
                )
                
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    
    async def deactivate_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deactivate a group"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("📝 **Usage:** `/deactivate <group_id>`")
            return
        
        try:
            group_id = int(context.args[0])
            self.db.deactivate_group(group_id)
            await update.message.reply_text(
                f"✅ Group `{group_id}` deactivated successfully."
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
            message = "📋 Activated Groups:\n\n"
            for group_id in groups:
                message += f"• {group_id}\n"
            message += f"\nTotal: {len(groups)} groups"
        else:
            message = "📭 No activated groups.\n\nUse /activate <group_id> to add one."
        
        await update.message.reply_text(message)
    
    # ==================== DATA MANAGEMENT ====================
    
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
                "• `/deletedata 7 days` - also works with full words"
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
                f"✅ Deleted `{deleted}` tickets older than {time_str}."
            )
        except Exception as e:
            logger.error(f"Error deleting data: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # ==================== CUSTOM FILTERS ====================
    
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
                "• `/addfilter website https://toonpay.com`"
            )
            return
        
        command = context.args[0].lower().strip('/')
        content = ' '.join(context.args[1:])
        
        # Store in database
        self.db.add_custom_command(command, content, update.effective_user.id)
        
        await update.message.reply_text(
            f"✅ **Custom command added!**\n\n"
            f"Command: `/{command}`\n"
            f"Content: {content[:100]}{'...' if len(content) > 100 else ''}"
        )
    
    async def remove_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a custom command"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Usage:** `/removefilter <command>`\n\n"
                "Example: `/removefilter presale`"
            )
            return
        
        command = context.args[0].lower().strip('/')
        
        if self.db.remove_custom_command(command):
            await update.message.reply_text(
                f"✅ Command `/{command}` removed successfully."
            )
        else:
            await update.message.reply_text(
                f"❌ Command `/{command}` not found."
            )
    
    async def list_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all custom commands"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        commands = self.db.get_custom_commands()
        
        if not commands:
            await update.message.reply_text("📭 No custom commands added yet.")
            return
        
        message = "📋 Custom Commands:\n\n"
        for cmd in commands:
            # Truncate content if too long
            content = cmd['content'][:50] + "..." if len(cmd['content']) > 50 else cmd['content']
            message += f"• /{cmd['command']} - {content}\n"
        
        await update.message.reply_text(message)
    
    # ==================== USER BROADCAST ====================
    
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
                "• Any media type"
            )
            return
        
        # Get all users
        users = self.db.get_all_users()
        if not users:
            await update.message.reply_text("📭 No users found to broadcast to.")
            return
        
        status_msg = await update.message.reply_text(
            f"📤 **Broadcasting to {len(users)} users...**\n"
            f"⏳ Please wait..."
        )
        
        success_count = 0
        fail_count = 0
        
        # Get the message to broadcast
        broadcast_msg = update.message.reply_to_message
        
        for user in users:
            try:
                if broadcast_msg.photo:
                    await context.bot.send_photo(
                        chat_id=user['user_id'],
                        photo=broadcast_msg.photo[-1].file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.video:
                    await context.bot.send_video(
                        chat_id=user['user_id'],
                        video=broadcast_msg.video.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.animation:
                    await context.bot.send_animation(
                        chat_id=user['user_id'],
                        animation=broadcast_msg.animation.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.document:
                    await context.bot.send_document(
                        chat_id=user['user_id'],
                        document=broadcast_msg.document.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                else:
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
            f"📊 User Broadcast Complete\n\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {fail_count}\n"
            f"📈 Total: {len(users)}"
        )
    
    # ==================== GROUP BROADCAST ====================
    
    async def broadcast_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to all groups where bot is admin"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast_groups` to send it to all groups.\n\n"
                "You can broadcast:\n"
                "• Text messages\n"
                "• Images with captions\n"
                "• Videos with captions\n"
                "• GIFs\n"
                "• Any media type"
            )
            return
        
        # Get all groups from database (admin groups + activated groups)
        admin_groups = self.db.get_admin_groups()
        activated_groups = self.db.get_activated_groups()
        
        # Combine and remove duplicates
        all_groups = list(set(admin_groups + activated_groups))
        
        if not all_groups:
            await update.message.reply_text("📭 No groups found to broadcast to.")
            return
        
        status_msg = await update.message.reply_text(
            f"📤 **Broadcasting to {len(all_groups)} groups...**\n"
            f"⏳ Please wait..."
        )
        
        success_count = 0
        fail_count = 0
        failed_groups = []
        
        # Get the message to broadcast
        broadcast_msg = update.message.reply_to_message
        
        for group_id in all_groups:
            try:
                if broadcast_msg.photo:
                    await context.bot.send_photo(
                        chat_id=group_id,
                        photo=broadcast_msg.photo[-1].file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.video:
                    await context.bot.send_video(
                        chat_id=group_id,
                        video=broadcast_msg.video.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.animation:
                    await context.bot.send_animation(
                        chat_id=group_id,
                        animation=broadcast_msg.animation.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.document:
                    await context.bot.send_document(
                        chat_id=group_id,
                        document=broadcast_msg.document.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                else:
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=broadcast_msg.text or "Broadcast message"
                    )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to group {group_id}: {e}")
                fail_count += 1
                failed_groups.append(str(group_id))
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(0.05)
        
        # Send summary
        summary = f"📊 Group Broadcast Complete\n\n"
        summary += f"✅ Success: {success_count}\n"
        summary += f"❌ Failed: {fail_count}\n"
        summary += f"📈 Total: {len(all_groups)}\n\n"
        
        if failed_groups:
            summary += f"Failed Groups:\n"
            for g in failed_groups[:10]:  # Show first 10 failed groups
                summary += f"• {g}\n"
            if len(failed_groups) > 10:
                summary += f"... and {len(failed_groups) - 10} more"
        
        await status_msg.edit_text(summary)
    
    async def broadcast_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to a specific group"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast_group <group_id>`\n\n"
                "Example: `/broadcast_group -100123456789`"
            )
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Please reply to a message to broadcast."
            )
            return
        
        try:
            group_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
            return
        
        broadcast_msg = update.message.reply_to_message
        
        try:
            if broadcast_msg.photo:
                await context.bot.send_photo(
                    chat_id=group_id,
                    photo=broadcast_msg.photo[-1].file_id,
                    caption=broadcast_msg.caption or ""
                )
            elif broadcast_msg.video:
                await context.bot.send_video(
                    chat_id=group_id,
                    video=broadcast_msg.video.file_id,
                    caption=broadcast_msg.caption or ""
                )
            elif broadcast_msg.animation:
                await context.bot.send_animation(
                    chat_id=group_id,
                    animation=broadcast_msg.animation.file_id,
                    caption=broadcast_msg.caption or ""
                )
            elif broadcast_msg.document:
                await context.bot.send_document(
                    chat_id=group_id,
                    document=broadcast_msg.document.file_id,
                    caption=broadcast_msg.caption or ""
                )
            else:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=broadcast_msg.text or "Broadcast message"
                )
            
            await update.message.reply_text(
                f"✅ Message sent successfully to group `{group_id}`."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to send message to group `{group_id}`.\n\nError: {str(e)}"
            )
    
    # ==================== CHANNEL BROADCAST ====================
    
    async def broadcast_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to all channels where bot is admin"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast_channels` to send it to all channels.\n\n"
                "You can broadcast:\n"
                "• Text messages\n"
                "• Images with captions\n"
                "• Videos with captions\n"
                "• GIFs\n"
                "• Any media type"
            )
            return
        
        # Get all channels from database
        channels = self.db.get_all_channels()
        
        if not channels:
            await update.message.reply_text("📭 No channels found to broadcast to.")
            return
        
        status_msg = await update.message.reply_text(
            f"📤 **Broadcasting to {len(channels)} channels...**\n"
            f"⏳ Please wait..."
        )
        
        success_count = 0
        fail_count = 0
        failed_channels = []
        
        # Get the message to broadcast
        broadcast_msg = update.message.reply_to_message
        
        for channel in channels:
            channel_id = channel['channel_id']
            try:
                if broadcast_msg.photo:
                    await context.bot.send_photo(
                        chat_id=channel_id,
                        photo=broadcast_msg.photo[-1].file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.video:
                    await context.bot.send_video(
                        chat_id=channel_id,
                        video=broadcast_msg.video.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.animation:
                    await context.bot.send_animation(
                        chat_id=channel_id,
                        animation=broadcast_msg.animation.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                elif broadcast_msg.document:
                    await context.bot.send_document(
                        chat_id=channel_id,
                        document=broadcast_msg.document.file_id,
                        caption=broadcast_msg.caption or ""
                    )
                else:
                    await context.bot.send_message(
                        chat_id=channel_id,
                        text=broadcast_msg.text or "Broadcast message"
                    )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to channel {channel_id}: {e}")
                fail_count += 1
                failed_channels.append(str(channel_id))
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(0.05)
        
        # Send summary
        summary = f"📊 Channel Broadcast Complete\n\n"
        summary += f"✅ Success: {success_count}\n"
        summary += f"❌ Failed: {fail_count}\n"
        summary += f"📈 Total: {len(channels)}\n\n"
        
        if failed_channels:
            summary += f"Failed Channels:\n"
            for c in failed_channels[:10]:  # Show first 10 failed channels
                summary += f"• {c}\n"
            if len(failed_channels) > 10:
                summary += f"... and {len(failed_channels) - 10} more"
        
        await status_msg.edit_text(summary)
    
    async def broadcast_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to a specific channel"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast_channel <channel_id>`\n\n"
                "Example: `/broadcast_channel -100123456789`"
            )
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Please reply to a message to broadcast."
            )
            return
        
        try:
            channel_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid channel ID. Must be a number.")
            return
        
        broadcast_msg = update.message.reply_to_message
        
        try:
            if broadcast_msg.photo:
                await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=broadcast_msg.photo[-1].file_id,
                    caption=broadcast_msg.caption or ""
                )
            elif broadcast_msg.video:
                await context.bot.send_video(
                    chat_id=channel_id,
                    video=broadcast_msg.video.file_id,
                    caption=broadcast_msg.caption or ""
                )
            elif broadcast_msg.animation:
                await context.bot.send_animation(
                    chat_id=channel_id,
                    animation=broadcast_msg.animation.file_id,
                    caption=broadcast_msg.caption or ""
                )
            elif broadcast_msg.document:
                await context.bot.send_document(
                    chat_id=channel_id,
                    document=broadcast_msg.document.file_id,
                    caption=broadcast_msg.caption or ""
                )
            else:
                await context.bot.send_message(
                    chat_id=channel_id,
                    text=broadcast_msg.text or "Broadcast message"
                )
            
            await update.message.reply_text(
                f"✅ Message sent successfully to channel `{channel_id}`."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to send message to channel `{channel_id}`.\n\nError: {str(e)}"
            )
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    async def add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a channel to broadcast list"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "📝 **Usage:** `/addchannel <channel_id>`\n\n"
                "Example: `/addchannel -100123456789`"
            )
            return
        
        try:
            channel_id = int(context.args[0])
            
            # Test if bot can send message to the channel
            try:
                await context.bot.send_message(
                    channel_id,
                    "✅ **This channel has been added to ToonPay broadcast list!**"
                )
                
                # Save to database
                self.db.add_channel(channel_id, update.effective_user.id)
                
                await update.message.reply_text(
                    f"✅ Channel `{channel_id}` added successfully!"
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ **Failed to add channel**\n\n"
                    f"Make sure I'm an admin in that channel!\n"
                    f"Error: {str(e)}"
                )
                
        except ValueError:
            await update.message.reply_text("❌ Invalid channel ID. Must be a number.")
    
    async def remove_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a channel from broadcast list"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "📝 **Usage:** `/removechannel <channel_id>`"
            )
            return
        
        try:
            channel_id = int(context.args[0])
            self.db.remove_channel(channel_id)
            await update.message.reply_text(
                f"✅ Channel `{channel_id}` removed successfully."
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid channel ID. Must be a number.")
    
    async def list_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all channels in broadcast list"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        channels = self.db.get_all_channels()
        if channels:
            message = "📋 Broadcast Channels:\n\n"
            for channel in channels:
                added_date = channel['added_at']
                if added_date:
                    date_str = added_date.strftime('%Y-%m-%d')
                else:
                    date_str = "Unknown"
                message += f"• {channel['channel_id']} (Added: {date_str})\n"
            message += f"\nTotal: {len(channels)} channels"
        else:
            message = "📭 No channels added.\n\nUse /addchannel <channel_id> to add one."
        
        await update.message.reply_text(message)
    
    # ==================== COMPLETE STATISTICS (FIXED) ====================
    
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
        
        # Overall stats message (without Markdown)
        overall = f"""📊 Complete Bot Statistics

Overview:
👥 Total Users: {total_users}
🎫 Total Tickets: {total_tickets}
✅ Solved Tickets: {total_solved}
🔄 In Progress: {total_in_progress}
🚫 Spam Tickets: {total_spam}
📭 Inactive Users: {len(inactive_users)} (started bot but no tickets)

"""
        
        await update.message.reply_text(overall)
        
        # Individual user stats
        if users_stats:
            await update.message.reply_text(
                "📋 User Details:\n\n"
                "(Sending detailed list...)"
            )
            
            # Send users in batches to avoid message too long error
            batch = ""
            for user in users_stats:
                # Handle None created_at
                created_date = user['created_at']
                if created_date:
                    date_str = created_date.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = "Unknown"
                
                # Handle username
                username = user['username'] or 'N/A'
                if username != 'N/A' and not username.startswith('@'):
                    username = f"@{username}"
                
                # Handle name
                name = user['name'] or 'Unknown'
                
                user_info = f"""Name: {name}
Username: {username}
User ID: {user['user_id']}
Language: {user.get('language', 'en')}
Registered: {date_str}
Status: {'✅ Active' if user['total_tickets'] > 0 else '📭 Inactive'}
Tickets: Total: {user['total_tickets']} | ✅ Solved: {user['solved_tickets']} | 🔄 In Progress: {user['in_progress_tickets']} | 🚫 Spam: {user['spam_tickets']}
─────────────────────

"""
                
                if len(batch) + len(user_info) > 4000:
                    await update.message.reply_text(batch)
                    batch = user_info
                else:
                    batch += user_info
            
            if batch:
                await update.message.reply_text(batch)
        else:
            await update.message.reply_text("📭 No users found.")
