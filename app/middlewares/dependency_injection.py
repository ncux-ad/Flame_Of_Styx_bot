"""
Упрощенный Dependency Injection middleware для двухслойной архитектуры.
Инжектирует только необходимые сервисы.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database import SessionLocal
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.services.admin import AdminService
from app.services.status import StatusService
from app.services.channels_admin import ChannelsAdminService
from app.services.bots_admin import BotsAdminService
from app.services.suspicious_admin import SuspiciousAdminService


class DependencyInjectionMiddleware(BaseMiddleware):
    """Упрощенный DI middleware для двухслойной архитектуры."""

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Инжектирует зависимости в хендлеры."""
        import logging

        logger = logging.getLogger(__name__)

        # Получаем bot instance
        bot = event.bot
        if not bot:
            logger.error("Bot instance not available")
            return await handler(event, data)

        # Получаем database session
        async with SessionLocal() as db_session:
            # Получаем admin IDs из конфига
            from app.config import load_config

            config = load_config()
            admin_id = config.admin_ids_list[0] if config.admin_ids_list else 0
            admin_ids = config.admin_ids_list

            # Создаем основные сервисы
            moderation_service = ModerationService(bot, db_session)
            link_service = LinkService(bot, db_session)
            profile_service = ProfileService(bot, db_session)
            channel_service = ChannelService(bot, db_session, config.native_channel_ids_list)
            bot_service = BotService(bot, db_session)
            help_service = HelpService()
            limits_service = LimitsService()
            
            # Создаем админские сервисы
            admin_service = AdminService(
                moderation_service=moderation_service,
                bot_service=bot_service,
                channel_service=channel_service,
                profile_service=profile_service,
                help_service=help_service,
                limits_service=limits_service,
            )
            status_service = StatusService(
                moderation_service=moderation_service,
                bot_service=bot_service,
                channel_service=channel_service,
            )
            channels_admin_service = ChannelsAdminService(channel_service)
            bots_admin_service = BotsAdminService(bot_service)
            suspicious_admin_service = SuspiciousAdminService(profile_service)
            
            # Создаем только необходимые сервисы
            services = {
                # Основные сервисы для антиспама
                "moderation_service": moderation_service,
                "link_service": link_service,
                "profile_service": profile_service,
                "channel_service": channel_service,
                "bot_service": bot_service,
                "help_service": help_service,
                "limits_service": limits_service,
                # Админские сервисы
                "admin_service": admin_service,
                "status_service": status_service,
                "channels_admin_service": channels_admin_service,
                "bots_admin_service": bots_admin_service,
                "suspicious_admin_service": suspicious_admin_service,
                # Метаданные
                "admin_id": admin_id,  # Первый админ для обратной совместимости
                "admin_ids": admin_ids,  # Все админы
                "db_session": db_session,
            }

            # Добавляем сервисы в data
            data.update(services)

            # Логирование
            logger.info(f"DI Middleware: Injected {len(services)} services")
            logger.info(f"DI Middleware: Services: {list(services.keys())}")

            # Вызываем хендлер с event и data (aiogram 3.x стиль)
            return await handler(event, data)
