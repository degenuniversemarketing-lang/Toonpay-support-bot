from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.helpers import parse_time_string
import logging

logger = logging.getLogger(__name__)

class SuperAdminHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def is_super_admin(self, update: Update) -> bool:
        from config import Config
        return update.effective_user.id == Config.SUPER_ADMIN_ID
    
    async def add_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a public group where /support command will work"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Usage:** `/add <group_id>`\n\n"
                "Get group ID by:\n"
                "1. Add @getidsbot to your group\n"
                "2. Send any message\n"
                "3. Bot will show group ID",
                parse_mode='Markdown'
            )
            return
        
        try:
            group_id = int(context.args[0])
            self.db.add_admin_group(group_id, update.effective_user.id)
            
            # Test if bot can send message to the group
            try:
                await context.bot.send_message(
                    group_id,
                    "✅ **This group has been added as a support channel!**\n\n"
                    "Users can now use /support command here.\n"
                    "New tickets will appear in this group.",
                    parse_mode='Markdown'
                )
                await update.message.reply_text(f"✅ Group `{group_id}` added successfully as support channel!", parse_mode='Markdown')
            except:
                await update.message.reply_text(
                    f"⚠️ Group `{group_id}` added but I couldn't send a test message.\n"
                    f"Make sure I'm an admin in that group!",
                    parse_mode='Markdown'
                )
                
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
        except Exception as e:
            logger.error(f"Error adding group: {e}")
            await update.message.reply_text(f"❌ Error adding group: {str(e)}")
    
    async def remove_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a group from support channels"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("📝 **Usage:** `/remove <group_id>`", parse_mode='Markdown')
            return
        
        try:
            group_id = int(context.args[0])
            self.db.remove_admin_group(group_id)
            await update.message.reply_text(f"✅ Group `{group_id}` removed from support channels.", parse_mode='Markdown')
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    
    async def list_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all support channels"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        groups = self.db.get_admin_groups()
        if groups:
            message = "📋 **Support Channels:**\n\n"
            for group_id in groups:
                message += f"• `{group_id}`\n"
            message += f"\nTotal: {len(groups)} groups"
        else:
            message = "📭 No support channels configured.\n\nUse `/add <group_id>` to add one."
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def delete_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete old ticket data"""
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Usage:** `/deletedata <days>`\n\n"
                "Example: `/deletedata 30` - deletes tickets older than 30 days",
                parse_mode='Markdown'
            )
            return
        
        try:
            days = int(context.args[0])
            if days < 1:
                await update.message.reply_text("❌ Days must be at least 1.")
                return
            
            deleted = self.db.delete_old_data(days)
            await update.message.reply_text(
                f"✅ Deleted `{deleted}` tickets older than {days} days.",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Invalid number of days.")
        except Exception as e:
            logger.error(f"Error deleting data: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
