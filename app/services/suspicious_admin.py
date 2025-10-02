"""
Suspicious Admin Service - бизнес-логика для подозрительных профилей
"""

import logging
from typing import Any, Dict, List, Optional

from aiogram.types import Message, User

from app.services.profiles import ProfileService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class SuspiciousAdminService:
    """Сервис для управления подозрительными профилями в админке."""

    def __init__(self, profile_service: ProfileService):
        self.profile_service = profile_service

    async def get_suspicious_profiles_display(self) -> str:
        """Получить отображение подозрительных профилей."""
        try:
            profiles = await self.profile_service.get_suspicious_profiles(limit=50)

            if not profiles:
                return "🔍 Подозрительные профили не найдены"

            # Формируем текст
            text = "🔍 <b>Подозрительные профили</b>\n\n"
            text += "Система автоматически анализирует профили пользователей и обнаруживает подозрительные паттерны.\n\n"
            text += "📊 <b>Доступные команды:</b>\n"
            text += "• /suspicious - просмотр всех подозрительных профилей\n"
            text += "• /suspicious_reset - сброс статусов для тестирования\n"
            text += "• /suspicious_analyze <user_id> - проанализировать пользователя\n"
            text += "• /suspicious_remove <user_id> - удалить из подозрительных\n"

            return text

        except Exception as e:
            logger.error(f"Error getting suspicious profiles display: {sanitize_for_logging(str(e))}")
            raise

    async def analyze_user_profile_display(self, user_id: int, admin_id: int) -> str:
        """Получить отображение анализа профиля пользователя."""
        try:
            # Получаем информацию о пользователе
            user_info = await self.profile_service.get_user_info(user_id)

            # Создаем объект User для анализа
            user = User(
                id=user_info["id"],
                is_bot=user_info["is_bot"],
                first_name=user_info["first_name"],
                last_name=user_info["last_name"],
                username=user_info["username"],
            )

            # Анализируем профиль
            profile = await self.profile_service.analyze_user_profile(user, admin_id)

            # Формируем ответ
            text = "🔍 <b>Анализ профиля пользователя</b>\n\n"
            text += (
                "<b>Пользователь:</b> " + str(user_info["first_name"] or "") + " " + str(user_info["last_name"] or "") + "\n"
            )
            text += "<b>ID:</b> <code>" + str(user_id) + "</code>\n"
            text += "<b>Username:</b> @" + str(user_info["username"] or "Нет") + "\n"

            if profile:
                # Пользователь подозрительный
                text += "<b>Счет подозрительности:</b> " + str(profile.suspicion_score) + "\n"

                # Безопасно парсим паттерны
                patterns = []
                if profile.detected_patterns and str(profile.detected_patterns).strip():
                    try:
                        if isinstance(profile.detected_patterns, (str, int, float)):
                            patterns = str(profile.detected_patterns).split(",")
                            patterns = [p.strip() for p in patterns if p.strip()]
                    except Exception:
                        patterns = []

                text += "<b>Обнаружено паттернов:</b> " + str(len(patterns)) + "\n\n"

                if patterns:
                    text += "<b>🔍 Обнаруженные паттерны:</b>\n"
                    for pattern in patterns:
                        text += "• " + str(pattern) + "\n"
                    text += "\n"

                # Безопасно проверяем связанный чат
                if profile.linked_chat_title and str(profile.linked_chat_title).strip():
                    try:
                        chat_title = str(profile.linked_chat_title).strip()
                        if chat_title:
                            text += "<b>📱 Связанный чат:</b> " + str(chat_title) + "\n"
                            text += "<b>📊 Постов:</b> " + str(profile.post_count) + "\n\n"
                    except Exception:
                        pass

                # Определяем статус
                try:
                    score = float(str(profile.suspicion_score))
                    if score >= 0.7:
                        status = "🔴 Высокий риск"
                    elif score >= 0.4:
                        status = "🟡 Средний риск"
                    else:
                        status = "🟢 Низкий риск"
                except Exception:
                    status = "🟢 Низкий риск"

                text += "<b>Статус:</b> " + str(status) + "\n"

                # Безопасно форматируем дату
                try:
                    if profile.created_at and hasattr(profile.created_at, "strftime"):
                        date_str = profile.created_at.strftime("%d.%m.%Y %H:%M")
                    else:
                        date_str = "Неизвестно"
                except Exception:
                    date_str = "Неизвестно"

                text += "<b>Дата анализа:</b> " + str(date_str)
            else:
                # Пользователь не подозрительный
                text += "<b>Счет подозрительности:</b> 0.00\n"
                text += "<b>Обнаружено паттернов:</b> 0\n\n"
                text += "<b>Статус:</b> 🟢 Низкий риск\n"
                text += "<b>Результат:</b> Пользователь не является подозрительным"

            return text

        except Exception as e:
            logger.error(f"Error analyzing user profile: {sanitize_for_logging(str(e))}")
            raise

    async def reset_suspicious_profiles(self) -> int:
        """Сбросить все подозрительные профили."""
        try:
            return await self.profile_service.reset_suspicious_profiles()
        except Exception as e:
            logger.error(f"Error resetting suspicious profiles: {sanitize_for_logging(str(e))}")
            raise

    async def remove_suspicious_profile(self, user_id: int) -> bool:
        """Удалить пользователя из подозрительных профилей."""
        try:
            profile = await self.profile_service._get_suspicious_profile(user_id)
            if not profile:
                return False

            await self.profile_service.db.delete(profile)
            await self.profile_service.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing suspicious profile: {sanitize_for_logging(str(e))}")
            raise
