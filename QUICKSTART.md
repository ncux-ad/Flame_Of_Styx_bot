# 🚀 Быстрый старт AntiSpam Bot

Это руководство поможет вам быстро запустить проект AntiSpam Bot.

## 📋 Предварительные требования

- **Python 3.11+**
- **Git**
- **Docker** (опционально, для локальной разработки)

## ⚡ Быстрый запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/antispam-bot.git
cd antispam-bot
```

### 2. Настройка окружения

#### Windows (PowerShell)
```powershell
# Запустите PowerShell от имени администратора
.\scripts\setup-dev.ps1
```

#### Linux/macOS
```bash
# Сделайте скрипт исполняемым
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

### 3. Настройка конфигурации

```bash
# Скопируйте пример конфигурации
cp env.example .env

# Отредактируйте .env файл
nano .env  # или notepad .env на Windows
```

**Обязательно настройте:**
- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMIN_IDS` - ID администраторов (через запятую)

### 4. Запуск

#### Через Docker (рекомендуется)
```bash
docker-compose up -d
```

#### Напрямую
```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/macOS
# или
.\venv\Scripts\Activate.ps1  # Windows

# Запустите бота
python bot.py
```

## 🔧 Разработка

### Установка зависимостей

```bash
pip install -e ".[dev]"
```

### Запуск тестов

```bash
pytest
```

### Линтеры

```bash
# Форматирование
black .

# Проверка стиля
ruff check .

# Проверка типов
mypy app/
```

### Pre-commit

```bash
pre-commit install
```

## 📚 Документация

- [Архитектура](docs/ARCHITECTURE.md)
- [DevOps](docs/DEVOPS.md)
- [Конфигурация](docs/CONFIG.md)
- [Roadmap](docs/ROADMAP.md)
- [TODO](docs/TODO.md)

## 🐛 Проблемы

Если у вас возникли проблемы:

1. Проверьте [Issues](https://github.com/your-username/antispam-bot/issues)
2. Создайте новый issue с подробным описанием
3. Проверьте логи: `docker-compose logs -f`

## 🤝 Вклад в проект

См. [CONTRIBUTING.md](CONTRIBUTING.md) для подробной информации.

## 📄 Лицензия

Проект использует MIT лицензию. См. [LICENSE](LICENSE).

---

**Готово!** 🎉 Ваш AntiSpam Bot готов к работе!
