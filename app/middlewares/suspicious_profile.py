"""Middleware for analyzing suspicious profiles."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.services.profiles import ProfileService

logger = logging.getLogger(__name__)


class SuspiciousProfileMiddleware(BaseMiddleware):
    """Middleware for analyzing user profiles for suspicious patterns."""

    def __init__(self, profile_service: ProfileService):
        self.profile_service = profile_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Analyze user profile for suspicious patterns."""

        # Проверяем, что это сообщение от пользователя
        if isinstance(event, Message) and event.from_user:
            # Пропускаем системного пользователя Telegram (777000) - это каналы
            if event.from_user.id == 777000:
                logger.info(f"Skipping profile analysis for Telegram system user (777000)")
                return await handler(event, data)

            logger.info(
                f"Processing message from user {event.from_user.id} in chat {event.chat.id if event.chat else 'unknown'}"
            )
            try:
                # Получаем admin_id из данных
                admin_id = data.get("admin_id")
                logger.info(f"Admin ID from data: {admin_id}")
                if not admin_id:
                    logger.warning("Admin ID not found in data, skipping profile analysis")
                    return await handler(event, data)

                # Анализируем профиль пользователя
                logger.info(f"Starting profile analysis for user {event.from_user.id}")
                suspicious_profile = await self.profile_service.analyze_user_profile(
                    user=event.from_user, admin_id=admin_id
                )

                if suspicious_profile:
                    logger.warning(
                        f"Suspicious profile detected: user_id={event.from_user.id}, "
                        f"score={suspicious_profile.suspicion_score}, "
                        f"chat_id={event.chat.id if event.chat else 'unknown'}"
                    )
                else:
                    logger.info(
                        f"Profile analysis completed for user {event.from_user.id} - not suspicious"
                    )

            except Exception as e:
                logger.error(f"Error in suspicious profile middleware: {e}")
        else:
            logger.info(
                f"Not a user message: event_type={type(event)}, has_from_user={hasattr(event, 'from_user') and event.from_user is not None}"
            )

        # Продолжаем выполнение следующего обработчика
        return await handler(event, data)
