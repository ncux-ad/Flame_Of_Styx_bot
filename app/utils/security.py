"""
Утилиты безопасности для AntiSpam Bot
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from app.constants import SENSITIVE_PATTERNS, MAX_LOG_MESSAGE_LENGTH

logger = logging.getLogger(__name__)


def sanitize_for_logging(message: str) -> str:
    """
    Санитизирует сообщение для безопасного логирования.
    
    Удаляет чувствительные данные (токены, пароли, секреты) из сообщений.
    
    Args:
        message: Исходное сообщение
        
    Returns:
        Санитизированное сообщение
    """
    if not isinstance(message, str):
        return str(message)
    
    sanitized = message
    
    # Удаляем чувствительные данные
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    
    # Ограничиваем длину сообщения
    if len(sanitized) > MAX_LOG_MESSAGE_LENGTH:
        sanitized = sanitized[:MAX_LOG_MESSAGE_LENGTH] + "..."
    
    return sanitized


def sanitize_user_input(user_input: str) -> str:
    """
    Санитизирует пользовательский ввод.
    
    Удаляет потенциально опасные конструкции.
    
    Args:
        user_input: Пользовательский ввод
        
    Returns:
        Санитизированный ввод
    """
    if not isinstance(user_input, str):
        return str(user_input)
    
    # Удаляем HTML теги
    sanitized = re.sub(r'<[^>]+>', '', user_input)
    
    # Удаляем SQL инъекции
    sql_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\'|\"|;|--|\/\*|\*\/)',
    ]
    
    for pattern in sql_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Удаляем пути к файлам
    sanitized = re.sub(r'\.\.\/', '', sanitized)
    sanitized = re.sub(r'\.\.\\', '', sanitized)
    
    # Удаляем JavaScript
    js_patterns = [
        r'<script[^>]*>.*?<\/script>',
        r'javascript:',
        r'eval\(',
        r'alert\(',
        r'confirm\(',
        r'prompt\(',
    ]
    
    for pattern in js_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Удаляем лишние пробелы
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def validate_bot_token(token: str) -> bool:
    """
    Валидирует токен бота.
    
    Args:
        token: Токен для проверки
        
    Returns:
        True если токен валидный, False иначе
    """
    if not isinstance(token, str):
        return False
    
    # Проверяем базовую структуру
    if ':' not in token:
        return False
    
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    bot_id, bot_secret = parts
    
    # Проверяем ID бота (должен быть числом)
    if not bot_id.isdigit() or len(bot_id) < 8:
        return False
    
    # Проверяем секретную часть
    if len(bot_secret) < 20:
        return False
    
    # Проверяем что секрет содержит только допустимые символы
    if not re.match(r'^[A-Za-z0-9_-]+$', bot_secret):
        return False
    
    return True


def validate_admin_id(admin_id: Union[str, int]) -> bool:
    """
    Валидирует ID администратора.
    
    Args:
        admin_id: ID для проверки
        
    Returns:
        True если ID валидный, False иначе
    """
    if isinstance(admin_id, int):
        admin_id = str(admin_id)
    
    if not isinstance(admin_id, str):
        return False
    
    # Проверяем что это число
    if not admin_id.isdigit():
        return False
    
    # Проверяем длину
    if len(admin_id) < 8:
        return False
    
    return True


def validate_channel_username(username: str) -> bool:
    """
    Валидирует username канала.
    
    Args:
        username: Username для проверки
        
    Returns:
        True если username валидный, False иначе
    """
    if not isinstance(username, str):
        return False
    
    # Проверяем формат @username
    pattern = r'^@[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, username))


def validate_channel_link(link: str) -> bool:
    """
    Валидирует ссылку на канал.
    
    Args:
        link: Ссылка для проверки
        
    Returns:
        True если ссылка валидная, False иначе
    """
    if not isinstance(link, str):
        return False
    
    # Проверяем формат https://t.me/username
    pattern = r'^https://t\.me/[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, link))


def safe_format_message(message: str, **kwargs: Any) -> str:
    """
    Безопасное форматирование сообщения.
    
    Args:
        message: Шаблон сообщения
        **kwargs: Параметры для форматирования
        
    Returns:
        Отформатированное сообщение
    """
    try:
        # Санитизируем все параметры
        safe_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                safe_kwargs[key] = sanitize_user_input(value)
            else:
                safe_kwargs[key] = value
        
        return message.format(**safe_kwargs)
    except Exception as e:
        logger.error(f"Ошибка форматирования сообщения: {e}")
        return message


def is_safe_filename(filename: str) -> bool:
    """
    Проверяет безопасность имени файла.
    
    Args:
        filename: Имя файла для проверки
        
    Returns:
        True если имя файла безопасное, False иначе
    """
    if not isinstance(filename, str):
        return False
    
    # Запрещенные символы
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    for char in dangerous_chars:
        if char in filename:
            return False
    
    # Проверяем длину
    if len(filename) > 255:
        return False
    
    return True


def mask_sensitive_data(data: str, mask_char: str = '*') -> str:
    """
    Маскирует чувствительные данные.
    
    Args:
        data: Данные для маскировки
        mask_char: Символ для маскировки
        
    Returns:
        Замаскированные данные
    """
    if not isinstance(data, str) or len(data) < 4:
        return data
    
    # Показываем первые 2 и последние 2 символа
    if len(data) <= 6:
        return mask_char * len(data)
    
    return data[:2] + mask_char * (len(data) - 4) + data[-2:]


def check_rate_limit(user_id: int, action: str, limits: Dict[str, Any]) -> bool:
    """
    Проверяет rate limit для пользователя.
    
    Args:
        user_id: ID пользователя
        action: Действие
        limits: Словарь с лимитами
        
    Returns:
        True если лимит не превышен, False иначе
    """
    # Здесь должна быть логика проверки rate limit
    # Пока возвращаем True для совместимости
    return True


def log_security_event(event_type: str, user_id: Optional[int], details: Dict[str, Any]) -> None:
    """
    Логирует событие безопасности.
    
    Args:
        event_type: Тип события
        user_id: ID пользователя
        details: Детали события
    """
    # Санитизируем детали
    safe_details = {}
    for key, value in details.items():
        if isinstance(value, str):
            safe_details[key] = sanitize_for_logging(value)
        else:
            safe_details[key] = value
    
    logger.warning(
        f"Security event: {event_type}, "
        f"user_id: {user_id}, "
        f"details: {safe_details}"
    )


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Валидирует конфигурацию.
    
    Args:
        config: Конфигурация для проверки
        
    Returns:
        Список ошибок валидации
    """
    errors = []
    
    # Проверяем обязательные поля
    required_fields = ['bot_token', 'admin_ids', 'db_path']
    for field in required_fields:
        if field not in config or not config[field]:
            errors.append(f"Отсутствует обязательное поле: {field}")
    
    # Валидируем токен бота
    if 'bot_token' in config and not validate_bot_token(config['bot_token']):
        errors.append("Некорректный токен бота")
    
    # Валидируем ID администраторов
    if 'admin_ids' in config:
        admin_ids = config['admin_ids']
        if isinstance(admin_ids, str):
            admin_ids = [x.strip() for x in admin_ids.split(',')]
        
        for admin_id in admin_ids:
            if not validate_admin_id(admin_id):
                errors.append(f"Некорректный ID администратора: {admin_id}")
    
    return errors


