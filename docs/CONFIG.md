# Конфигурация AntiSpam Bot

## Переменные окружения (.env)

### Основные настройки
```bash
# Токен бота (обязательно)
BOT_TOKEN=your_bot_token_here

# ID администраторов через запятую (обязательно)
ADMIN_IDS=123456789,987654321

# Путь к базе данных (опционально, по умолчанию: data/bot.db)
DB_PATH=data/bot.db
```

### Настройки базы данных
```bash
# Для продакшена с PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/antispam_bot

# Для Redis (опционально)
REDIS_URL=redis://localhost:6379/0
```

### Настройки логирования
```bash
# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Формат логов (text, json)
LOG_FORMAT=text
```

### Настройки rate limiting
```bash
# Включить rate limiting (true/false)
RATE_LIMIT_ENABLED=true

# Количество запросов в минуту
RATE_LIMIT_REQUESTS=5

# Окно времени в секундах
RATE_LIMIT_WINDOW=60
```

## Пример полного .env файла

```bash
# Основные настройки
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321
DB_PATH=data/bot.db

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=text

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=60

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0
```

## Валидация конфигурации

Конфигурация автоматически валидируется при запуске бота:

- ✅ **BOT_TOKEN** - проверка формата токена
- ✅ **ADMIN_IDS** - парсинг и валидация ID
- ✅ **DB_PATH** - проверка доступности директории
- ✅ **LOG_LEVEL** - проверка допустимых значений

## Безопасность

- 🔒 **Никогда не коммитьте .env файл** в Git
- 🔒 **Используйте сильные токены** для продакшена
- 🔒 **Ограничьте права доступа** к .env файлу (600)
- 🔒 **Регулярно обновляйте** токены и пароли
