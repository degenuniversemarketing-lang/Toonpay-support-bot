from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.helpers import parse_time_string
from datetime import datetime, timedelta

class SuperAdminHandlers:
    def __init__(self, db: Database):
        self.db = db
    
    async def is_super_admin(self, update: Update) -> bool:
        from config import Config
        return update.effective_user.id == Config.SUPER_ADMIN_ID
    
    async def add_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /add <group_id>")
            return
        
        try:
            group_id = int(context.args[0])
            self.db.add_admin_group(group_id, update.effective_user.id)
            await update.message.reply_text(f"✅ Group {group_id} added as admin group.")
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    
    async def remove_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /remove <group_id>")
            return
        
        try:
            group_id = int(context.args[0])
            self.db.remove_admin_group(group_id)
            await update.message.reply_text(f"✅ Group {group_id} removed from admin groups.")
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Must be a number.")
    
    async def list_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        groups = self.db.get_admin_groups()
        if groups:
            message = "📋 **Admin Groups:**\n\n"
            for group_id in groups:
                message += f"• {group_id}\n"
        else:
            message = "No admin groups configured."
        
        await update.message.reply_text(message)
    
    async def delete_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_super_admin(update):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /deletedata <days/hours/minutes>\nExample: /deletedata 7 days")
            return
        
        time_str = ' '.join(context.args)
        try:
            delta = parse_time_string(time_str)
            days = delta.days + delta.seconds / 86400
            
            deleted = self.db.delete_old_data(days)
            await update.message.reply_text(f"✅ Deleted {deleted} tickets older than {time_str}.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
