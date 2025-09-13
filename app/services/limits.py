"""Сервис для управления лимитами системы."""

import json
import logging
import os
from typing import Any, Dict

from app.config import load_config

logger = logging.getLogger(__name__)


class LimitsService:
    """Сервис для управления лимитами системы."""

    def __init__(self):
        self.config = load_config()
        self.limits_file = "limits.json"
        self._cached_limits = None
        self._last_file_mtime = 0

    def get_current_limits(self) -> Dict[str, Any]:
        """Получить текущие лимиты с поддержкой hot-reload."""
        # Проверяем, нужно ли обновить кэш
        if self._should_reload_limits():
            self._cached_limits = self._load_limits()

        return self._cached_limits or {
            "max_messages_per_minute": self.config.max_messages_per_minute,
            "max_links_per_message": self.config.max_links_per_message,
            "ban_duration_hours": self.config.ban_duration_hours,
            "suspicion_threshold": self.config.suspicion_threshold,
        }

    def update_limit(self, limit_name: str, value: Any) -> bool:
        """Обновить лимит."""
        try:
            # Загружаем текущие лимиты
            limits = self._load_limits()

            # Обновляем лимит
            limits[limit_name] = value

            # Сохраняем в файл
            self._save_limits(limits)

            logger.info(f"Limit {limit_name} updated to {value}")
            return True

        except Exception as e:
            logger.error(f"Error updating limit {limit_name}: {e}")
            return False

    def _load_limits(self) -> Dict[str, Any]:
        """Загрузить лимиты из файла."""
        try:
            with open(self.limits_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Если файл не существует, создаем с дефолтными значениями
            return self.get_current_limits()
        except Exception as e:
            logger.error(f"Error loading limits: {e}")
            return self.get_current_limits()

    def _save_limits(self, limits: Dict[str, Any]) -> None:
        """Сохранить лимиты в файл."""
        try:
            with open(self.limits_file, "w", encoding="utf-8") as f:
                json.dump(limits, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving limits: {e}")
            raise

    def _should_reload_limits(self) -> bool:
        """Проверить, нужно ли перезагрузить лимиты."""
        try:
            if not os.path.exists(self.limits_file):
                return False

            current_mtime = os.path.getmtime(self.limits_file)
            if current_mtime > self._last_file_mtime:
                self._last_file_mtime = current_mtime
                return True
        except Exception as e:
            logger.error(f"Ошибка проверки времени модификации файла: {e}")

        return False

    def reload_limits(self) -> bool:
        """Принудительно перезагрузить лимиты из файла."""
        try:
            self._cached_limits = self._load_limits()
            logger.info("Лимиты перезагружены из файла")
            return True
        except Exception as e:
            logger.error(f"Ошибка перезагрузки лимитов: {e}")
            return False

    def get_limits_display(self) -> str:
        """Получить отображение лимитов для пользователя."""
        limits = self.get_current_limits()

        return (
            "📊 <b>Текущие лимиты:</b>\n"
            f"• Максимум сообщений в минуту: {limits['max_messages_per_minute']}\n"
            f"• Максимум ссылок в сообщении: {limits['max_links_per_message']}\n"
            f"• Время блокировки: {limits['ban_duration_hours']} часов\n"
            f"• Порог подозрительности: {limits['suspicion_threshold']}\n\n"
            "ℹ️ Для изменения лимитов используйте команды:\n"
            "• /setlimit messages &lt;число&gt; - изменить лимит сообщений\n"
            "• /setlimit links &lt;число&gt; - изменить лимит ссылок\n"
            "• /setlimit ban &lt;часы&gt; - изменить время блокировки\n"
            "• /setlimit threshold &lt;число&gt; - изменить порог подозрительности\n\n"
            "🔄 <b>Hot-reload:</b> Изменения в limits.json применяются автоматически!"
        )
