# Архитектура AntiSpam Bot

## 🏗️ Общая схема

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram API  │◄──►│   AntiSpam Bot  │◄──►│   SQLite/Postgres│
│                 │    │   (aiogram 3.x) │    │   (SQLAlchemy)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   (Rate Limit)  │
                       └─────────────────┘
```

## 📁 Структура модулей

### `app/handlers/` - Обработчики событий
- **`user.py`** - новые участники, сообщения пользователей
- **`channels.py`** - сообщения от каналов (sender_chat)
- **`admin.py`** - админские команды

### `app/services/` - Бизнес-логика
- **`moderation.py`** - бан/мут/разбан пользователей
- **`links.py`** - проверка ссылок на ботов
- **`channels.py`** - управление whitelist/blacklist каналов
- **`bots.py`** - управление whitelist ботов
- **`profiles.py`** - анализ профилей GPT-ботов

### `app/middlewares/` - Промежуточное ПО
- **`logging.py`** - логирование всех событий
- **`ratelimit.py`** - ограничение частоты запросов

### `app/filters/` - Фильтры
- **`is_admin.py`** - проверка прав администратора

### `app/keyboards/` - Клавиатуры
- **`inline.py`** - inline-кнопки для админов
- **`reply.py`** - обычные клавиатуры

## 🔄 Поток обработки

1. **Новый участник** → `handlers/user.py` → `services/moderation.py`
2. **Сообщение с ссылкой** → `handlers/user.py` → `services/links.py`
3. **Сообщение от канала** → `handlers/channels.py` → `services/channels.py`
4. **Админская команда** → `handlers/admin.py` → соответствующий сервис

## 🗄️ База данных

### Таблицы
- **`users`** - информация о пользователях
- **`channels`** - whitelist/blacklist каналов
- **`bots`** - whitelist ботов
- **`moderation_log`** - логи модерации
- **`suspicious_profiles`** - подозрительные профили

## 🔧 Конфигурация

- **`.env`** - переменные окружения
- **`app/config.py`** - настройки через Pydantic
- **`app/database.py`** - подключение к БД

## 🚀 Развертывание

- **Разработка**: Docker Compose
- **Продакшен**: Systemd сервис на Ubuntu 20.04
