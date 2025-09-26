# 🤖 Flame of Styx - AntiSpam Bot

Telegram-бот для защиты от спама в каналах с **умной системой модерации** и **автоматическим обнаружением подозрительных профилей**.

## ✨ Возможности

- 🛡️ **Антиспам защита** - автоматическое обнаружение и блокировка спама
- 🔗 **Фильтрация бот-ссылок** - проверка `t.me/username` и `@username`
- 📱 **Медиа-антиспам** - обнаружение QR-кодов и подозрительных медиа
- 👤 **Система подозрительных профилей** - автоматическое обнаружение ботов и спам-аккаунтов
- 🔄 **Hot-reload настроек** - автоматическое обновление лимитов без перезапуска
- 📊 **Статистика и мониторинг** - детальная статистика по каналам и ботам
- 🔐 **Админ-панель** - удобное управление через команды
- 🐳 **Docker поддержка** - легкий деплой в контейнерах
- 🏗️ **Упрощенная архитектура** - только 2 слоя: Anti-spam + Admin

## 🚀 Быстрый старт

### ⚡ Автоматическая установка
```bash
# Скачивание и установка
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot
sudo bash install.sh
```

### 🐳 Docker установка (рекомендуется)
```bash
# Клонирование репозитория
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot

# Настройка переменных окружения
cp env.template .env
# Отредактируйте .env с вашими данными

# Запуск в Docker
docker-compose up -d --build
```

## 🎯 Команды бота

### 👑 Админские команды (в личке с ботом)

#### 📊 Статистика и мониторинг
- `/status` - Подробная статистика работы бота
- `/settings` - Настройки бота и конфигурация
- `/logs [уровень]` - Просмотр логов системы (`/logs error`, `/logs warning`)

#### 📺 Управление каналами
- `/channels` - Управление каналами с разделением на нативные и иностранные
- `/instructions` - Инструкция по настройке бота для админов каналов

#### 🤖 Управление ботами
- `/bots` - Управление ботами и whitelist

#### 🔍 Подозрительные профили
- `/suspicious` - Просмотр подозрительных профилей
- `/reset_suspicious` - Сброс статусов для тестирования
- `/recalculate_suspicious` - Пересчет с новыми весами
- `/cleanup_duplicates` - Очистка дублирующих профилей

#### 🚫 Модерация и баны
- `/unban [номер]` - Разблокировать пользователя по номеру
- `/unban <user_id> [chat_id]` - Разблокировать по ID
- `/banned` - Список заблокированных пользователей
- `/ban_history` - История банов с ID чатов
- `/sync_bans` - Синхронизация банов с Telegram API

#### ⚙️ Лимиты и настройки
- `/setlimits` - Просмотр текущих лимитов
- `/setlimit <тип> <значение>` - Изменение конкретного лимита
- `/reload_limits` - Перезагрузка лимитов из файла

#### 📖 Справка
- `/help` - Общая справка по командам
- `/help [категория]` - Справка по категории (`admin`, `channels`, `bots`, `moderation`, `suspicious`, `bans`, `limits`, `logs`)

### 🛡️ Антиспам (автоматически в каналах)
- **Обнаружение ссылок:** `t.me/username`
- **Обнаружение упоминаний:** `@username`
- **Медиа-контент:** QR-коды, подозрительные подписи
- **Действия:** удаление сообщения + бан пользователя

## 🏗️ Архитектура

```
app/
├── handlers/          # Обработчики команд и сообщений
│   ├── antispam.py   # Основной антиспам фильтр
│   ├── admin.py      # Админские команды
│   └── channels.py   # Обработка каналов
├── middlewares/       # Middleware для DI и логирования
│   ├── dependency_injection.py  # Упрощенный DI
│   ├── logging.py     # Логирование
│   ├── ratelimit.py   # Ограничение частоты
│   └── suspicious_profile.py  # Анализ профилей
├── services/          # Бизнес-логика и сервисы
│   ├── links.py       # Проверка ссылок
│   ├── profiles.py    # Анализ профилей
│   ├── moderation.py  # Модерация
│   ├── channels.py    # Управление каналами
│   ├── bots.py        # Управление ботами
│   ├── help.py        # Справка
│   └── limits.py      # Управление лимитами
├── models/           # Модели базы данных
├── filters/          # Фильтры для обработчиков
├── keyboards/        # Клавиатуры для интерфейса
└── config.py         # Конфигурация приложения
```

