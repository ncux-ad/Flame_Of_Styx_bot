"""Middleware for analyzing suspicious profiles."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.services.profiles import ProfileService

logger = logging.getLogger(__name__)


class SuspiciousProfileMiddleware(BaseMiddleware):
    """Middleware for analyzing user profiles for suspicious patterns."""

    def __init__(self, profile_service: ProfileService, auto_ban: bool = False, auto_mute: bool = False):
        self.profile_service = profile_service
        self.auto_ban = auto_ban
        self.auto_mute = auto_mute

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
                logger.info("Skipping profile analysis for Telegram system user (777000)")
                return await handler(event, data)

            # Пропускаем анализ для сообщений от каналов (sender_chat)
            # (когда есть sender_chat, это означает, что сообщение от канала)
            if event.sender_chat:
                logger.info(f"Skipping profile analysis for message from channel: {event.sender_chat.title}")
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
                suspicious_profile = await self.profile_service.analyze_user_profile(user=event.from_user, admin_id=admin_id)

                if suspicious_profile:
                    logger.warning(
                        f"Suspicious profile detected: user_id={event.from_user.id}, "
                        f"score={suspicious_profile.suspicion_score}, "
                        f"chat_id={event.chat.id if event.chat else 'unknown'}"
                    )

                    # Опциональная реакция на подозрительный профиль
                    if self.auto_ban or self.auto_mute:
                        await self._handle_suspicious_profile(event, suspicious_profile, data)
                else:
                    logger.info(f"Profile analysis completed for user {event.from_user.id} - not suspicious")

            except Exception as e:
                logger.error(f"Error in suspicious profile middleware: {e}")
        else:
            logger.info(
                f"Not a user message: event_type={type(event)}, has_from_user={hasattr(event, 'from_user') and event.from_user is not None}"
            )

        # Продолжаем выполнение следующего обработчика
        return await handler(event, data)

    async def _handle_suspicious_profile(self, event: Message, suspicious_profile, data: Dict[str, Any]) -> None:
        """Handle suspicious profile with optional auto-ban or auto-mute."""
        try:
            from app.services.moderation import ModerationService

            # Получаем сервисы из data
            moderation_service = data.get("moderation_service")
            if not moderation_service:
                logger.error("ModerationService not found in data")
                return

            user_id = event.from_user.id
            chat_id = event.chat.id if event.chat else None

            if not chat_id:
                logger.error("Chat ID not available for moderation action")
                return

            # Определяем действие на основе настроек
            if self.auto_ban:
                # Автоматический бан
                success = await moderation_service.ban_user(
                    user_id=user_id,
                    chat_id=chat_id,
                    admin_id=data.get("admin_id", 0),  # System action
                    reason=f"Подозрительный профиль (счет: {suspicious_profile.suspicion_score:.2f})",
                )

                if success:
                    logger.warning(f"Auto-banned suspicious user {user_id} in chat {chat_id}")
                    # Удаляем сообщение
                    await moderation_service.delete_message(
                        chat_id=chat_id, message_id=event.message_id, admin_id=data.get("admin_id", 0)
                    )
                else:
                    logger.error(f"Failed to auto-ban suspicious user {user_id}")

            elif self.auto_mute:
                # Автоматический мьют (если поддерживается)
                logger.info(f"Auto-mute not implemented yet for user {user_id}")
                # TODO: Implement mute functionality if needed

        except Exception as e:
            logger.error(f"Error handling suspicious profile: {e}")
