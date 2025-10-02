"""
Защита персональных данных в логах.

Реализует систему двойного логирования:
1. Общие логи без ПД для мониторинга
2. Полные логи с ПД для анализа спама (зашифрованные)
"""

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class PIIProtector:
    """Защита персональных данных в логах."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Инициализация защитника ПД."""
        self.encryption_key = encryption_key or self._generate_key()
        self.cipher = Fernet(self.encryption_key.encode())

        # Паттерны для поиска ПД
        self.pii_patterns = {
            "phone": r"(\+?[1-9]\d{1,14})",  # Телефоны
            "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # Email
            "username": r"@([a-zA-Z0-9_]{5,32})",  # Username
            "user_id": r"user_id[:\s=]+(\d+)",  # User ID
            "chat_id": r"chat_id[:\s=]+(-?\d+)",  # Chat ID
            "first_name": r"first_name[:\s=]+([^\s,]+)",  # Имя
            "last_name": r"last_name[:\s=]+([^\s,]+)",  # Фамилия
        }

        # Словарь для замены ПД
        self.pii_replacements = {}

    def _generate_key(self) -> str:
        """Генерирует ключ шифрования."""
        return Fernet.generate_key().decode()

    def _hash_pii(self, value: str) -> str:
        """Хеширует ПД для анонимизации."""
        return hashlib.sha256(value.encode()).hexdigest()[:8]

    def _encrypt_pii(self, data: str) -> str:
        """Шифрует ПД."""
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Ошибка шифрования ПД: {e}")
            return data

    def _decrypt_pii(self, encrypted_data: str) -> str:
        """Расшифровывает ПД."""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Ошибка расшифровки ПД: {e}")
            return encrypted_data

    def protect_pii(self, text: str) -> str:
        """Защищает ПД в тексте."""
        protected_text = text

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, protected_text)
            for match in matches:
                if match not in self.pii_replacements:
                    self.pii_replacements[match] = f"[{pii_type.upper()}_{self._hash_pii(match)}]"
                protected_text = protected_text.replace(match, self.pii_replacements[match])

        return protected_text

    def extract_pii(self, text: str) -> Dict[str, List[str]]:
        """Извлекает ПД из текста."""
        pii_data = {}

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                pii_data[pii_type] = list(set(matches))

        return pii_data

    def create_secure_log_entry(
        self,
        message: str,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Создает защищенную запись лога."""
        # Извлекаем ПД
        pii_data = self.extract_pii(message)
        if user_id:
            pii_data["user_id"] = [str(user_id)]
        if chat_id:
            pii_data["chat_id"] = [str(chat_id)]

        # Создаем защищенное сообщение
        protected_message = self.protect_pii(message)

        # Создаем запись
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "protected_message": protected_message,
            "pii_count": len(pii_data),
            "pii_types": list(pii_data.keys()),
            "additional_data": additional_data or {},
        }

        # Если есть ПД, создаем полную запись для анализа спама
        if pii_data:
            full_entry = {
                "timestamp": datetime.now().isoformat(),
                "original_message": message,
                "user_id": user_id,
                "chat_id": chat_id,
                "pii_data": pii_data,
                "additional_data": additional_data or {},
            }

            # Шифруем полную запись
            encrypted_entry = self._encrypt_pii(json.dumps(full_entry, ensure_ascii=False))
            log_entry["encrypted_full_data"] = encrypted_entry

        return log_entry

    def decrypt_log_entry(self, encrypted_data: str) -> Dict[str, Any]:
        """Расшифровывает запись лога."""
        try:
            decrypted_data = self._decrypt_pii(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            logger.error(f"Ошибка расшифровки записи лога: {e}")
            return {}


class SecureLogger:
    """Безопасный логгер с защитой ПД."""

    def __init__(self, name: str, pii_protector: Optional[PIIProtector] = None, enable_full_logging: bool = False):
        """Инициализация безопасного логгера."""
        self.logger = logging.getLogger(name)
        self.pii_protector = pii_protector or PIIProtector()
        self.enable_full_logging = enable_full_logging

        # Определяем пути логов в зависимости от окружения
        self._setup_log_paths()

        # Настройка обработчиков
        self._setup_handlers()

    def _setup_log_paths(self):
        """Настраивает пути логов в зависимости от окружения."""
        environment = os.getenv("ENVIRONMENT", "development")

        if environment == "production":
            # Продакшн пути
            self.logs_base_dir = Path("/var/log/flame-of-styx")
            self.app_logs_dir = Path("/opt/flame-of-styx/logs")
        else:
            # Разработка
            self.logs_base_dir = Path("logs")
            self.app_logs_dir = Path("logs")

        # Конкретные пути
        self.general_logs_dir = self.logs_base_dir / "general"
        self.encrypted_logs_dir = self.logs_base_dir / "encrypted"
        self.security_logs_dir = self.logs_base_dir / "security"
        self.reports_dir = self.logs_base_dir / "reports"

        # Создаем директории если не существуют
        for dir_path in [self.general_logs_dir, self.encrypted_logs_dir, self.security_logs_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _setup_handlers(self):
        """Настраивает обработчики логов."""
        # Обработчик для общих логов (без ПД)
        general_log_file = self.general_logs_dir / "general.log"

        # Убеждаемся что файл существует и имеет правильные права
        try:
            general_log_file.touch(mode=0o644)
        except PermissionError:
            # Если не можем создать файл, используем временный
            general_log_file = self.general_logs_dir / "general_temp.log"
            general_log_file.touch(mode=0o644)

        general_handler = logging.FileHandler(general_log_file, encoding="utf-8")
        general_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        general_handler.setFormatter(general_formatter)
        general_handler.setLevel(logging.INFO)

        # Обработчик для полных логов (с ПД, зашифрованные)
        if self.enable_full_logging:
            encrypted_log_file = self.encrypted_logs_dir / "full_encrypted.log"
            full_handler = logging.FileHandler(encrypted_log_file, encoding="utf-8")
            full_handler.setLevel(logging.DEBUG)

            self.logger.addHandler(full_handler)

        self.logger.addHandler(general_handler)
        self.logger.setLevel(logging.INFO)

    def log_message(
        self,
        message: str,
        level: int = logging.INFO,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """Логирует сообщение с защитой ПД."""
        # Создаем защищенную запись
        log_entry = self.pii_protector.create_secure_log_entry(message, user_id, chat_id, additional_data)

        # Логируем защищенное сообщение
        protected_message = log_entry["protected_message"]
        self.logger.log(level, protected_message)

        # Если включено полное логирование, логируем зашифрованные данные
        if self.enable_full_logging and "encrypted_full_data" in log_entry:
            self.logger.debug(f"ENCRYPTED_DATA: {log_entry['encrypted_full_data']}")

    def log_spam_analysis(self, message: str, user_id: int, chat_id: int, analysis_result: Dict[str, Any]):
        """Логирует данные для анализа спама."""
        additional_data = {"analysis_result": analysis_result, "log_type": "spam_analysis"}

        self.log_message(
            message=message, level=logging.DEBUG, user_id=user_id, chat_id=chat_id, additional_data=additional_data
        )

    def get_spam_analysis_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получает данные для анализа спама за указанный период."""
        if not self.enable_full_logging:
            return []

        try:
            # Читаем зашифрованные логи
            log_file = self.encrypted_logs_dir / "full_encrypted.log"
            if not log_file.exists():
                return []

            decrypted_entries = []
            cutoff_date = datetime.now() - timedelta(days=days)

            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "ENCRYPTED_DATA:" in line:
                        encrypted_data = line.split("ENCRYPTED_DATA: ")[1].strip()
                        try:
                            decrypted_entry = self.pii_protector.decrypt_log_entry(encrypted_data)
                            if decrypted_entry.get("additional_data", {}).get("log_type") == "spam_analysis":
                                entry_date = datetime.fromisoformat(decrypted_entry["timestamp"])
                                if entry_date >= cutoff_date:
                                    decrypted_entries.append(decrypted_entry)
                        except Exception as e:
                            logger.error(f"Ошибка расшифровки записи: {e}")
                            continue

            return decrypted_entries

        except Exception as e:
            logger.error(f"Ошибка получения данных для анализа спама: {e}")
            return []

    def cleanup_old_logs(self, days: int = 90):
        """Очищает старые логи."""
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                return

            cutoff_date = datetime.now() - timedelta(days=days)

            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.info(f"Удален старый лог: {log_file}")

        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")


# Глобальный экземпляр защитника ПД
pii_protector = PIIProtector()

# Глобальный безопасный логгер
secure_logger = SecureLogger(
    name="flame_of_styx_bot",
    pii_protector=pii_protector,
    enable_full_logging=True,  # Включаем полное логирование для анализа спама
)
