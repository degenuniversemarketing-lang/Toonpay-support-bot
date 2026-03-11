import asyncio
import logging
import sys
from config import Config
from database import init_db
from middlewares.auth import GroupAuthMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global variables
bot = None
dp = None

# Try different aiogram import methods
try:
    # Method 1: aiogram 3.x with DefaultBotProperties
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    logger.info("Using aiogram 3.x with DefaultBotProperties")
    
except ImportError:
    try:
        # Method 2: aiogram 3.x without DefaultBotProperties
        from aiogram import Bot, Dispatcher
        from aiogram.enums import ParseMode
        from aiogram.fsm.storage.memory import MemoryStorage
        
        bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        logger.info("Using aiogram 3.x with legacy parse_mode")
        
    except ImportError:
        logger.error("Failed to import aiogram. Please install aiogram>=3.0.0")
        sys.exit(1)

# Import handlers
from handlers import user, admin, super_admin, group

# Register middlewares
dp.message.middleware(GroupAuthMiddleware())

# Register routers - ONLY ONCE!
dp.include_router(user.router)
dp.include_router(group.router)
dp.include_router(admin.router)
dp.include_router(super_admin.router)

async def main():
    """Main function"""
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Set bot commands
    from aiogram.types import BotCommand as BotCommandType
    commands = [
        BotCommandType(command="start", description="Start the bot"),
        BotCommandType(command="support", description="Get support (works in groups)"),
        BotCommandType(command="profile", description="View your profile"),
        BotCommandType(command="update_email", description="Update your email"),
        BotCommandType(command="update_phone", description="Update your phone number")
    ]
    await bot.set_my_commands(commands)
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
