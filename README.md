# 🤖 Flame of Styx - AntiSpam Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.12.0-green.svg)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Quality](https://github.com/ncux-ad/Flame_Of_Styx_bot/actions/workflows/code-quality.yml/badge.svg)](https://github.com/ncux-ad/Flame_Of_Styx_bot/actions/workflows/code-quality.yml)

> **Мощный антиспам бот для Telegram с продвинутыми возможностями мониторинга и управления**

## 🚀 Быстрый старт

### 📋 Требования
- **Python 3.11+**
- **Redis** (для rate limiting)
- **SQLite** (встроенная БД)
- **Ubuntu 20.04+** (рекомендуется)

### ⚡ Установка за 5 минут

```bash
# 1. Клонировать репозиторий
git clone https://github.com/ncux-ad/Flame_Of_Styx_bot.git
cd Flame_Of_Styx_bot

# 2. Запустить умную установку
bash scripts/install-bot.sh

# 3. Настроить мониторинг (опционально)
bash scripts/install-monitoring.sh
```

## 🎯 Основные возможности

### 🛡️ Антиспам защита
- **Умная фильтрация** - ML-алгоритмы для детекции спама
- **Rate limiting** - защита от флуда
- **Подозрительные профили** - анализ пользователей
- **Автоматические баны** - настраиваемые правила

### 📊 Мониторинг и аналитика
- **Glances** - системный мониторинг в реальном времени
- **Healthcheck** - проверка состояния бота
- **Логирование** - детальные логи всех операций
- **Метрики** - статистика работы

### ⚙️ Управление
- **Админ панель** - полное управление через Telegram
- **Настройка лимитов** - гибкая конфигурация
- **Управление каналами** - добавление/удаление
- **Статистика** - подробная аналитика

## 🔧 Конфигурация

### 📝 Переменные окружения

Создайте файл `.env`:

```env
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Redis для rate limiting
REDIS_URL=redis://localhost:6379/0

# Настройки бота
ADMIN_IDS=123456789,987654321
DEBUG=false
LOG_LEVEL=INFO

# Мониторинг
ENABLE_MONITORING=true
GLANCES_WEB_PORT=61208
HEALTHCHECK_PORT=8081
```

### ⚙️ Лимиты и правила

Настройте `limits.json`:

```json
{
  "max_messages_per_minute": 10,
  "max_links_per_message": 3,
  "ban_duration_hours": 24,
  "suspicion_threshold": 0.55,
  "allow_photos_without_caption": true,
  "allow_videos_without_caption": true
}
```

## 📊 Мониторинг

### 🌐 Веб-интерфейс
- **Glances**: `http://your-server:61208`
- **Healthcheck**: `http://your-server:8081/healthcheck.php`
- **Аутентификация**: glances-admin / ваш-пароль

### 📱 Telegram команды
- `/status` - статус бота и статистика
- `/settings` - настройки антиспама
- `/suspicious` - подозрительные профили
- `/channels` - управление каналами
- `/setlimits` - настройка лимитов

## 🏗️ Архитектура

### 📁 Структура проекта
```
Flame_Of_Styx_bot/
├── app/                    # Основное приложение
│   ├── handlers/          # Обработчики команд
│   ├── middlewares/       # Middleware для валидации
│   ├── services/          # Бизнес-логика
│   ├── models/            # Модели данных
│   └── utils/             # Утилиты
├── scripts/               # Скрипты установки
├── docs/                  # Документация
├── tests/                 # Тесты
└── monitoring/            # Конфигурация мониторинга
```

### 🔄 Основные компоненты
- **Bot Core** - ядро бота на aiogram 3.12
- **AntiSpam Engine** - движок антиспама
- **Rate Limiter** - ограничение частоты запросов
- **Monitoring System** - система мониторинга
- **Admin Interface** - интерфейс управления

## 🚀 Развертывание

### 🐳 Docker (рекомендуется)
```bash
# Запуск в production
docker-compose -f docker-compose.prod.yml up -d

# Запуск с мониторингом
docker-compose -f docker-compose.monitoring.yml up -d
```

### ⚙️ Systemd (для VPS)
```bash
# Установка как сервис
sudo cp systemd/antispam-bot.service /etc/systemd/system/
sudo systemctl enable antispam-bot
sudo systemctl start antispam-bot
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Тесты с покрытием
pytest --cov=app

# Проверка безопасности
bandit -r app/
safety check
```

## 📚 Документация

- **[Руководство администратора](docs/ADMIN_GUIDE.md)**
- **[Руководство разработчика](docs/DEVELOPMENT.md)**
- **[API документация](docs/API.md)**
- **[Безопасность](docs/SECURITY.md)**
- **[Мониторинг](MONITORING_SETUP.md)**

## 🤝 Участие в разработке

1. **Fork** репозитория
2. Создайте **feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit** изменения: `git commit -m 'Add amazing feature'`
4. **Push** в branch: `git push origin feature/amazing-feature`
5. Откройте **Pull Request**

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- **Issues**: [GitHub Issues](https://github.com/ncux-ad/Flame_Of_Styx_bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ncux-ad/Flame_Of_Styx_bot/discussions)
- **Email**: [ncux-ad@github.com](mailto:ncux-ad@github.com)

## 🎉 Благодарности

- **aiogram** - отличная библиотека для Telegram Bot API
- **SQLAlchemy** - мощная ORM для работы с БД
- **Glances** - легкий системный мониторинг
- **Redis** - быстрый кэш и rate limiting

---

**Сделано с ❤️ для защиты Telegram сообществ от спама**