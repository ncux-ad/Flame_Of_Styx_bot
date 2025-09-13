"""
Упрощенная архитектура антиспам-бота с двумя слоями:
1. Anti-spam Router (перехватывает всё)
2. Admin Router (только админские команды)
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import load_config
from app.database import create_tables
from app.middlewares.dependency_injection import DependencyInjectionMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware
from app.middlewares.suspicious_profile import SuspiciousProfileMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the simplified bot."""
    bot = None
    try:
        # 1. Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        logger.info(f"Bot token: {config.bot_token[:10]}...")
        logger.info(f"Admin IDs: {config.admin_ids_list}")
        logger.info(f"Database path: {config.db_path}")

        # 2. Initialize database
        await create_tables()
        logger.info("Database tables created successfully")

        # 3. Create bot
        bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        # 4. Create dispatcher
        dp = Dispatcher()

        # 5. Register middlewares (order matters!)
        # Logging -> RateLimit -> DI -> SuspiciousProfile
        dp.message.middleware(LoggingMiddleware())
        dp.message.middleware(RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60))
        dp.message.middleware(DependencyInjectionMiddleware())

        # SuspiciousProfile middleware (after DI to get profile_service)
        async def suspicious_profile_middleware(handler, event, data):
            logger.info("SuspiciousProfileMiddleware called")
            if "profile_service" in data:
                logger.info("Profile service found, creating SuspiciousProfileMiddleware")
                suspicious_middleware = SuspiciousProfileMiddleware(data["profile_service"])
                return await suspicious_middleware(handler, event, data)
            else:
                logger.warning("Profile service not found in data")
            return await handler(event, data)

        dp.message.middleware(suspicious_profile_middleware)

        # Apply to other update types
        for update_type in [
            dp.callback_query,
            dp.my_chat_member,
            dp.chat_member,
            dp.channel_post,
            dp.edited_message,
            dp.edited_channel_post,
        ]:
            update_type.middleware(LoggingMiddleware())
            update_type.middleware(DependencyInjectionMiddleware())

        logger.info("Middlewares registered successfully")

        # 6. Register routers in correct order
        from app.handlers import admin, antispam, channels

        # Admin router first (handles admin commands)
        dp.include_router(admin.admin_router)

        # Channel router second (handles channel events like my_chat_member)
        dp.include_router(channels.channel_router)

        # Anti-spam router third (catches everything else)
        dp.include_router(antispam.antispam_router)

        logger.info("Routers registered successfully")
        logger.info("Starting bot...")

        # 7. Start polling
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
