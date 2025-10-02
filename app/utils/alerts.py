"""
Система алертов для мониторинга бота
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.config import load_config

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Уровни алертов."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Структура алерта."""

    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    data: Optional[Dict[str, Any]] = None


class AlertManager:
    """Менеджер алертов."""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.rate_limits: Dict[str, datetime] = {}
        self.config = load_config()

    def add_handler(self, handler: Callable[[Alert], None]):
        """Добавляет обработчик алертов."""
        self.alert_handlers.append(handler)

    async def send_alert(self, alert: Alert):
        """Отправляет алерт."""
        # Проверяем rate limit
        if self._is_rate_limited(alert):
            logger.debug(f"Alert rate limited: {alert.title}")
            return

        # Добавляем в список
        self.alerts.append(alert)

        # Ограничиваем количество алертов
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-500:]

        # Отправляем обработчикам
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

        logger.info(f"Alert sent: {alert.level.value} - {alert.title}")

    def _is_rate_limited(self, alert: Alert) -> bool:
        """Проверяет rate limit для алерта."""
        key = f"{alert.source}:{alert.level.value}"
        now = datetime.now()

        if key in self.rate_limits:
            last_alert = self.rate_limits[key]
            # Rate limit: 1 алерт в минуту для одного источника и уровня
            if now - last_alert < timedelta(minutes=1):
                return True

        self.rate_limits[key] = now
        return False

    def create_alert(
        self, level: AlertLevel, title: str, message: str, source: str, data: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Создает алерт."""
        return Alert(level=level, title=title, message=message, timestamp=datetime.now(), source=source, data=data)

    async def alert_bot_started(self, commit_id: str):
        """Алерт о запуске бота."""
        alert = self.create_alert(
            level=AlertLevel.INFO,
            title="🤖 Bot Started",
            message=f"AntiSpam Bot started successfully. Commit: {commit_id}",
            source="bot_startup",
            data={"commit_id": commit_id},
        )
        await self.send_alert(alert)

    async def alert_bot_stopped(self, reason: str = "Unknown"):
        """Алерт об остановке бота."""
        alert = self.create_alert(
            level=AlertLevel.WARNING,
            title="🛑 Bot Stopped",
            message=f"AntiSpam Bot stopped. Reason: {reason}",
            source="bot_shutdown",
            data={"reason": reason},
        )
        await self.send_alert(alert)

    async def alert_high_cpu_usage(self, cpu_percent: float):
        """Алерт о высокой загрузке CPU."""
        alert = self.create_alert(
            level=AlertLevel.WARNING,
            title="⚠️ High CPU Usage",
            message=f"CPU usage is {cpu_percent:.1f}%",
            source="system_monitor",
            data={"cpu_percent": cpu_percent},
        )
        await self.send_alert(alert)

    async def alert_high_memory_usage(self, memory_percent: float):
        """Алерт о высоком использовании памяти."""
        alert = self.create_alert(
            level=AlertLevel.WARNING,
            title="⚠️ High Memory Usage",
            message=f"Memory usage is {memory_percent:.1f}%",
            source="system_monitor",
            data={"memory_percent": memory_percent},
        )
        await self.send_alert(alert)

    async def alert_database_error(self, error: str):
        """Алерт об ошибке базы данных."""
        alert = self.create_alert(
            level=AlertLevel.ERROR,
            title="❌ Database Error",
            message=f"Database error: {error}",
            source="database",
            data={"error": error},
        )
        await self.send_alert(alert)

    async def alert_redis_error(self, error: str):
        """Алерт об ошибке Redis."""
        alert = self.create_alert(
            level=AlertLevel.ERROR,
            title="❌ Redis Error",
            message=f"Redis error: {error}",
            source="redis",
            data={"error": error},
        )
        await self.send_alert(alert)

    async def alert_telegram_error(self, error: str):
        """Алерт об ошибке Telegram API."""
        alert = self.create_alert(
            level=AlertLevel.ERROR,
            title="❌ Telegram API Error",
            message=f"Telegram API error: {error}",
            source="telegram_api",
            data={"error": error},
        )
        await self.send_alert(alert)

    async def alert_suspicious_activity(self, user_id: int, reason: str):
        """Алерт о подозрительной активности."""
        alert = self.create_alert(
            level=AlertLevel.WARNING,
            title="🔍 Suspicious Activity",
            message=f"Suspicious activity detected from user {user_id}: {reason}",
            source="antispam",
            data={"user_id": user_id, "reason": reason},
        )
        await self.send_alert(alert)

    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Получает недавние алерты."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp > cutoff]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Получает статистику алертов."""
        recent_alerts = self.get_recent_alerts(24)

        stats = {
            "total_alerts_24h": len(recent_alerts),
            "by_level": {},
            "by_source": {},
            "recent_critical": len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
        }

        for alert in recent_alerts:
            level = alert.level.value
            source = alert.source

            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        return stats


# Глобальный менеджер алертов
alert_manager = AlertManager()


async def telegram_alert_handler(alert: Alert):
    """Обработчик алертов через Telegram."""
    try:
        from aiogram import Bot

        from app.config import load_config

        config = load_config()
        bot = Bot(token=config.bot_token)

        # Формируем сообщение
        emoji_map = {AlertLevel.INFO: "ℹ️", AlertLevel.WARNING: "⚠️", AlertLevel.ERROR: "❌", AlertLevel.CRITICAL: "🚨"}

        emoji = emoji_map.get(alert.level, "📢")
        message = f"{emoji} <b>{alert.title}</b>\n\n{alert.message}\n\n<i>Source: {alert.source}</i>"

        # Отправляем админам
        for admin_id in config.admin_ids_list:
            try:
                await bot.send_message(admin_id, message)
            except Exception as e:
                logger.error(f"Failed to send alert to admin {admin_id}: {e}")

        await bot.session.close()

    except Exception as e:
        logger.error(f"Error in telegram alert handler: {e}")


def setup_alerts():
    """Настраивает систему алертов."""
    # Добавляем обработчик Telegram
    alert_manager.add_handler(telegram_alert_handler)

    logger.info("Alert system configured")


def get_alert_manager() -> AlertManager:
    """Получить глобальный менеджер алертов."""
    return alert_manager
