# AntiSpam Bot

Антиспам-бот для Telegram-каналов с комментариями. Защищает от ботов, спама и GPT-ботов с каналами-приманками.

## 🎯 Основной функционал

- **Автобан ботов** (кроме whitelist)
- **Удаление ссылок** на `t.me/bot`
- **Управление каналами** (whitelist/blacklist для sender_chat)
- **Выявление GPT-ботов** с каналами-приманками
- **Админ-панель** с удобными инструментами

## 🏗️ Архитектура

- **Python 3.11+** + **aiogram 3.x**
- **SQLite** (MVP) / **PostgreSQL** (продакшн)
- **Redis** (rate limiting, кеширование)
- **SQLAlchemy async ORM**
- **Systemd** (продакшн) / **Docker** (разработка)

## 🚀 Быстрый старт

### Локальная разработка (Windows)

```bash
# Клонирование
git clone <repository-url>
cd antispam-bot

# Настройка окружения
cp env.example .env
# Отредактируйте .env файл

# Запуск через Docker
docker-compose up -d

# Просмотр логов
docker-compose logs -f antispam-bot
```

### Продакшен (Ubuntu 20.04)

```bash
# Автоматическое развертывание
sudo ./scripts/deploy.sh

# Настройка конфигурации
sudo nano /opt/antispam-bot/.env

# Перезапуск после настройки
sudo systemctl restart antispam-bot
```

## 📊 Управление

```bash
# Статус сервиса
sudo systemctl status antispam-bot

# Логи
sudo journalctl -u antispam-bot -f

# Перезапуск
sudo systemctl restart antispam-bot

# Обновление
sudo ./scripts/update.sh
```

## 📚 Документация

- [Архитектура](docs/ARCHITECTURE.md)
- [DevOps](docs/DEVOPS.md)
- [Конфигурация](docs/CONFIG.md)
- [Roadmap](docs/ROADMAP.md)
- [TODO](docs/TODO.md)

## 🛠️ Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Линтеры
black .
ruff check .
mypy app/

# Тесты
pytest -v
```

## 📈 Статус проекта

- ✅ **Базовая архитектура** - готова
- ✅ **DevOps инфраструктура** - готова
- ⏳ **Основной функционал** - в разработке
- ⏳ **Тесты и CI/CD** - планируется
