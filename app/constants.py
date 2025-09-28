"""
Константы для AntiSpam Bot
"""

import re

# =============================================================================
# ВРЕМЕННЫЕ КОНСТАНТЫ
# =============================================================================

# Таймауты (в секундах)
DEFAULT_TIMEOUT = 30
RATE_LIMIT_INTERVAL = 60
HEALTH_CHECK_TIMEOUT = 5
REQUEST_TIMEOUT = 10

# Интервалы повторов (в секундах)
RETRY_DELAY = 1
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

# =============================================================================
# ЛИМИТЫ И ОГРАНИЧЕНИЯ
# =============================================================================

# Rate limiting
DEFAULT_RATE_LIMIT = 5
MAX_MESSAGES_PER_MINUTE = 10
MAX_MESSAGES_PER_HOUR = 100

# Подозрительные профили
SUSPICION_THRESHOLD = 0.55
MAX_SUSPICION_SCORE = 1.0
MIN_SUSPICION_SCORE = 0.0

# Размеры файлов (в байтах)
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB

# =============================================================================
# СТРОКОВЫЕ КОНСТАНТЫ
# =============================================================================

# Сообщения об ошибках
ERROR_MESSAGES = {
    "UNAUTHORIZED": "❌ У вас нет прав для выполнения этой команды",
    "INVALID_INPUT": "❌ Некорректные входные данные",
    "RATE_LIMIT_EXCEEDED": "⏳ Слишком часто пишешь, притормози.",
    "BOT_ERROR": "❌ Произошла ошибка бота. Попробуйте позже.",
    "CHANNEL_NOT_FOUND": "❌ Канал не найден",
    "INVALID_CHANNEL": "❌ Некорректный канал",
}

# Сообщения об успехе
SUCCESS_MESSAGES = {
    "COMMAND_EXECUTED": "✅ Команда выполнена успешно",
    "CHANNEL_ADDED": "✅ Канал добавлен",
    "CHANNEL_REMOVED": "✅ Канал удален",
    "SETTINGS_UPDATED": "✅ Настройки обновлены",
}

# =============================================================================
# КОНФИГУРАЦИОННЫЕ КОНСТАНТЫ
# =============================================================================

# Telegram API
TELEGRAM_API_URL = "https://api.telegram.org/bot"
TELEGRAM_FILE_URL = "https://api.telegram.org/file/bot"

# База данных
DEFAULT_DB_PATH = "db.sqlite3"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"

# Логирование
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================================================
# РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ
# =============================================================================

# Паттерны для валидации
PATTERNS = {
    "BOT_TOKEN": re.compile(r"^\d+:[A-Za-z0-9_-]{35}$"),
    "ADMIN_ID": re.compile(r"^\d+$"),
    "CHANNEL_USERNAME": re.compile(r"^@[a-zA-Z0-9_]{5,32}$"),
    "CHANNEL_LINK": re.compile(r"^https://t\.me/[a-zA-Z0-9_]{5,32}$"),
    "EMAIL": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
}

# =============================================================================
# КОДЫ ОШИБОК
# =============================================================================


class ErrorCodes:
    """Коды ошибок для API"""

    # Общие ошибки
    SUCCESS = 0
    UNKNOWN_ERROR = 1
    INVALID_REQUEST = 2
    UNAUTHORIZED = 3
    FORBIDDEN = 4
    NOT_FOUND = 5

    # Ошибки валидации
    INVALID_TOKEN = 100
    INVALID_ADMIN_ID = 101
    INVALID_CHANNEL = 102
    INVALID_MESSAGE = 103

    # Ошибки rate limiting
    RATE_LIMIT_EXCEEDED = 200
    TOO_MANY_REQUESTS = 201

    # Ошибки базы данных
    DB_CONNECTION_ERROR = 300
    DB_QUERY_ERROR = 301
    DB_TRANSACTION_ERROR = 302


# =============================================================================
# НАСТРОЙКИ БЕЗОПАСНОСТИ
# =============================================================================

# Минимальные требования к безопасности
MIN_TOKEN_LENGTH = 20
MIN_ADMIN_ID_LENGTH = 8
MAX_LOG_MESSAGE_LENGTH = 1000

# Паттерны для фильтрации чувствительных данных
SENSITIVE_PATTERNS = [
    # Сначала более специфичные паттерны
    re.compile(r"password\s+is\s+[^\s]+", re.IGNORECASE),
    re.compile(r"secret\s+key[=:\s]+[^\s]+", re.IGNORECASE),
    # Затем общие паттерны
    re.compile(r"token[=:\s]+[a-zA-Z0-9_-]+", re.IGNORECASE),
    re.compile(r"password[=:\s]+[^\s]+", re.IGNORECASE),
    re.compile(r"secret[=:\s]+[^\s]+", re.IGNORECASE),
    re.compile(r"key[=:\s]+[a-zA-Z0-9_-]+", re.IGNORECASE),
    
    # Паттерны для персональных данных
    re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),  # Номера карт
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN (американский)
    re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),  # CPF (бразильский)
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
    re.compile(r"\b(?:\+?7|8)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}\b"),  # Телефоны (российские)
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),  # Телефоны (американские)
    
    # Паттерны для адресов и личной информации
    re.compile(r"\b(?:ул|улица|проспект|пр|переулок|пер|площадь|пл|бульвар|б-р)\s+[А-Яа-я\s\d]+", re.IGNORECASE),  # Адреса (русские)
    re.compile(r"\b(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln)\s+[A-Za-z\s\d]+", re.IGNORECASE),  # Адреса (английские)
    
    # Паттерны для имен и фамилий (базовые)
    re.compile(r"\b(?:имя|name|фамилия|surname|отчество|patronymic)\s*[=:]\s*[А-Яа-яA-Za-z\s]+", re.IGNORECASE),
    
    # Паттерны для ID документов
    re.compile(r"\b(?:паспорт|passport|id|идентификатор)\s*[=:]\s*[A-Za-z0-9\s\-]+", re.IGNORECASE),
]

# =============================================================================
# НАСТРОЙКИ ПРОИЗВОДИТЕЛЬНОСТИ
# =============================================================================

# Размеры буферов
DEFAULT_BUFFER_SIZE = 8192
MAX_CONCURRENT_REQUESTS = 10
MAX_CONCURRENT_DB_CONNECTIONS = 5

# Кэширование
CACHE_TTL = 300  # 5 минут
MAX_CACHE_SIZE = 1000
