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
        try:
            # Method 3: aiogram 2.x
            from aiogram import Bot, Dispatcher
            from aiogram.contrib.fsm_storage.memory import MemoryStorage
            
            bot = Bot(token=Config.BOT_TOKEN, parse_mode="HTML")
            storage = MemoryStorage()
            dp = Dispatcher(bot, storage=storage)
            logger.info("Using aiogram 2.x")
            
        except ImportError as e:
            logger.error(f"Failed to import aiogram: {e}")
            sys.exit(1)

# Import handlers
from handlers import user, admin, super_admin, group

# Register middlewares (for aiogram 3.x)
if hasattr(dp, 'message') and hasattr(dp.message, 'middleware'):
    dp.message.middleware(GroupAuthMiddleware())

# Register routers
if hasattr(dp, 'include_router'):
    # aiogram 3.x
    dp.include_router(user.router)
    dp.include_router(group.router)
    dp.include_router(admin.router)
    dp.include_router(super_admin.router)
else:
    # aiogram 2.x
    dp.register_message_handler(user.cmd_start, commands=['start'])
    # Register more handlers as needed

async def main():
    """Main function"""
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start polling
    logger.info("Starting bot...")
    try:
        if hasattr(dp, 'start_polling'):
            # aiogram 2.x
            await dp.start_polling()
        else:
            # aiogram 3.x
            await dp.start_polling(bot)
    finally:
        if hasattr(bot, 'session'):
            await bot.session.close()
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
