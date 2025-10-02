"""
Status Service - бизнес-логика для команды /status
"""

import logging
from typing import Any, Dict, List

from aiogram.types import Message

from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.moderation import ModerationService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class StatusService:
    """Сервис для получения статуса бота."""

    def __init__(
        self,
        moderation_service: ModerationService,
        bot_service: BotService,
        channel_service: ChannelService,
    ):
        self.moderation_service = moderation_service
        self.bot_service = bot_service
        self.channel_service = channel_service

    async def get_bot_status(self, admin_id: int) -> str:
        """Получить статус бота в виде текста."""
        try:
            # Получаем статистику
            banned_users = await self.moderation_service.get_banned_users(limit=100)
            spam_stats = await self.moderation_service.get_spam_statistics()
            deleted_messages = spam_stats.get("deleted_messages", 0)
            total_actions = spam_stats.get("total_actions", 0)

            # Получаем каналы
            all_channels = await self.channel_service.get_all_channels()

            # Разделяем на нативные и группы комментариев
            native_channels = []
            comment_groups = []

            for channel in all_channels:
                if hasattr(channel, "is_comment_group") and bool(channel.is_comment_group):
                    comment_groups.append(
                        {
                            "title": channel.title or f"Группа {channel.telegram_id}",
                            "chat_id": str(channel.telegram_id),
                            "type": "Группа для комментариев",
                        }
                    )
                elif hasattr(channel, "is_native") and bool(channel.is_native):
                    native_channels.append(
                        {
                            "title": channel.title or f"Канал {channel.telegram_id}",
                            "chat_id": str(channel.telegram_id),
                            "type": "Канал",
                        }
                    )

            # Формируем текст статуса
            status_text = "📊 <b>Подробная статистика бота</b>\n\n"

            # Информация о боте
            status_text += "🤖 <b>Информация о боте:</b>\n"
            status_text += "• Username: @FlameOfStyx_bot\n"
            status_text += "• ID: 7977609078\n"
            status_text += "• Статус: ✅ Работает\n\n"

            # Подключенные чаты
            total_chats = len(native_channels) + len(comment_groups)
            status_text += f"📢 <b>Подключённые чаты ({total_chats}):</b>\n"

            for channel in native_channels:
                status_text += f"• {channel['title']} <code>({channel['chat_id']})</code>\n"
                status_text += f"  └ Тип: {channel['type']}\n"
                status_text += "  └ Статус: ✅ Антиспам активен\n"

            for chat in comment_groups:
                status_text += f"• {chat['title']} <code>({chat['chat_id']})</code>\n"
                status_text += f"  └ Тип: {chat['type']}\n"
                status_text += "  └ Статус: ✅ Антиспам активен\n"

            # Модерация
            status_text += "\n🚫 <b>Модерация:</b>\n"
            status_text += f"• Активных банов: {len(banned_users)}\n"
            status_text += f"• Всего записей: {len(banned_users)}\n"
            status_text += f"• Удалено спам-сообщений: {deleted_messages}\n"
            status_text += f"• Всего действий модерации: {total_actions}\n\n"

            # Мониторинг и healthcheck
            status_text += "📊 <b>Мониторинг и Healthcheck:</b>\n"
            status_text += "• <b>Glances:</b> http://your-server:61208 (мониторинг системы)\n"
            status_text += "• <b>Healthcheck:</b> http://your-server/health (статус бота)\n"
            status_text += "• <b>Логи:</b> /var/log/flame-of-styx/ (системные логи)\n"
            status_text += "• <b>Отчеты безопасности:</b> reports/security/ (отчеты)\n\n"

            status_text += f"👑 <b>Администратор:</b> <code>{admin_id}</code>"

            return status_text

        except Exception as e:
            logger.error(f"Error getting bot status: {sanitize_for_logging(str(e))}")
            raise
