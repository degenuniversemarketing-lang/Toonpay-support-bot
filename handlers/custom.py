from telegram import Update
from telegram.ext import ContextTypes
from database import Database
import logging

logger = logging.getLogger(__name__)

class CustomCommandHandler:
    def __init__(self, db: Database):
        self.db = db
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom commands"""
        command = update.message.text.split()[0][1:].lower()
        
        # Skip built-in commands
        built_in = ['start', 'new', 'cancel', 'support', 'pending', 'stats', 
                   'search', 'download', 'download_solved', 'download_pending',
                   'activate', 'deactivate', 'listactivated', 'deletedata',
                   'addfilter', 'removefilter', 'listfilters', 'broadcast', 'allstats']
        
        if command in built_in:
            return  # Let built-in handlers process it
        
        # Check if it's a custom command
        cmd_data = self.db.get_custom_command(command)
        
        if cmd_data:
            content = cmd_data['content']
            
            # Check if content is a link
            if content.startswith(('http://', 'https://', 't.me/', 'www.')):
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                
                # Add protocol if missing
                if content.startswith('t.me/'):
                    content = 'https://' + content
                elif content.startswith('www.'):
                    content = 'https://' + content
                
                keyboard = [[InlineKeyboardButton("🔗 Click Here", url=content)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"Here's your requested link:",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(content)
            
            return True
        
        # If not found, optionally send error
        # await update.message.reply_text("❌ Unknown command.")
