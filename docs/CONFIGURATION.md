# ⚙️ Конфигурация

## 📋 Переменные окружения

### Обязательные параметры

| Переменная | Описание | Пример | Обязательно |
|------------|----------|--------|-------------|
| `BOT_TOKEN` | Токен Telegram бота | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` | ✅ |
| `ADMIN_IDS` | ID администраторов (через запятую) | `123456789,987654321` | ✅ |
| `DB_PATH` | Путь к файлу базы данных | `db.sqlite3` | ✅ |

### Дополнительные параметры

| Переменная | Описание | По умолчанию | Обязательно |
|------------|----------|--------------|-------------|
| `LOG_LEVEL` | Уровень логирования | `INFO` | ❌ |
| `RATE_LIMIT` | Лимит запросов в минуту | `5` | ❌ |
| `RATE_INTERVAL` | Интервал для лимита (секунды) | `60` | ❌ |

## 🔧 Способы конфигурации

### 1. Через .env файл

Создайте файл `.env` в корне проекта:

```env
# Основные настройки
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321
DB_PATH=db.sqlite3

# Дополнительные настройки
LOG_LEVEL=INFO
RATE_LIMIT=5
RATE_INTERVAL=60
```

### 2. Через docker-compose.yml

```yaml
version: '3.8'
services:
  antispam-bot:
    build: .
    container_name: antispam-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
      - ADMIN_IDS=123456789,987654321
      - DB_PATH=db.sqlite3
      - LOG_LEVEL=INFO
      - RATE_LIMIT=5
      - RATE_INTERVAL=60
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - antispam-network
```

### 3. Через переменные окружения системы

```bash
# Linux/macOS
export BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export ADMIN_IDS="123456789,987654321"
export DB_PATH="db.sqlite3"

# Windows
set BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
set ADMIN_IDS=123456789,987654321
set DB_PATH=db.sqlite3
```

## 🤖 Получение BOT_TOKEN

### 1. Создание бота через @BotFather

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "My AntiSpam Bot")
4. Введите username бота (например: "my_antispam_bot")
5. Скопируйте полученный токен

### 2. Получение дополнительных настроек

```bash
# Установка команд бота
/setcommands

# Установка описания
/setdescription

# Установка краткого описания
/setabouttext

# Установка аватара
/setuserpic
```

## 👥 Получение ADMIN_IDS

### 1. Через @userinfobot

1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Отправьте любое сообщение
3. Скопируйте ваш ID

### 2. Через @getidsbot

1. Откройте [@getidsbot](https://t.me/getidsbot)
2. Отправьте любое сообщение
3. Скопируйте ваш ID

### 3. Через код

```python
# Временный код для получения ID
import asyncio
from aiogram import Bot

async def get_user_id():
    bot = Bot(token="YOUR_BOT_TOKEN")
    updates = await bot.get_updates()
    for update in updates:
        if update.message:
            print(f"User ID: {update.message.from_user.id}")
            print(f"Username: @{update.message.from_user.username}")
    await bot.session.close()

asyncio.run(get_user_id())
```

## 🗄️ Настройка базы данных

### SQLite (по умолчанию)

```env
DB_PATH=db.sqlite3
```

### PostgreSQL

```env
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=antispam_bot
DB_USER=postgres
DB_PASSWORD=password
```

### MySQL

```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=antispam_bot
DB_USER=mysql
DB_PASSWORD=password
```

## 📊 Настройка логирования

### Уровни логирования

| Уровень | Описание | Использование |
|---------|----------|---------------|
| `DEBUG` | Подробная отладочная информация | Разработка |
| `INFO` | Общая информация о работе | Продакшен |
| `WARNING` | Предупреждения | Продакшен |
| `ERROR` | Ошибки | Продакшен |
| `CRITICAL` | Критические ошибки | Продакшен |

### Конфигурация логов

```python
# app/config.py
import logging

class Settings(BaseSettings):
    log_level: str = "INFO"

    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/bot.log'),
                logging.StreamHandler()
            ]
        )
```

## 🚦 Настройка Rate Limiting

### Параметры

```env
# Количество запросов
RATE_LIMIT=5

# Интервал в секундах
RATE_INTERVAL=60

# Сообщение при превышении лимита
RATE_LIMIT_MESSAGE="⏳ Слишком часто пишешь, притормози."
```

### Кастомизация

```python
# app/middlewares/ratelimit.py
class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 5, interval: int = 60, message: str = None):
        self.limit = limit
        self.interval = interval
        self.message = message or "⏳ Слишком часто пишешь, притормози."
```

## 🔐 Безопасность

### 1. Защита токена

```bash
# Установка правильных прав доступа
chmod 600 .env

# Исключение из Git
echo ".env" >> .gitignore
```

### 2. Ограничение доступа

```python
# app/filters/is_admin.py
class IsAdminFilter(BaseFilter):
    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        config = load_config()
        user_id = obj.from_user.id if obj.from_user else None
        return user_id in config.admin_ids_list
```

### 3. Валидация конфигурации

```python
# app/config.py
@validator("bot_token")
def validate_token(cls, v):
    if not v or len(v) < 20:
        raise ValueError("BOT_TOKEN некорректный или отсутствует")
    if ':' not in v or len(v.split(':')[0]) < 8:
        raise ValueError("BOT_TOKEN должен быть в формате 'bot_id:token'")
    return v

@validator("admin_ids")
def validate_admin_ids(cls, v):
    if not v:
        raise ValueError("ADMIN_IDS не может быть пустым")
    # Дополнительная валидация...
    return v
```

## 🌍 Настройка для разных окружений

### Development

```env
# .env.development
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789
DB_PATH=dev_db.sqlite3
LOG_LEVEL=DEBUG
RATE_LIMIT=100
```

### Staging

```env
# .env.staging
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321
DB_PATH=staging_db.sqlite3
LOG_LEVEL=INFO
RATE_LIMIT=10
```

### Production

```env
# .env.production
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321,555666777
DB_PATH=prod_db.sqlite3
LOG_LEVEL=WARNING
RATE_LIMIT=5
```

## 🔄 Обновление конфигурации

### Без перезапуска

```python
# app/config.py
class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def reload(self):
        """Reload configuration from environment."""
        return Settings()
```

### С перезапуском

```bash
# Docker
docker-compose restart

# Systemd
sudo systemctl restart antispam-bot
```

## 🧪 Тестирование конфигурации

### Проверка валидности

```python
# test_config.py
import pytest
from app.config import load_config

def test_config_validation():
    """Test configuration validation."""
    try:
        config = load_config()
        assert config.bot_token
        assert config.admin_ids_list
        assert config.db_path
    except Exception as e:
        pytest.fail(f"Configuration validation failed: {e}")
```

### Проверка подключения

```python
# test_connection.py
import asyncio
from app.config import load_config
from aiogram import Bot

async def test_bot_connection():
    """Test bot connection."""
    config = load_config()
    bot = Bot(token=config.bot_token)

    try:
        me = await bot.get_me()
        print(f"Bot connected: @{me.username}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await bot.session.close()

asyncio.run(test_bot_connection())
```

## 📞 Поддержка

Если у вас возникли проблемы с конфигурацией:

1. Проверьте [руководство по развертыванию](DEPLOYMENT.md)
2. Изучите [руководство для разработчиков](DEVELOPMENT.md)
3. Проверьте логи: `docker logs antispam-bot`
4. Создайте Issue в репозитории