def validate_user_id(user_id: Union[str, int]) -> bool:
    """
    Валидирует ID пользователя.
    
    Args:
        user_id: ID для проверки
        
    Returns:
        True если ID валидный, False иначе
    """
    if isinstance(user_id, int):
        user_id = str(user_id)
    
    if not isinstance(user_id, str):
        return False
    
    # Проверяем что это число
    if not user_id.isdigit():
        return False
    
    # Проверяем длину
    if len(user_id) < 8:
        return False
    
    return True


def validate_username(username: str) -> bool:
    """
    Валидирует username пользователя.
    
    Args:
        username: Username для проверки
        
    Returns:
        True если username валидный, False иначе
    """
    if not isinstance(username, str):
        return False
    
    # Проверяем длину
    if len(username) < 5 or len(username) > 32:
        return False
    
    # Проверяем что содержит только допустимые символы
    import re
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


def validate_chat_id(chat_id: Union[str, int]) -> bool:
    """
    Валидирует ID чата.
    
    Args:
        chat_id: ID чата для проверки
        
    Returns:
        True если ID чата валидный, False иначе
    """
    if isinstance(chat_id, int):
        chat_id = str(chat_id)
    
    if not isinstance(chat_id, str):
        return False
    
    # Проверяем что это число
    if not chat_id.isdigit():
        return False
    
    # Проверяем длину
    if len(chat_id) < 8:
        return False
    
    return True


def hash_user_id(user_id: Union[str, int]) -> str:
    """
    Хеширует ID пользователя для безопасного логирования.
    
    Args:
        user_id: ID пользователя для хеширования
        
    Returns:
        Хешированный ID пользователя
    """
    import hashlib
    
    if isinstance(user_id, int):
        user_id = str(user_id)
    
    if not isinstance(user_id, str):
        return "unknown"
    
    # Создаем хеш с солью для безопасности
    salt = "antispam_bot_salt_2024"
    hash_object = hashlib.sha256(f"{user_id}{salt}".encode())
    return hash_object.hexdigest()[:16]  # Возвращаем первые 16 символов