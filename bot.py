import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import load_config
from app.database import create_tables
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Create bot with default properties
        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Create dispatcher
        dp = Dispatcher()
        
        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")
        
        # Register middlewares
        dp.message.middleware(LoggingMiddleware())
        dp.message.middleware(RateLimitMiddleware(limit=5, interval=60))
        logger.info("Middlewares registered successfully")
        
        # Register routers
        from app.handlers import user, channels, admin
        dp.include_router(user.user_router)
        dp.include_router(channels.channel_router)
        dp.include_router(admin.admin_router)
        
        logger.info("Starting bot...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
