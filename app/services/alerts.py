"""
Сервис для отправки уведомлений администраторам
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from app.config import Settings
from app.utils.security import sanitize_for_logging


class AlertLevel(Enum):
    """Уровни алертов"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class AlertType(Enum):
    """Типы алертов"""

    SYSTEM_ERROR = "system_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BAN_ACTION = "ban_action"
    CHANNEL_JOINED = "channel_joined"
    BOT_STATUS = "bot_status"
    DATABASE_ERROR = "database_error"
    REDIS_ERROR = "redis_error"


@dataclass
class Alert:
    """Структура алерта"""

    level: AlertLevel
    alert_type: AlertType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertService:
    """Сервис для отправки уведомлений администраторам"""

    def __init__(self, bot: Bot, config: Settings):
        self.bot = bot
        self.config = config
        self.admin_ids = config.admin_ids_list
        self.alert_queue: List[Alert] = []
        self.rate_limits: Dict[int, datetime] = {}  # user_id -> last_alert_time
        self.min_alert_interval = 60  # секунд между алертами для одного админа

    async def send_alert(
        self,
        level: AlertLevel,
        alert_type: AlertType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        admin_ids: Optional[List[int]] = None,
    ) -> bool:
        """Отправить алерт администраторам"""
        try:
            alert = Alert(level=level, alert_type=alert_type, title=title, message=message, data=data)

            # Добавляем в очередь
            self.alert_queue.append(alert)

            # Отправляем алерт
            return await self._send_alert_to_admins(alert, admin_ids)

        except Exception as e:
            print(f"Ошибка отправки алерта: {e}")
            return False

    async def _send_alert_to_admins(self, alert: Alert, admin_ids: Optional[List[int]] = None) -> bool:
        """Отправить алерт конкретным админам"""
        if admin_ids is None:
            admin_ids = self.admin_ids

        if not admin_ids:
            return False

        success_count = 0

        for admin_id in admin_ids:
            try:
                # Проверяем rate limit
                if not self._check_rate_limit(admin_id):
                    continue

                # Форматируем сообщение
                formatted_message = self._format_alert_message(alert)

                # Отправляем сообщение
                await self.bot.send_message(chat_id=admin_id, text=formatted_message, parse_mode="HTML")

                # Обновляем rate limit
                self.rate_limits[admin_id] = datetime.now()
                success_count += 1

            except TelegramBadRequest as e:
                print(f"Ошибка отправки алерта админу {admin_id}: {e}")
                continue
            except Exception as e:
                print(f"Неожиданная ошибка при отправке алерта админу {admin_id}: {e}")
                continue

        return success_count > 0

    def _check_rate_limit(self, admin_id: int) -> bool:
        """Проверить rate limit для админа"""
        if admin_id not in self.rate_limits:
            return True

        last_alert = self.rate_limits[admin_id]
        time_diff = (datetime.now() - last_alert).total_seconds()

        return time_diff >= self.min_alert_interval

    def _format_alert_message(self, alert: Alert) -> str:
        """Форматировать сообщение алерта"""
        # Эмодзи для разных уровней
        level_emojis = {AlertLevel.ERROR: "🔴", AlertLevel.WARNING: "⚠️", AlertLevel.INFO: "ℹ️", AlertLevel.SUCCESS: "✅"}

        # Эмодзи для разных типов
        type_emojis = {
            AlertType.SYSTEM_ERROR: "💥",
            AlertType.RATE_LIMIT_EXCEEDED: "🚫",
            AlertType.SUSPICIOUS_ACTIVITY: "👁️",
            AlertType.BAN_ACTION: "🔨",
            AlertType.CHANNEL_JOINED: "➕",
            AlertType.BOT_STATUS: "🤖",
            AlertType.DATABASE_ERROR: "🗄️",
            AlertType.REDIS_ERROR: "🔴",
        }

        level_emoji = level_emojis.get(alert.level, "ℹ️")
        type_emoji = type_emojis.get(alert.alert_type, "ℹ️")

        # Форматируем время
        time_str = alert.timestamp.strftime("%H:%M:%S")

        # Создаем сообщение
        message = f"{level_emoji} <b>{alert.title}</b>\n"
        message += f"{type_emoji} <i>{alert.alert_type.value}</i>\n"
        message += f"🕐 {time_str}\n\n"
        message += f"{alert.message}"

        # Добавляем дополнительные данные если есть
        if alert.data:
            message += "\n\n📊 <b>Дополнительно:</b>"
            for key, value in alert.data.items():
                safe_value = sanitize_for_logging(str(value))
                message += f"\n• {key}: {safe_value}"

        return message

    async def send_error_alert(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Отправить алерт об ошибке"""
        return await self.send_alert(
            level=AlertLevel.ERROR, alert_type=AlertType.SYSTEM_ERROR, title=title, message=message, data=data
        )

    async def send_warning_alert(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Отправить предупреждение"""
        return await self.send_alert(
            level=AlertLevel.WARNING, alert_type=AlertType.SUSPICIOUS_ACTIVITY, title=title, message=message, data=data
        )

    async def send_info_alert(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Отправить информационное сообщение"""
        return await self.send_alert(
            level=AlertLevel.INFO, alert_type=AlertType.BOT_STATUS, title=title, message=message, data=data
        )

    async def send_success_alert(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Отправить сообщение об успехе"""
        return await self.send_alert(
            level=AlertLevel.SUCCESS, alert_type=AlertType.BAN_ACTION, title=title, message=message, data=data
        )

    async def get_alert_stats(self) -> Dict[str, Any]:
        """Получить статистику алертов"""
        return {
            "total_alerts": len(self.alert_queue),
            "recent_alerts": len([a for a in self.alert_queue if (datetime.now() - a.timestamp).total_seconds() < 3600]),
            "admin_count": len(self.admin_ids),
            "rate_limited_admins": len(self.rate_limits),
        }
