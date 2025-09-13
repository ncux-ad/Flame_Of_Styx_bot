"""
Упрощенный Dependency Injection middleware для двухслойной архитектуры.
Инжектирует только необходимые сервисы.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.database import SessionLocal
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService


class DependencyInjectionMiddleware(BaseMiddleware):
    """Упрощенный DI middleware для двухслойной архитектуры."""

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Инжектирует зависимости в хендлеры."""
        import logging

        logger = logging.getLogger(__name__)

        # Получаем bot instance
        bot = event.bot

        # Получаем database session
        async with SessionLocal() as db_session:
            # Получаем admin ID из конфига
            from app.config import load_config

            config = load_config()
            admin_id = config.admin_ids_list[0] if config.admin_ids_list else 0

            # Создаем только необходимые сервисы
            services = {
                # Основные сервисы для антиспама
                "moderation_service": ModerationService(bot, db_session),
                "link_service": LinkService(bot, db_session),
                # Дополнительные сервисы для админки
                "profile_service": ProfileService(bot, db_session),
                "channel_service": ChannelService(bot, db_session),
                "bot_service": BotService(bot, db_session),
                "help_service": HelpService(),
                "limits_service": LimitsService(),
                # Метаданные
                "admin_id": admin_id,
                "db_session": db_session,
            }

            # Добавляем сервисы в data
            data.update(services)

            # Логирование
            logger.info(f"DI Middleware: Injected {len(services)} services")
            logger.info(f"DI Middleware: Services: {list(services.keys())}")

            # Вызываем хендлер с event и data (aiogram 3.x стиль)
            return await handler(event, data)
