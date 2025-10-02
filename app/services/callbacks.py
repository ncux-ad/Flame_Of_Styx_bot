"""
Callbacks Service - бизнес-логика для callback-ов
"""

import logging
from typing import Any, Dict, Optional

from aiogram.types import CallbackQuery

from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class CallbacksService:
    """Сервис для обработки callback-ов."""

    def __init__(
        self,
        moderation_service: ModerationService,
        profile_service: ProfileService,
    ):
        self.moderation_service = moderation_service
        self.profile_service = profile_service

    async def handle_ban_suspicious_user(self, callback_query: CallbackQuery, user_id: int, admin_id: int) -> Dict[str, Any]:
        """Обработать бан подозрительного пользователя."""
        try:
            if not callback_query.from_user:
                return {"success": False, "error": "No user"}

            # Получаем информацию о пользователе
            user_info = await self.profile_service.get_user_info(user_id)

            # Получаем профиль для получения счета подозрительности
            profile = await self.profile_service._get_suspicious_profile(user_id)
            suspicion_score = profile.suspicion_score if profile else 0.0

            # Баним пользователя
            success = await self.moderation_service.ban_user(
                user_id=user_id,
                chat_id=callback_query.message.chat.id if callback_query.message else 0,
                reason=f"Подозрительный профиль (счет: {suspicion_score:.2f})",
                admin_id=admin_id,
            )

            if success:
                # Отмечаем профиль как проверенный и подтвержденный
                await self.profile_service.mark_profile_as_reviewed(
                    user_id=user_id,
                    admin_id=admin_id,
                    is_confirmed=True,
                    notes="Забанен за подозрительный профиль",
                )

                return {
                    "success": True,
                    "user_info": user_info,
                    "user_id": user_id,
                    "suspicion_score": suspicion_score,
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to ban user",
                    "user_id": user_id,
                }

        except Exception as e:
            logger.error(f"Error in ban_suspicious callback: {sanitize_for_logging(str(e))}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
            }

    async def handle_watch_suspicious_user(self, callback_query: CallbackQuery, user_id: int, admin_id: int) -> Dict[str, Any]:
        """Обработать добавление подозрительного пользователя в наблюдение."""
        try:
            if not callback_query.from_user:
                return {"success": False, "error": "No user"}

            # Отмечаем профиль как проверенный, но не подтвержденный
            await self.profile_service.mark_profile_as_reviewed(
                user_id=user_id,
                admin_id=admin_id,
                is_confirmed=False,
                notes="Помечен для наблюдения",
            )

            return {
                "success": True,
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(f"Error in watch_suspicious callback: {sanitize_for_logging(str(e))}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
            }

    async def handle_allow_suspicious_user(self, callback_query: CallbackQuery, user_id: int, admin_id: int) -> Dict[str, Any]:
        """Обработать разрешение подозрительного пользователя (ложное срабатывание)."""
        try:
            if not callback_query.from_user:
                return {"success": False, "error": "No user"}

            # Отмечаем профиль как проверенный и ложное срабатывание
            await self.profile_service.mark_profile_as_reviewed(
                user_id=user_id,
                admin_id=admin_id,
                is_confirmed=False,
                notes="Ложное срабатывание - разрешен",
            )

            return {
                "success": True,
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(f"Error in allow_suspicious callback: {sanitize_for_logging(str(e))}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
            }

    def get_ban_success_message(self, user_info: Dict[str, Any], user_id: int) -> str:
        """Получить сообщение об успешном бане."""
        return (
            f"🚫 <b>Пользователь забанен</b>\n\n"
            f"ID: {user_id}\n"
            f"Имя: {user_info.get('first_name', 'Неизвестно')}\n"
            f"Причина: Подозрительный профиль"
        )

    def get_watch_success_message(self, user_id: int) -> str:
        """Получить сообщение об успешном добавлении в наблюдение."""
        return f"👀 <b>Пользователь добавлен в наблюдение</b>\n\n" f"ID: {user_id}\n" f"Статус: Наблюдение"

    def get_allow_success_message(self, user_id: int) -> str:
        """Получить сообщение об успешном разрешении."""
        return f"✅ <b>Пользователь разрешен</b>\n\n" f"ID: {user_id}\n" f"Статус: Ложное срабатывание"

    def get_error_message(self, error_type: str) -> str:
        """Получить сообщение об ошибке."""
        error_messages = {
            "ban": "❌ Ошибка при бане пользователя",
            "watch": "❌ Ошибка добавления в наблюдение",
            "allow": "❌ Ошибка разрешения пользователя",
            "general": "❌ Ошибка обработки",
        }
        return error_messages.get(error_type, "❌ Неизвестная ошибка")
