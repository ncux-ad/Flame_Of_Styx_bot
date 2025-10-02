"""
Конфигурация логирования для разных окружений.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict


def get_logging_config() -> Dict[str, Any]:
    """Возвращает конфигурацию логирования в зависимости от окружения."""

    environment = os.getenv("ENVIRONMENT", "development")

    # Базовые пути
    if environment == "production":
        logs_base_dir = Path("/var/log/flame-of-styx")
        app_logs_dir = Path("/opt/flame-of-styx/logs")
    else:
        logs_base_dir = Path("logs")
        app_logs_dir = Path("logs")

    # Создаем директории
    for dir_path in [logs_base_dir, app_logs_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Конфигурация логирования
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "datefmt": "%Y-%m-%d %H:%M:%S"},
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "general_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": str(logs_base_dir / "general" / "general.log"),
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(logs_base_dir / "general" / "error.log"),
                "maxBytes": 5 * 1024 * 1024,  # 5MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(logs_base_dir / "security" / "security.log"),
                "maxBytes": 5 * 1024 * 1024,  # 5MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "flame_of_styx_bot": {"level": "INFO", "handlers": ["console", "general_file", "error_file"], "propagate": False},
            "app.utils.pii_protection": {"level": "DEBUG", "handlers": ["general_file", "security_file"], "propagate": False},
            "app.services.links": {"level": "INFO", "handlers": ["general_file"], "propagate": False},
            "app.services.profiles": {"level": "INFO", "handlers": ["general_file"], "propagate": False},
            "app.handlers.admin.spam_analysis": {
                "level": "INFO",
                "handlers": ["general_file", "security_file"],
                "propagate": False,
            },
        },
        "root": {"level": "WARNING", "handlers": ["console", "error_file"]},
    }

    # Дополнительные настройки для продакшна
    if environment == "production":
        # В продакшне убираем консольный вывод
        config["handlers"]["console"]["level"] = "WARNING"

        # Добавляем обработчик для системных логов
        config["handlers"]["system_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(logs_base_dir / "general" / "system.log"),
            "maxBytes": 20 * 1024 * 1024,  # 20MB
            "backupCount": 10,
            "encoding": "utf-8",
        }

        # Обновляем root logger для продакшна
        config["root"]["handlers"] = ["system_file", "error_file"]

    return config


def setup_logging():
    """Настраивает логирование для приложения."""
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Логируем информацию о настройке
    logger = logging.getLogger("flame_of_styx_bot")
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Логирование настроено для окружения: {environment}")


# Импортируем logging.config для использования в setup_logging
import logging.config
