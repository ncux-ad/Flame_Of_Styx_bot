"""
Dependency Injection middleware с использованием punq контейнера.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database import SessionLocal
from app.container import container


class DependencyInjectionMiddleware(BaseMiddleware):
    """DI middleware с использованием punq контейнера."""

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
            # Получаем все сервисы из контейнера
            services = container.get_all_services(bot, db_session)

            # Добавляем сервисы в data
            data.update(services)

            # Логирование
            logger.info(f"DI Middleware: Injected {len(services)} services using punq container")
            logger.info(f"DI Middleware: Services: {list(services.keys())}")

            # Вызываем хендлер с event и data (aiogram 3.x стиль)
            return await handler(event, data)
