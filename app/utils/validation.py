"""
Расширенная валидация входных данных для AntiSpam Bot
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from aiogram.types import Message, CallbackQuery, User, Chat

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Уровни серьезности ошибок валидации"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationError:
    """Ошибка валидации"""
    field: str
    message: str
    severity: ValidationSeverity
    code: str
    value: Any = None


class InputValidator:
    """Класс для строгой валидации входных данных"""
    
    # Константы для валидации
    MAX_MESSAGE_LENGTH = 4096  # Telegram limit
    MAX_COMMAND_LENGTH = 32
    MAX_PARAMETER_LENGTH = 100
    MAX_USERNAME_LENGTH = 32
    MAX_FIRST_NAME_LENGTH = 64
    MAX_LAST_NAME_LENGTH = 64
    MAX_CHAT_TITLE_LENGTH = 255
    
    # Паттерны для валидации
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{5,32}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Подозрительные паттерны
    SUSPICIOUS_PATTERNS = [
        (r'<script[^>]*>.*?</script>', 'javascript_injection'),
        (r'javascript:', 'javascript_url'),
        (r'eval\s*\(', 'eval_function'),
        (r'\.\./', 'path_traversal'),
        (r'SELECT.*FROM', 'sql_injection'),
        (r'UNION.*SELECT', 'sql_union_injection'),
        (r'DROP\s+TABLE', 'sql_drop'),
        (r'INSERT\s+INTO', 'sql_insert'),
        (r'UPDATE\s+SET', 'sql_update'),
        (r'DELETE\s+FROM', 'sql_delete'),
        (r'<iframe[^>]*>', 'iframe_injection'),
        (r'on\w+\s*=', 'event_handler'),
        (r'data:text/html', 'data_url_html'),
        (r'vbscript:', 'vbscript_url'),
        (r'file://', 'file_url'),
        (r'ftp://', 'ftp_url'),
        (r'\\x[0-9a-fA-F]{2}', 'hex_encoding'),
        (r'%[0-9a-fA-F]{2}', 'url_encoding'),
        (r'\\u[0-9a-fA-F]{4}', 'unicode_encoding'),
    ]
    
    def __init__(self):
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.DOTALL), code)
            for pattern, code in self.SUSPICIOUS_PATTERNS
        ]
    
    def validate_message(self, message: Message) -> List[ValidationError]:
        """Валидирует сообщение Telegram"""
        errors = []
        
        # Базовые проверки
        errors.extend(self._validate_basic_message_fields(message))
        
        # Проверка текста
        if message.text:
            errors.extend(self._validate_text_content(message.text, "message_text"))
        
        # Проверка пользователя
        if message.from_user:
            errors.extend(self._validate_user(message.from_user))
        
        # Проверка чата
        if message.chat:
            errors.extend(self._validate_chat(message.chat))
        
        return errors
    
    def validate_callback_query(self, callback: CallbackQuery) -> List[ValidationError]:
        """Валидирует callback query"""
        errors = []
        
        # Базовые проверки
        if not callback.data:
            errors.append(ValidationError(
                field="callback_data",
                message="Отсутствуют данные callback",
                severity=ValidationSeverity.HIGH,
                code="missing_callback_data"
            ))
        else:
            errors.extend(self._validate_text_content(callback.data, "callback_data"))
        
        # Проверка пользователя
        if callback.from_user:
            errors.extend(self._validate_user(callback.from_user))
        
        return errors
    
    def validate_command(self, command: str, args: List[str]) -> List[ValidationError]:
        """Валидирует команду и её параметры"""
        errors = []
        
        # Проверка команды
        if not command:
            errors.append(ValidationError(
                field="command",
                message="Отсутствует команда",
                severity=ValidationSeverity.CRITICAL,
                code="missing_command"
            ))
        else:
            # Для команд не применяем подозрительные паттерны, только базовые проверки
            if not isinstance(command, str):
                errors.append(ValidationError(
                    field="command",
                    message="Команда должна быть строкой",
                    severity=ValidationSeverity.HIGH,
                    code="invalid_command_type",
                    value=type(command).__name__
                ))
            elif len(command) > self.MAX_COMMAND_LENGTH:
                errors.append(ValidationError(
                    field="command",
                    message=f"Команда слишком длинная (максимум {self.MAX_COMMAND_LENGTH} символов)",
                    severity=ValidationSeverity.HIGH,
                    code="command_too_long",
                    value=len(command)
                ))
            elif not command.startswith('/'):
                errors.append(ValidationError(
                    field="command",
                    message="Команда должна начинаться с '/'",
                    severity=ValidationSeverity.HIGH,
                    code="invalid_command_format",
                    value=command
                ))
        
        # Проверка параметров
        for i, arg in enumerate(args):
            errors.extend(self._validate_text_content(arg, f"arg_{i}"))
            
            if len(arg) > self.MAX_PARAMETER_LENGTH:
                errors.append(ValidationError(
                    field=f"arg_{i}",
                    message=f"Параметр слишком длинный (максимум {self.MAX_PARAMETER_LENGTH} символов)",
                    severity=ValidationSeverity.MEDIUM,
                    code="parameter_too_long",
                    value=len(arg)
                ))
        
        return errors
    
    def _validate_basic_message_fields(self, message: Message) -> List[ValidationError]:
        """Валидирует базовые поля сообщения"""
        errors = []
        
        if not message.chat:
            errors.append(ValidationError(
                field="chat",
                message="Отсутствует информация о чате",
                severity=ValidationSeverity.CRITICAL,
                code="missing_chat"
            ))
        elif not message.chat.id:
            errors.append(ValidationError(
                field="chat_id",
                message="Отсутствует ID чата",
                severity=ValidationSeverity.CRITICAL,
                code="missing_chat_id"
            ))
        
        if not message.from_user and not message.sender_chat:
            errors.append(ValidationError(
                field="sender",
                message="Отсутствует информация об отправителе",
                severity=ValidationSeverity.HIGH,
                code="missing_sender"
            ))
        
        return errors
    
    def _validate_text_content(self, text: str, field_name: str) -> List[ValidationError]:
        """Валидирует текстовое содержимое"""
        errors = []
        
        if not isinstance(text, str):
            errors.append(ValidationError(
                field=field_name,
                message="Текст должен быть строкой",
                severity=ValidationSeverity.HIGH,
                code="invalid_text_type",
                value=type(text).__name__
            ))
            return errors
        
        # Проверка длины
        if len(text) > self.MAX_MESSAGE_LENGTH:
            errors.append(ValidationError(
                field=field_name,
                message=f"Текст слишком длинный (максимум {self.MAX_MESSAGE_LENGTH} символов)",
                severity=ValidationSeverity.MEDIUM,
                code="text_too_long",
                value=len(text)
            ))
        
        # Проверка на подозрительные паттерны
        for pattern, code in self.compiled_patterns:
            if pattern.search(text):
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Обнаружен подозрительный паттерн: {code}",
                    severity=ValidationSeverity.HIGH,
                    code=code,
                    value=text[:100] + "..." if len(text) > 100 else text
                ))
        
        # Проверка на пустые строки
        if not text.strip():
            errors.append(ValidationError(
                field=field_name,
                message="Текст не может быть пустым",
                severity=ValidationSeverity.LOW,
                code="empty_text"
            ))
        
        return errors
    
    def _validate_user(self, user: User) -> List[ValidationError]:
        """Валидирует пользователя"""
        errors = []
        
        if not user.id:
            errors.append(ValidationError(
                field="user_id",
                message="Отсутствует ID пользователя",
                severity=ValidationSeverity.CRITICAL,
                code="missing_user_id"
            ))
        elif not isinstance(user.id, int) or user.id <= 0:
            errors.append(ValidationError(
                field="user_id",
                message="Некорректный ID пользователя",
                severity=ValidationSeverity.HIGH,
                code="invalid_user_id",
                value=user.id
            ))
        
        # Проверка имени
        if user.first_name:
            if len(user.first_name) > self.MAX_FIRST_NAME_LENGTH:
                errors.append(ValidationError(
                    field="first_name",
                    message=f"Имя слишком длинное (максимум {self.MAX_FIRST_NAME_LENGTH} символов)",
                    severity=ValidationSeverity.MEDIUM,
                    code="first_name_too_long",
                    value=len(user.first_name)
                ))
            
            # Проверка на подозрительные символы в имени
            if not re.match(r'^[a-zA-Zа-яА-Я\s\-\.\']+$', user.first_name):
                errors.append(ValidationError(
                    field="first_name",
                    message="Имя содержит недопустимые символы",
                    severity=ValidationSeverity.MEDIUM,
                    code="invalid_first_name_chars",
                    value=user.first_name
                ))
        
        # Проверка фамилии
        if user.last_name:
            if len(user.last_name) > self.MAX_LAST_NAME_LENGTH:
                errors.append(ValidationError(
                    field="last_name",
                    message=f"Фамилия слишком длинная (максимум {self.MAX_LAST_NAME_LENGTH} символов)",
                    severity=ValidationSeverity.MEDIUM,
                    code="last_name_too_long",
                    value=len(user.last_name)
                ))
            
            # Проверка на подозрительные символы в фамилии
            if not re.match(r'^[a-zA-Zа-яА-Я\s\-\.\']+$', user.last_name):
                errors.append(ValidationError(
                    field="last_name",
                    message="Фамилия содержит недопустимые символы",
                    severity=ValidationSeverity.MEDIUM,
                    code="invalid_last_name_chars",
                    value=user.last_name
                ))
        
        # Проверка username
        if user.username:
            if len(user.username) > self.MAX_USERNAME_LENGTH:
                errors.append(ValidationError(
                    field="username",
                    message=f"Username слишком длинный (максимум {self.MAX_USERNAME_LENGTH} символов)",
                    severity=ValidationSeverity.MEDIUM,
                    code="username_too_long",
                    value=len(user.username)
                ))
            
            if not self.USERNAME_PATTERN.match(user.username):
                errors.append(ValidationError(
                    field="username",
                    message="Username содержит недопустимые символы",
                    severity=ValidationSeverity.MEDIUM,
                    code="invalid_username_chars",
                    value=user.username
                ))
        
        return errors
    
    def _validate_chat(self, chat: Chat) -> List[ValidationError]:
        """Валидирует чат"""
        errors = []
        
        if not chat.id:
            errors.append(ValidationError(
                field="chat_id",
                message="Отсутствует ID чата",
                severity=ValidationSeverity.CRITICAL,
                code="missing_chat_id"
            ))
        elif not isinstance(chat.id, int):
            errors.append(ValidationError(
                field="chat_id",
                message="ID чата должен быть числом",
                severity=ValidationSeverity.HIGH,
                code="invalid_chat_id_type",
                value=type(chat.id).__name__
            ))
        
        # Проверка названия чата
        if chat.title:
            if len(chat.title) > self.MAX_CHAT_TITLE_LENGTH:
                errors.append(ValidationError(
                    field="chat_title",
                    message=f"Название чата слишком длинное (максимум {self.MAX_CHAT_TITLE_LENGTH} символов)",
                    severity=ValidationSeverity.MEDIUM,
                    code="chat_title_too_long",
                    value=len(chat.title)
                ))
            
            # Проверка на подозрительные символы в названии
            if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-\.\']+$', chat.title):
                errors.append(ValidationError(
                    field="chat_title",
                    message="Название чата содержит недопустимые символы",
                    severity=ValidationSeverity.MEDIUM,
                    code="invalid_chat_title_chars",
                    value=chat.title
                ))
        
        return errors
    
    def validate_phone_number(self, phone: str) -> List[ValidationError]:
        """Валидирует номер телефона"""
        errors = []
        
        if not phone:
            errors.append(ValidationError(
                field="phone",
                message="Отсутствует номер телефона",
                severity=ValidationSeverity.HIGH,
                code="missing_phone"
            ))
        elif not self.PHONE_PATTERN.match(phone):
            errors.append(ValidationError(
                field="phone",
                message="Некорректный формат номера телефона",
                severity=ValidationSeverity.MEDIUM,
                code="invalid_phone_format",
                value=phone
            ))
        
        return errors
    
    def validate_email(self, email: str) -> List[ValidationError]:
        """Валидирует email"""
        errors = []
        
        if not email:
            errors.append(ValidationError(
                field="email",
                message="Отсутствует email",
                severity=ValidationSeverity.HIGH,
                code="missing_email"
            ))
        elif not self.EMAIL_PATTERN.match(email):
            errors.append(ValidationError(
                field="email",
                message="Некорректный формат email",
                severity=ValidationSeverity.MEDIUM,
                code="invalid_email_format",
                value=email
            ))
        
        return errors


# Глобальный экземпляр валидатора
input_validator = InputValidator()
