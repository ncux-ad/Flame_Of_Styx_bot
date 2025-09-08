# 🤖 AntiSpam Bot

Telegram-бот для защиты от спама, рекламы и подозрительных пользователей в группах и каналах.

## ✨ Возможности

- 🛡️ **Антиспам защита** - автоматическое обнаружение и блокировка спама
- 🔗 **Фильтрация ссылок** - проверка и блокировка подозрительных ссылок
- 👤 **Анализ профилей** - выявление подозрительных пользователей
- 📊 **Статистика** - детальная статистика по каналам и ботам
- ⚙️ **Гибкая настройка** - настройка правил и фильтров
- 🔐 **Админ-панель** - удобное управление через команды

## 🚀 Быстрый старт

### ⚡ Одна команда для установки
```bash
# Скачивание и установка
git clone https://github.com/your-repo/antispam-bot.git
cd antispam-bot
sudo bash install.sh
```

### 🐳 Docker установка
```bash
make install-docker
```

### ⚙️ systemd установка
```bash
make install-systemd
```

### 📖 Подробная документация
- [Быстрая установка](QUICK_INSTALL.md)
- [Полное руководство](docs/INSTALLATION.md)
- [Let's Encrypt SSL](docs/LETSENCRYPT.md)

### Требования

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Домен, указывающий на сервер
- Telegram Bot Token
- Минимум 512MB RAM

### Ручная установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd ad_anti_spam_bot_full
```

2. **Настройте переменные окружения:**
```bash
# Скопируйте пример конфигурации
cp env.example .env

# Отредактируйте .env файл
nano .env
```

3. **Запустите через Docker:**
```bash
docker-compose up -d
```

### Конфигурация

Создайте файл `.env` или настройте переменные в `docker-compose.yml`:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321
DB_PATH=db.sqlite3
```

## 📖 Документация

📚 **[Полный индекс документации](docs/INDEX.md)**
🔗 **[Быстрые ссылки на ресурсы](QUICK_LINKS.md)**

### Основные руководства:
- [Руководство по развертыванию](docs/DEPLOYMENT.md)
- [Руководство для разработчиков](docs/DEVELOPMENT.md)
- [Конфигурация](docs/CONFIGURATION.md)
- [API документация](docs/API.md)
- [Лучшие практики DI](DI_BEST_PRACTICES.md)
- [Официальная документация библиотек](docs/OFFICIAL_DOCUMENTATION.md)
- [Практические примеры кода](docs/CODE_EXAMPLES.md)
- [Настройка PowerShell 7](docs/POWERSHELL_SETUP.md)
- [Кибербезопасность](docs/SECURITY.md)
- [Руководство по безопасности](docs/SECURITY_GUIDELINES.md)
- [Let's Encrypt SSL сертификаты](docs/LETSENCRYPT.md)

## 🎯 Команды бота

### Админские команды

- `/start` - Главное меню
- `/status` - Статистика бота
- `/channels` - Управление каналами
- `/bots` - Управление ботами
- `/suspicious` - Подозрительные профили
- `/help` - Справка
- `/logs` - Просмотр логов

## 🏗️ Архитектура

```
app/
├── handlers/          # Обработчики команд и сообщений
├── middlewares/       # Middleware для DI и логирования
├── services/          # Бизнес-логика и сервисы
├── models/           # Модели базы данных
├── filters/          # Фильтры для обработчиков
├── keyboards/        # Клавиатуры для интерфейса
└── config.py         # Конфигурация приложения
```

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

Логи сохраняются в директории `logs/` и доступны через команду `/logs`.

### База данных

Используется SQLite база данных, файл сохраняется в `data/db.sqlite3`.

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
2. Создайте [Issue](../../issues)
3. Обратитесь к [руководству по DI](DI_BEST_PRACTICES.md)

## 🔄 Обновления

### v1.0.0
- ✅ Базовая функциональность антиспам-бота
- ✅ Система внедрения зависимостей
- ✅ Админ-панель
- ✅ Docker поддержка
- ✅ Полная документация

---

**Создано с ❤️ для защиты Telegram сообществ**