## 🔧 Конфигурация

### Переменные окружения

```env
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321

# Native Channels (каналы, где бот является администратором)
NATIVE_CHANNEL_IDS=-10000000000

# Database Configuration
DB_PATH=db.sqlite3

# Logging Configuration
LOG_LEVEL=INFO

# Rate Limiting Configuration
RATE_LIMIT=5
RATE_INTERVAL=60

# Additional Configuration
DOMAIN=your-domain.com
EMAIL=your-email@example.com
REDIS_PASSWORD=your_redis_password
NOTIFICATION_WEBHOOK=https://api.telegram.org/bot<token>/sendMessage?chat_id=<admin_id>&text=
```

### Настройка лимитов

Создайте файл `limits.json` для настройки антиспам параметров:

```json
{
  "max_messages_per_minute": 10,
  "max_links_per_message": 3,
  "ban_duration_hours": 24,
  "suspicion_threshold": 0.4,
  "check_media_without_caption": true,
  "allow_videos_without_caption": true,
  "allow_photos_without_caption": true,
  "max_document_size_suspicious": 50000
}
```

## 🐳 Docker

### Сборка образа
```bash
docker build -t antispam-bot .
```

### Запуск контейнера
```bash
docker-compose up -d
```

### Просмотр логов
```bash
docker logs antispam-bot -f
```

## 📊 Мониторинг

### Логи
Логи сохраняются в systemd journal и доступны через команду `/logs`.

### База данных
Используется SQLite база данных, файл сохраняется в `data/db.sqlite3`.

## 🔧 Разработка

### Локальная разработка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте переменные окружения:**
```bash
export BOT_TOKEN="your_token"
export ADMIN_IDS="123456789,987654321"
export DB_PATH="db.sqlite3"
```

3. **Запустите бота:**
```bash
python bot.py
```

### Тестирование
```bash
# Запуск тестов
python -m pytest tests/

# Запуск с покрытием
python -m pytest --cov=app tests/
```

## 📚 Документация

### 🔥 Основные функции
- [Система подозрительных профилей](docs/SUSPICIOUS_PROFILES.md) - автоматическое обнаружение ботов
- [Hot-reload настроек](docs/HOT_RELOAD.md) - обновление конфигурации без перезапуска
- [Архитектура системы](docs/ARCHITECTURE.md) - подробное описание архитектуры

### 📖 Руководства
- [Руководство администратора](docs/ADMIN_GUIDE.md) - полное руководство для админов
- [Руководство по развертыванию](docs/DEPLOYMENT.md) - установка и настройка
- [Конфигурация](docs/CONFIGURATION.md) - настройка параметров
- [API документация](docs/API.md) - описание API
- [Устранение неполадок](docs/TROUBLESHOOTING.md) - решение проблем

### 🔒 Безопасность
- [Руководство по безопасности](docs/SECURITY_GUIDELINES.md)
- [Исправления безопасности](docs/SECURITY_FIXES.md)

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [документацию](docs/)
2. Создайте [Issue](../../issues) (следуйте [правилам оформления](CONTRIBUTING.md))
3. Обратитесь к [руководству по устранению неполадок](docs/TROUBLESHOOTING.md)
4. Свяжитесь с разработчиком: [@ncux-ad](https://github.com/ncux-ad)

## 🔄 Обновления

### v2.0.0 (Текущая версия)
- ✅ Умная система подозрительных профилей
- ✅ Разделение каналов на нативные и иностранные
- ✅ Команда `/logs` для просмотра логов
- ✅ Улучшенная система уведомлений
- ✅ Hot-reload настроек
- ✅ Полная документация

### v1.0.0
- ✅ Базовая функциональность антиспам-бота
- ✅ Система внедрения зависимостей
- ✅ Админ-панель
- ✅ Docker поддержка

---

**Создано с ❤️ для защиты Telegram сообществ**