"""
Продвинутая система логирования для мониторинга
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.utils.windows_safe import is_windows, safe_log


class AdvancedLogger:
    """Продвинутый логгер с ротацией и мониторингом."""

    def __init__(self, name: str = "antispam_bot", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Создаем логгер
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Очищаем существующие хендлеры
        self.logger.handlers.clear()

        # Настраиваем форматирование
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Настраиваем хендлеры
        self._setup_handlers()

        # Счетчики для мониторинга
        self.counters = {"info": 0, "warning": 0, "error": 0, "critical": 0, "debug": 0}

    def _setup_handlers(self):
        """Настраивает хендлеры для логирования."""

        # 1. Консольный вывод
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

        # 2. Основной файл логов с ротацией
        main_log_file = self.log_dir / "bot.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
        )
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(self.formatter)
        self.logger.addHandler(main_handler)

        # 3. Файл ошибок
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 5MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.formatter)
        self.logger.addHandler(error_handler)

        # 4. Файл для мониторинга (JSON формат)
        monitor_log_file = self.log_dir / "monitor.log"
        monitor_handler = logging.handlers.RotatingFileHandler(
            monitor_log_file, maxBytes=20 * 1024 * 1024, backupCount=2, encoding="utf-8"  # 20MB
        )
        monitor_handler.setLevel(logging.INFO)
        monitor_handler.setFormatter(self.formatter)
        self.logger.addHandler(monitor_handler)

    def _log_with_counter(self, level: str, message: str, *args, **kwargs):
        """Логирует сообщение и увеличивает счетчик."""
        self.counters[level] += 1

        # Используем safe_log для Windows
        if is_windows():
            safe_log(self.logger, level, message)
        else:
            getattr(self.logger, level)(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Информационное сообщение."""
        self._log_with_counter("info", message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Предупреждение."""
        self._log_with_counter("warning", message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Ошибка."""
        self._log_with_counter("error", message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Критическая ошибка."""
        self._log_with_counter("critical", message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Отладочное сообщение."""
        self._log_with_counter("debug", message, *args, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику логирования."""
        return {
            "counters": self.counters.copy(),
            "total_logs": sum(self.counters.values()),
            "log_dir": str(self.log_dir),
            "log_files": [str(f) for f in self.log_dir.glob("*.log")],
        }

    def log_bot_event(self, event_type: str, data: Dict[str, Any]):
        """Логирует событие бота для мониторинга."""
        event_data = {"timestamp": datetime.now().isoformat(), "event_type": event_type, "data": data}

        self.info(f"BOT_EVENT: {event_type} - {data}")

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Логирует производительность операции."""
        perf_data = {"operation": operation, "duration_ms": round(duration * 1000, 2), **kwargs}

        self.info(f"PERFORMANCE: {operation} took {duration:.3f}s")

    def log_security_event(self, event: str, user_id: Optional[int] = None, **kwargs):
        """Логирует событие безопасности."""
        security_data = {"event": event, "user_id": user_id, "timestamp": datetime.now().isoformat(), **kwargs}

        self.warning(f"SECURITY: {event} - User: {user_id}")


# Глобальный экземпляр логгера
advanced_logger = AdvancedLogger()


def get_advanced_logger() -> AdvancedLogger:
    """Получить глобальный продвинутый логгер."""
    return advanced_logger


def setup_monitoring_logging():
    """Настраивает логирование для мониторинга."""
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Очищаем существующие хендлеры
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Добавляем наш продвинутый логгер
    root_logger.addHandler(advanced_logger.logger.handlers[0])

    return advanced_logger
