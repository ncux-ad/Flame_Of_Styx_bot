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
from app.middlewares.validation import ValidationMiddleware, CommandValidationMiddleware
from app.services.config_watcher import LimitsHotReload
from app.services.limits import LimitsService
from app.utils.graceful_shutdown import create_graceful_shutdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("bot.log", encoding="utf-8")  # File output
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the simplified bot with graceful shutdown."""
    bot = None
    shutdown_manager = None
    redis_available = False
    
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

        # 5. Setup graceful shutdown
        shutdown_manager = await create_graceful_shutdown(bot, dp, config.admin_ids_list)
        
        # 6. Initialize Redis (if enabled)
        redis_available = False
        if config.redis_enabled:
            try:
                from app.services.redis import get_redis_service
                redis_service = await get_redis_service()
                redis_available = True
                logger.info("Redis подключен успешно")
            except Exception as e:
                logger.error(f"Ошибка подключения к Redis: {e}")
                logger.warning("Продолжаем работу без Redis rate limiting")
                config.redis_enabled = False
                redis_available = False

        # 7. Register middlewares (order matters!)
        # Validation -> Logging -> RateLimit -> DI -> SuspiciousProfile
        dp.message.middleware(ValidationMiddleware())
        dp.message.middleware(CommandValidationMiddleware())
        dp.message.middleware(LoggingMiddleware())
        
        # Rate limiting middleware (Redis or fallback)
        if redis_available:
            try:
                from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware
                dp.message.middleware(RedisRateLimitMiddleware(
                    user_limit=config.redis_user_limit,
                    admin_limit=config.redis_admin_limit,
                    interval=config.redis_interval,
                    strategy=config.redis_strategy,
                    block_duration=config.redis_block_duration,
                ))
            except ImportError as e:
                logger.error(f"Не удалось импортировать RedisRateLimitMiddleware: {e}")
                logger.warning("Используем локальный rate limiting")
                dp.message.middleware(RateLimitMiddleware(
                    user_limit=config.redis_user_limit,
                    admin_limit=config.redis_admin_limit,
                    interval=config.redis_interval
                ))
        else:
            dp.message.middleware(RateLimitMiddleware(
                user_limit=config.redis_user_limit,
                admin_limit=config.redis_admin_limit,
                interval=config.redis_interval
            ))
        
        dp.message.middleware(DependencyInjectionMiddleware())

        # SuspiciousProfile middleware (after DI to get profile_service)
        async def suspicious_profile_middleware(handler, event, data):
            logger.info("SuspiciousProfileMiddleware called")
            if "profile_service" in data:
                logger.info("Profile service found, creating SuspiciousProfileMiddleware")
                # Можно настроить auto_ban и auto_mute через конфиг
                suspicious_middleware = SuspiciousProfileMiddleware(
                    data["profile_service"], 
                    auto_ban=False,  # По умолчанию отключено для безопасности
                    auto_mute=False
                )
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
            update_type.middleware(ValidationMiddleware())
            update_type.middleware(LoggingMiddleware())
            
            # Rate limiting for other update types
            if redis_available:
                try:
                    from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware
                    update_type.middleware(RedisRateLimitMiddleware(
                        user_limit=config.redis_user_limit,
                        admin_limit=config.redis_admin_limit,
                        interval=config.redis_interval,
                        strategy=config.redis_strategy,
                        block_duration=config.redis_block_duration,
                    ))
                except ImportError:
                    update_type.middleware(RateLimitMiddleware(
                        user_limit=config.redis_user_limit,
                        admin_limit=config.redis_admin_limit,
                        interval=config.redis_interval
                    ))
            else:
                update_type.middleware(RateLimitMiddleware(
                    user_limit=config.redis_user_limit,
                    admin_limit=config.redis_admin_limit,
                    interval=config.redis_interval
                ))
            
            update_type.middleware(DependencyInjectionMiddleware())

        logger.info("Middlewares registered successfully")

        # 7. Register routers in correct order
        from app.handlers import admin, antispam, channels

        # Admin router first (handles admin commands)
        dp.include_router(admin.admin_router)

        # Channel router second (handles channel events like my_chat_member)
        dp.include_router(channels.channel_router)

        # Anti-spam router third (catches everything else)
        dp.include_router(antispam.antispam_router)

        logger.info("Routers registered successfully")

        # 8. Initialize hot-reload for limits
        limits_service = LimitsService()
        hot_reload = LimitsHotReload(limits_service, bot, config.admin_ids_list)
        hot_reload.show_limits_on_startup = config.show_limits_on_startup
        await hot_reload.start()
        logger.info("Hot-reload for limits started")
        
        # 9. Register hot-reload shutdown callback
        shutdown_manager.add_shutdown_callback(hot_reload.stop)

        # 10. Startup notification will be sent by hot-reload

        logger.info("Starting bot...")

        # 11. Start polling
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        # 12. Graceful shutdown
        if shutdown_manager and not shutdown_manager.is_shutdown_requested():
            logger.info("Performing graceful shutdown...")
            await shutdown_manager.graceful_shutdown()
        elif bot:
            logger.info("Closing bot session...")
            await bot.session.close()
        
        # 13. Close Redis connection (only if it was initialized)
        if redis_available:
            try:
                from app.services.redis import close_redis_service
                await close_redis_service()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        else:
            logger.info("Redis was not initialized, skipping connection close")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
