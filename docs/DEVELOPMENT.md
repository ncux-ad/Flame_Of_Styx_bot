# 👨‍💻 Руководство для разработчиков

## 🏗️ Архитектура проекта

```
ad_anti_spam_bot_full/
├── app/                    # Основной код приложения
│   ├── handlers/          # Обработчики команд и сообщений
│   │   ├── admin.py       # Админские команды
│   │   ├── user.py        # Пользовательские сообщения
│   │   └── channels.py    # Обработка каналов
│   ├── middlewares/       # Middleware
│   │   ├── dependency_injection.py  # DI middleware
│   │   ├── logging.py     # Логирование
│   │   └── ratelimit.py   # Ограничение частоты
│   ├── services/          # Бизнес-логика
│   │   ├── bots.py        # Управление ботами
│   │   ├── channels.py    # Управление каналами
│   │   ├── links.py       # Анализ ссылок
│   │   ├── profiles.py    # Анализ профилей
│   │   └── moderation.py  # Модерация
│   ├── models/            # Модели базы данных
│   │   ├── bot.py         # Модель бота
│   │   ├── channel.py     # Модель канала
│   │   ├── profile.py     # Модель профиля
│   │   └── link.py        # Модель ссылки
│   ├── filters/           # Фильтры
│   │   ├── is_admin.py    # Проверка админа
│   │   └── is_admin_or_silent.py  # Тихая проверка
│   ├── keyboards/         # Клавиатуры
│   │   ├── inline.py      # Inline клавиатуры
│   │   └── reply.py       # Reply клавиатуры
│   ├── database.py        # Настройка БД
│   └── config.py          # Конфигурация
├── tests/                 # Тесты
├── docs/                  # Документация
├── data/                  # Данные (БД, файлы)
├── logs/                  # Логи
├── bot.py                 # Точка входа
├── requirements.txt       # Зависимости Python
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose
└── README.md             # Основная документация
```

## 🛠️ Настройка среды разработки

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Linux/macOS)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# Создание .env файла
cp env.example .env

# Редактирование конфигурации
nano .env
```

### 3. Настройка IDE

#### VS Code

Создайте `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "terminal.integrated.defaultProfile.windows": "PowerShell"
}
```

#### PyCharm

1. Откройте проект в PyCharm
2. Настройте интерпретатор Python на виртуальное окружение
3. Настройте переменные окружения в Run Configuration

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
python -m pytest

# С покрытием
python -m pytest --cov=app

# Конкретный тест
python -m pytest tests/test_handlers.py::test_start_command

# С подробным выводом
python -m pytest -v
```

### Создание тестов

```python
# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.handlers.admin import handle_start_command

@pytest.mark.asyncio
async def test_start_command():
    """Test /start command handler."""
    # Создание мока сообщения
    message = MagicMock()
    message.answer = AsyncMock()

    # Вызов обработчика
    await handle_start_command(message, data={})

    # Проверка вызова
    message.answer.assert_called_once()
```

## 🔧 Разработка

### 1. Создание нового сервиса

```python
# app/services/new_service.py
from typing import Optional
from app.database import get_db
from app.models.new_model import NewModel

class NewService:
    """New service for handling specific functionality."""

    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_session = db_session

    async def create_item(self, data: dict) -> Optional[NewModel]:
        """Create new item."""
        # Implementation here
        pass

    async def get_item(self, item_id: int) -> Optional[NewModel]:
        """Get item by ID."""
        # Implementation here
        pass
```

### 2. Создание нового обработчика

```python
# app/handlers/new_handler.py
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("newcommand"))
async def handle_new_command(message: Message, data: dict = None) -> None:
    """Handle new command."""
    try:
        # Get service from data
        service = data.get('new_service') if data else None

        if not service:
            logger.error("Service not injected properly")
            return

        # Handle command logic
        await message.answer("New command executed!")

    except Exception as e:
        logger.error(f"Error handling new command: {e}")
```

### 3. Регистрация в DI middleware

```python
# app/middlewares/dependency_injection.py
from app.services.new_service import NewService

# В методе __call__ добавить:
services = {
    'link_service': LinkService(bot, db_session),
    'profile_service': ProfileService(bot, db_session),
    'channel_service': ChannelService(bot, db_session),
    'bot_service': BotService(bot, db_session),
    'moderation_service': ModerationService(bot, db_session),
    'new_service': NewService(bot, db_session),  # Новый сервис
    'db_session': db_session
}
```

### 4. Регистрация роутера

```python
# bot.py
from app.handlers import new_handler

# В функции main():
dp.include_router(new_handler.router)
```

## 📊 База данных

### 1. Создание новой модели

```python
# app/models/new_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class NewModel(Base):
    """New model for database."""

    __tablename__ = 'new_models'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NewModel(id={self.id}, name='{self.name}')>"
```

### 2. Миграции

```python
# app/database.py
from app.models.new_model import NewModel

# В функции create_tables():
Base.metadata.create_all(bind=engine)
```

## 🔍 Отладка

### 1. Логирование

```python
import logging

logger = logging.getLogger(__name__)

# Различные уровни логирования
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### 2. Отладка в VS Code

Создайте `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Bot",
            "type": "python",
            "request": "launch",
            "program": "bot.py",
            "console": "integratedTerminal",
            "env": {
                "BOT_TOKEN": "your_token_here",
                "ADMIN_IDS": "123456789,987654321",
                "DB_PATH": "db.sqlite3"
            }
        }
    ]
}
```

### 3. Отладка Docker

```bash
# Запуск с отладкой
docker-compose -f docker-compose.debug.yml up

# Подключение к контейнеру
docker exec -it antispam-bot bash

# Просмотр логов
docker logs antispam-bot -f
```

## 🚀 Развертывание

### 1. Локальное тестирование

```bash
# Запуск без Docker
python bot.py

# Запуск с Docker
docker-compose up --build
```

### 2. Тестирование в продакшене

```bash
# Создание тестового окружения
docker-compose -f docker-compose.test.yml up

# Запуск тестов
docker-compose exec antispam-bot python -m pytest
```

## 📝 Стиль кода

### 1. Форматирование

```bash
# Установка black
pip install black

# Форматирование кода
black app/

# Проверка стиля
black --check app/
```

### 2. Линтинг

```bash
# Установка pylint
pip install pylint

# Проверка кода
pylint app/

# Конфигурация pylint
pylint --rcfile=.pylintrc app/
```

### 3. Типизация

```python
from typing import Optional, List, Dict, Any
from aiogram.types import Message, CallbackQuery

async def handler(
    message: Message,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Handler with proper type hints."""
    pass
```

## 🔄 CI/CD

### GitHub Actions

Создайте `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        python -m pytest --cov=app tests/

    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## 📚 Полезные ресурсы

- [aiogram 3 документация](https://docs.aiogram.dev/)
- [SQLAlchemy документация](https://docs.sqlalchemy.org/)
- [Pytest документация](https://docs.pytest.org/)
- [Docker документация](https://docs.docker.com/)
- [Руководство по DI](DI_BEST_PRACTICES.md)

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/new-feature`
3. Внесите изменения и добавьте тесты
4. Зафиксируйте изменения: `git commit -m "Add new feature"`
5. Отправьте в ветку: `git push origin feature/new-feature`
6. Создайте Pull Request

## 📞 Поддержка

Если у вас возникли вопросы:

1. Изучите [документацию по DI](DI_BEST_PRACTICES.md)
2. Проверьте [руководство по развертыванию](DEPLOYMENT.md)
3. Создайте Issue в репозитории
4. Обратитесь к логам для диагностики
