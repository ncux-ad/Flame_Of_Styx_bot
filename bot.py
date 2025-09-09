import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message

from app.config import load_config
from app.database import create_tables
from app.middlewares.dependency_injection import DependencyInjectionMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    bot = None
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        logger.info(f"Bot token: {config.bot_token[:10]}...")
        logger.info(f"Admin IDs: {config.admin_ids_list}")
        logger.info(f"Database path: {config.db_path}")

        # Create bot with default properties
        bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        # Create dispatcher
        dp = Dispatcher()

        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")

        # Register middlewares (order matters!)
        # DependencyInjectionMiddleware must be first to provide services
        dp.message.middleware(DependencyInjectionMiddleware())
        dp.message.middleware(LoggingMiddleware())
        dp.message.middleware(RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60))

        # Also register for callback queries
        dp.callback_query.middleware(DependencyInjectionMiddleware())
        dp.callback_query.middleware(LoggingMiddleware())
        dp.callback_query.middleware(
            RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)
        )

        # Register for all other update types
        dp.my_chat_member.middleware(DependencyInjectionMiddleware())
        dp.chat_member.middleware(DependencyInjectionMiddleware())
        dp.chosen_inline_result.middleware(DependencyInjectionMiddleware())
        dp.inline_query.middleware(DependencyInjectionMiddleware())
        dp.pre_checkout_query.middleware(DependencyInjectionMiddleware())
        dp.shipping_query.middleware(DependencyInjectionMiddleware())
        dp.poll_answer.middleware(DependencyInjectionMiddleware())
        dp.poll.middleware(DependencyInjectionMiddleware())
        dp.chat_join_request.middleware(DependencyInjectionMiddleware())
        dp.business_connection.middleware(DependencyInjectionMiddleware())
        dp.business_message.middleware(DependencyInjectionMiddleware())
        dp.edited_message.middleware(DependencyInjectionMiddleware())
        dp.channel_post.middleware(DependencyInjectionMiddleware())
        dp.channel_post.middleware(LoggingMiddleware())
        dp.channel_post.middleware(RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60))
        dp.edited_channel_post.middleware(DependencyInjectionMiddleware())

        logger.info("Middlewares registered successfully")

        # Register routers
        from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
        from app.handlers import admin, channels, user

        # Register routers with filters
        # Admin router first to handle admin commands
        dp.include_router(admin.admin_router)
        dp.include_router(channels.channel_router)
        dp.include_router(user.user_router)

        # Apply admin filter only to non-command messages
        # Commands will be handled by their respective routers
        # dp.message.filter(IsAdminOrSilentFilter())

        logger.info("Starting bot...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        if bot:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
