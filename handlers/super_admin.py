from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from utils.helpers import parse_time_string
import logging
from datetime import datetime
import asyncio
from collections import Counter

logger = logging.getLogger(__name__)

# Language names and emojis
LANGUAGE_INFO = {
    'en': {'name': 'English', 'emoji': '🇬🇧'},
    'de': {'name': 'German', 'emoji': '🇩🇪'},
    'hu': {'name': 'Hungarian', 'emoji': '🇭🇺'},
    'es': {'name': 'Spanish', 'emoji': '🇪🇸'},
    'fr': {'name': 'French', 'emoji': '🇫🇷'},
    'it': {'name': 'Italian', 'emoji': '🇮🇹'},
    'pt': {'name': 'Portuguese', 'emoji': '🇵🇹'},
    'ru': {'name': 'Russian', 'emoji': '🇷🇺'},
    'ar': {'name': 'Arabic', 'emoji': '🇸🇦'},
    'zh': {'name': 'Chinese', 'emoji': '🇨🇳'},
    'ja': {'name': 'Japanese', 'emoji': '🇯🇵'},
    'hi': {'name': 'Hindi', 'emoji': '🇮🇳'}
}

class SuperAdminHandlers:
    def __init__(self, db: Database):
        self.db = db
        self.filters = {}
    
    async def is_super_admin(self, update: Update) -> bool:
        from config import Config
        return update.effective_user.id == Config.SUPER_ADMIN_ID
    
    # ==================== LANGUAGE BROADCAST ====================
    
    async def broadcast_language_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show language selection menu for broadcast"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Get language statistics
        lang_stats = self.db.get_language_statistics()
        
        if not lang_stats:
            await update.message.reply_text("📭 No users found to broadcast to.")
            return
        
        total_users = sum(lang_stats.values())
        
        # Create message
        message = "🌐 **Language-Based Broadcast**\n\n"
        message += f"📊 **Total Users:** {total_users}\n\n"
        message += "**Select a language to broadcast to:**\n\n"
        
        # Create buttons for each language
        keyboard = []
        for lang_code, count in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True):
            if lang_code in LANGUAGE_INFO:
                info = LANGUAGE_INFO[lang_code]
                button_text = f"{info['emoji']} {info['name']} ({count} users)"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"broadcast_lang_{lang_code}")])
        
        # Add option for ALL users
        keyboard.append([InlineKeyboardButton("🌍 ALL USERS (All Languages)", callback_data="broadcast_lang_all")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def broadcast_language_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection for broadcast"""
        query = update.callback_query
        await query.answer()
        
        if not await self.is_super_admin(update):
            await query.edit_message_text("❌ You are not authorized to use this command.")
            return
        
        lang_code = query.data.replace('broadcast_lang_', '')
        
        if lang_code == 'cancel':
            await query.edit_message_text("❌ Broadcast cancelled.")
            return
        
        # Store selected language in context
        context.user_data['broadcast_lang'] = lang_code
        
        if lang_code == 'all':
            lang_name = "ALL USERS"
            user_count = len(self.db.get_all_users())
        else:
            lang_name = LANGUAGE_INFO.get(lang_code, {}).get('name', lang_code.upper())
            user_count = self.db.get_user_count_by_language(lang_code)
        
        await query.edit_message_text(
            f"📤 **Broadcast to {lang_name}**\n\n"
            f"👥 **Users to receive:** {user_count}\n\n"
            f"✅ **Ready!**\n\n"
            f"Now **reply** to a message with your broadcast content.\n\n"
            f"Supported content:\n"
            f"• Text messages\n"
            f"• Images with captions\n"
            f"• Videos with captions\n"
            f"• GIFs\n"
            f"• Any media type\n\n"
            f"⏱️ You have 5 minutes to send the broadcast message."
        )
        
        # Set timeout for broadcast
        context.user_data['broadcast_pending'] = True
        
        # Schedule timeout
        if 'broadcast_timeout' in context.user_data:
            context.user_data['broadcast_timeout'].cancel()
        
        loop = asyncio.get_event_loop()
        timeout_task = loop.create_task(self.broadcast_timeout(update, context))
        context.user_data['broadcast_timeout'] = timeout_task
    
    async def broadcast_timeout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle broadcast timeout"""
        await asyncio.sleep(300)  # 5 minutes timeout
        if context.user_data.get('broadcast_pending', False):
            context.user_data['broadcast_pending'] = False
            context.user_data.pop('broadcast_lang', None)
            try:
                await update.message.reply_text("⏰ Broadcast session timed out. Please start again with /broadcast_lang")
            except:
                pass
    
    async def process_language_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the actual broadcast message after language selection"""
        if not context.user_data.get('broadcast_pending', False):
            return
        
        if 'broadcast_lang' not in context.user_data:
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "❌ Please **reply** to a message with your broadcast content.\n\n"
                "Usage:\n"
                "1. Send the message you want to broadcast\n"
                "2. Reply to that message with this command"
            )
            return
        
        lang_code = context.user_data['broadcast_lang']
        
        if lang_code == 'all':
            users = self.db.get_all_users()
            lang_name = "ALL USERS"
        else:
            users = self.db.get_users_by_language(lang_code)
            lang_name = LANGUAGE_INFO.get(lang_code, {}).get('name', lang_code.upper())
        
        if not users:
            await update.message.reply_text(f"📭 No users found for {lang_name}.")
            context.user_data['broadcast_pending'] = False
            context.user_data.pop('broadcast_lang', None)
            return
        
        status_msg = await update.message.reply_text(
            f"📤 **Broadcasting to {lang_name}**\n"
            f"👥 **Target Users:** {len(users)}\n"
            f"⏳ Sending messages...\n\n"
            f"_{lang_name}_"
        )
        
        success_count = 0
        fail_count = 0
        
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
            
            await asyncio.sleep(0.05)
        
        await status_msg.edit_text(
            f"📊 **Language Broadcast Complete**\n\n"
            f"🌐 **Language:** {lang_name}\n"
            f"✅ **Success:** {success_count}\n"
            f"❌ **Failed:** {fail_count}\n"
            f"📈 **Total:** {len(users)}"
        )
        
        # Clear broadcast session
        context.user_data['broadcast_pending'] = False
        context.user_data.pop('broadcast_lang', None)
    
    # ==================== SIMPLE LANGUAGE BROADCAST COMMANDS ====================
    
    async def broadcast_en(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to English users only"""
        await self.broadcast_by_language(update, context, 'en', 'English')
    
    async def broadcast_de(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to German users only"""
        await self.broadcast_by_language(update, context, 'de', 'German')
    
    async def broadcast_hu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Hungarian users only"""
        await self.broadcast_by_language(update, context, 'hu', 'Hungarian')
    
    async def broadcast_es(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Spanish users only"""
        await self.broadcast_by_language(update, context, 'es', 'Spanish')
    
    async def broadcast_fr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to French users only"""
        await self.broadcast_by_language(update, context, 'fr', 'French')
    
    async def broadcast_it(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Italian users only"""
        await self.broadcast_by_language(update, context, 'it', 'Italian')
    
    async def broadcast_pt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Portuguese users only"""
        await self.broadcast_by_language(update, context, 'pt', 'Portuguese')
    
    async def broadcast_ru(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Russian users only"""
        await self.broadcast_by_language(update, context, 'ru', 'Russian')
    
    async def broadcast_ar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Arabic users only"""
        await self.broadcast_by_language(update, context, 'ar', 'Arabic')
    
    async def broadcast_zh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Chinese users only"""
        await self.broadcast_by_language(update, context, 'zh', 'Chinese')
    
    async def broadcast_ja(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Japanese users only"""
        await self.broadcast_by_language(update, context, 'ja', 'Japanese')
    
    async def broadcast_hi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast to Hindi users only"""
        await self.broadcast_by_language(update, context, 'hi', 'Hindi')
    
    async def broadcast_by_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code, lang_name):
        """Helper method to broadcast by language"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                f"📤 **Broadcast to {lang_name} Users**\n\n"
                f"Usage:\n"
                f"1. Send the message you want to broadcast\n"
                f"2. Reply to that message with `/{lang_code}`\n\n"
                f"Supported content:\n"
                f"• Text messages\n"
                f"• Images with captions\n"
                f"• Videos with captions\n"
                f"• GIFs\n"
                f"• Any media type"
            )
            return
        
        # Get users by language
        users = self.db.get_users_by_language(lang_code)
        
        if not users:
            await update.message.reply_text(f"📭 No {lang_name} users found.")
            return
        
        status_msg = await update.message.reply_text(
            f"📤 **Broadcasting to {lang_name} Users**\n"
            f"👥 **Target Users:** {len(users)}\n"
            f"⏳ Sending messages..."
        )
        
        success_count = 0
        fail_count = 0
        
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
            
            await asyncio.sleep(0.05)
        
        await status_msg.edit_text(
            f"📊 **Broadcast Complete**\n\n"
            f"🌐 **Language:** {lang_name}\n"
            f"✅ **Success:** {success_count}\n"
            f"❌ **Failed:** {fail_count}\n"
            f"📈 **Total:** {len(users)}"
        )
    
    # ==================== EXISTING BROADCAST METHODS ====================
    
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to all users (original method)"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast` to send it to all users.\n\n"
                "You can also use language-specific broadcast:\n"
                "• `/broadcast_en` - English only\n"
                "• `/broadcast_de` - German only\n"
                "• `/broadcast_lang` - Show language selection menu\n\n"
                "Supported content:\n"
                "• Text messages\n"
                "• Images with captions\n"
                "• Videos with captions\n"
                "• GIFs\n"
                "• Any media type"
            )
            return
        
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
            
            await asyncio.sleep(0.05)
        
        await status_msg.edit_text(
            f"📊 **Broadcast Complete**\n\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {fail_count}\n"
            f"📈 Total: {len(users)}"
        )
    
    # ==================== EXISTING METHODS (Group Management, etc.) ====================
    
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
            
            try:
                await context.bot.send_message(
                    group_id,
                    "✅ **This group has been activated for ToonPay Support!**\n\n"
                    "Users can now use /support command here."
                )
                
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
            message = "📋 **Activated Groups:**\n\n"
            for group_id in groups:
                message += f"• {group_id}\n"
            message += f"\nTotal: {len(groups)} groups"
        else:
            message = "📭 No activated groups.\n\nUse `/activate <group_id>` to add one."
        
        await update.message.reply_text(message)
    
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
            days = delta.total_seconds() / 86400
            deleted = self.db.delete_old_data(days)
            
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
            await update.message.reply_text(f"✅ Command `/{command}` removed successfully.")
        else:
            await update.message.reply_text(f"❌ Command `/{command}` not found.")
    
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
            content = cmd['content'][:50] + "..." if len(cmd['content']) > 50 else cmd['content']
            message += f"• /{cmd['command']} - {content}\n"
        
        await update.message.reply_text(message)
    
    # ==================== GROUP BROADCAST ====================
    
    async def broadcast_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to all groups where bot is admin"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
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
        
        admin_groups = self.db.get_admin_groups()
        activated_groups = self.db.get_activated_groups()
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
            
            await asyncio.sleep(0.05)
        
        summary = f"📊 **Group Broadcast Complete**\n\n"
        summary += f"✅ Success: {success_count}\n"
        summary += f"❌ Failed: {fail_count}\n"
        summary += f"📈 Total: {len(all_groups)}"
        
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
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a message to broadcast.")
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
            
            await update.message.reply_text(f"✅ Message sent successfully to group `{group_id}`.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send message to group `{group_id}`.\n\nError: {str(e)}")
    
    # ==================== CHANNEL MANAGEMENT ====================
    
    async def broadcast_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message to all channels where bot is admin"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📝 **Usage:** Reply to a message with `/broadcast_channels` to send it to all channels."
            )
            return
        
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
            
            await asyncio.sleep(0.05)
        
        summary = f"📊 **Channel Broadcast Complete**\n\n"
        summary += f"✅ Success: {success_count}\n"
        summary += f"❌ Failed: {fail_count}\n"
        summary += f"📈 Total: {len(channels)}"
        
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
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a message to broadcast.")
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
            
            await update.message.reply_text(f"✅ Message sent successfully to channel `{channel_id}`.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send message to channel `{channel_id}`.\n\nError: {str(e)}")
    
    async def add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a channel to broadcast list"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("📝 **Usage:** `/addchannel <channel_id>`\n\nExample: `/addchannel -100123456789`")
            return
        
        try:
            channel_id = int(context.args[0])
            
            try:
                await context.bot.send_message(
                    channel_id,
                    "✅ **This channel has been added to ToonPay broadcast list!**"
                )
                
                self.db.add_channel(channel_id, update.effective_user.id)
                await update.message.reply_text(f"✅ Channel `{channel_id}` added successfully!")
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
            await update.message.reply_text("📝 **Usage:** `/removechannel <channel_id>`")
            return
        
        try:
            channel_id = int(context.args[0])
            self.db.remove_channel(channel_id)
            await update.message.reply_text(f"✅ Channel `{channel_id}` removed successfully.")
        except ValueError:
            await update.message.reply_text("❌ Invalid channel ID. Must be a number.")
    
    async def list_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all channels in broadcast list"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        channels = self.db.get_all_channels()
        if channels:
            message = "📋 **Broadcast Channels:**\n\n"
            for channel in channels:
                added_date = channel['added_at']
                date_str = added_date.strftime('%Y-%m-%d') if added_date else "Unknown"
                message += f"• {channel['channel_id']} (Added: {date_str})\n"
            message += f"\nTotal: {len(channels)} channels"
        else:
            message = "📭 No channels added.\n\nUse `/addchannel <channel_id>` to add one."
        
        await update.message.reply_text(message)
    
    # ==================== ALL STATS WITH LANGUAGE BREAKDOWN ====================
    
    async def all_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get comprehensive statistics about all users with language breakdown"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        users_stats = self.db.get_all_users_with_stats()
        
        total_users = len(users_stats)
        total_tickets = sum(u['total_tickets'] for u in users_stats)
        total_solved = sum(u['solved_tickets'] for u in users_stats)
        total_in_progress = sum(u['in_progress_tickets'] for u in users_stats)
        total_spam = sum(u['spam_tickets'] for u in users_stats)
        inactive_users = [u for u in users_stats if u['total_tickets'] == 0]
        
        # Language breakdown
        language_counts = Counter()
        for user in users_stats:
            lang = user.get('language', 'en')
            language_counts[lang] += 1
        
        language_stats = "\n🌐 **Language Breakdown:**\n"
        for lang_code, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
            info = LANGUAGE_INFO.get(lang_code, {'name': lang_code.upper(), 'emoji': '🌐'})
            language_stats += f"  {info['emoji']} {info['name']}: {count} users\n"
        
        overall = f"""📊 **Complete Bot Statistics**

**Overview:**
👥 **Total Users:** {total_users}
🎫 **Total Tickets:** {total_tickets}
✅ **Solved Tickets:** {total_solved}
🔄 **In Progress:** {total_in_progress}
🚫 **Spam Tickets:** {total_spam}
📭 **Inactive Users:** {len(inactive_users)} (started bot but no tickets)
{language_stats}
"""
        
        await update.message.reply_text(overall)
        
        if users_stats:
            await update.message.reply_text("📋 **User Details:**\n\n_(Sending detailed list...)_")
            
            batch = ""
            for user in users_stats:
                created_date = user['created_at']
                date_str = created_date.strftime('%Y-%m-%d %H:%M') if created_date else "Unknown"
                
                username = user['username'] or 'N/A'
                if username != 'N/A' and not username.startswith('@'):
                    username = f"@{username}"
                
                name = user['name'] or 'Unknown'
                lang_code = user.get('language', 'en')
                info = LANGUAGE_INFO.get(lang_code, {'emoji': '🌐', 'name': lang_code.upper()})
                
                user_info = f"""**Name:** {name}
**Username:** {username}
**User ID:** {user['user_id']}
**Language:** {info['emoji']} {info['name']}
**Registered:** {date_str}
**Status:** {'✅ Active' if user['total_tickets'] > 0 else '📭 Inactive'}
**Tickets:** Total: {user['total_tickets']} | ✅ Solved: {user['solved_tickets']} | 🔄 In Progress: {user['in_progress_tickets']} | 🚫 Spam: {user['spam_tickets']}
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
