# 💻 Примеры кода

## 🤖 Aiogram 3.x Примеры

### Базовый бот с DI

```python
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

# Создание бота
bot = Bot(token="YOUR_TOKEN")
dp = Dispatcher()

# Простой обработчик
@dp.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer("Привет! Я бот с DI!")

# Запуск
if __name__ == "__main__":
    dp.run_polling(bot)
```

### Middleware с внедрением зависимостей

```python
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Any, Callable, Dict

class DependencyInjectionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Создание сервисов
        services = {
            'my_service': MyService(),
            'db_session': get_db_session()
        }

        # Добавление в контекст
        data.update(services)

        # Вызов обработчика
        return await handler(event, data)

# Регистрация middleware
dp.message.middleware(DependencyInjectionMiddleware())
```

### Обработчик с сервисами

```python
from aiogram.types import Message

@dp.message(Command("data"))
async def data_handler(message: Message, data: dict = None) -> None:
    # Получение сервиса из DI
    my_service = data.get('my_service') if data else None

    if not my_service:
        await message.answer("❌ Сервис недоступен")
        return

    # Использование сервиса
    result = await my_service.get_data()
    await message.answer(f"Данные: {result}")
```

## 🗄️ SQLAlchemy Примеры

### Базовая модель

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
```

### Создание сессии

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Создание движка
engine = create_engine("sqlite:///bot.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Использование сессии
async def get_user(user_id: int):
    async with SessionLocal() as session:
        return session.query(User).filter(User.id == user_id).first()
```

### Асинхронная работа с БД

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Асинхронный движок
async_engine = create_async_engine("sqlite+aiosqlite:///bot.db")
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_user_async(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

## ⚙️ Pydantic Примеры

### Базовая модель настроек

```python
from pydantic import BaseSettings, validator
from typing import List

class Settings(BaseSettings):
    bot_token: str
    admin_ids: str = "123456789,987654321"
    db_path: str = "bot.db"

    @validator("bot_token")
    def validate_token(cls, v):
        if not v or len(v) < 20:
            raise ValueError("BOT_TOKEN некорректный")
        return v

    @property
    def admin_ids_list(self) -> List[int]:
        return [int(x.strip()) for x in self.admin_ids.split(",")]

    class Config:
        env_file = ".env"

# Использование
settings = Settings()
print(f"Admin IDs: {settings.admin_ids_list}")
```

### Валидация данных

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: Optional[int] = Field(None, ge=0, le=120)

    @validator('username')
    def username_must_be_valid(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "age": 25
            }
        }

# Использование
try:
    user_data = UserCreate(
        username="john_doe",
        email="john@example.com",
        age=25
    )
    print(f"Valid user: {user_data}")
except ValueError as e:
    print(f"Validation error: {e}")
```

## 🧪 Тестирование Примеры

### Базовый тест

```python
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
    assert "AntiSpam Bot" in message.answer.call_args[0][0]
```

### Тест с сервисами

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.handlers.admin import handle_status_command

@pytest.mark.asyncio
async def test_status_command_with_services():
    """Test /status command with services."""
    # Создание моков
    message = MagicMock()
    message.answer = AsyncMock()

    mock_service = MagicMock()
    mock_service.get_stats = AsyncMock(return_value={"users": 100, "messages": 1000})

    data = {"stats_service": mock_service}

    # Вызов обработчика
    await handle_status_command(message, data=data)

    # Проверки
    message.answer.assert_called_once()
    mock_service.get_stats.assert_called_once()
```

### Тест базы данных

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.database import Base

@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_create_user(db_session):
    """Test user creation."""
    user = User(username="test_user", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "test_user"
```

## 🐳 Docker Примеры

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директорий
RUN mkdir -p data logs

# Запуск приложения
CMD ["python", "bot.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  antispam-bot:
    build: .
    container_name: antispam-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - DB_PATH=${DB_PATH}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

## 🔍 Качество кода Примеры

### Black форматирование

```python
# До форматирования
def long_function_name(parameter_one,parameter_two,parameter_three,parameter_four,parameter_five):
    return parameter_one+parameter_two+parameter_three+parameter_four+parameter_five

# После форматирования Black
def long_function_name(
    parameter_one,
    parameter_two,
    parameter_three,
    parameter_four,
    parameter_five,
):
    return (
        parameter_one
        + parameter_two
        + parameter_three
        + parameter_four
        + parameter_five
    )
```

### isort сортировка импортов

```python
# До сортировки
import os
from aiogram import Bot
import logging
from typing import List
from app.services import UserService

# После сортировки isort
import logging
import os
from typing import List

from aiogram import Bot

from app.services import UserService
```

### MyPy типизация

```python
from typing import Optional, List, Dict, Any
from aiogram.types import Message, CallbackQuery

async def process_message(
    message: Message,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Process message with type hints."""
    if not data:
        return

    service: Optional[UserService] = data.get('user_service')
    if not service:
        return

    result: List[Dict[str, Any]] = await service.get_user_data()
    await message.answer(f"Data: {result}")
```

## 🔄 CI/CD Примеры

### GitHub Actions

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint with pylint
      run: pylint app/

    - name: Format check with black
      run: black --check app/

    - name: Type check with mypy
      run: mypy app/

    - name: Test with pytest
      run: pytest --cov=app tests/
```

### Pre-commit конфигурация

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/pylint
    rev: v2.17.0
    hooks:
      - id: pylint
```

## 🛡️ Безопасность Примеры

### Валидация входных данных

```python
from pydantic import BaseModel, validator
import re

class MessageData(BaseModel):
    text: str
    user_id: int

    @validator('text')
    def validate_text(cls, v):
        # Проверка на XSS
        if '<script>' in v.lower():
            raise ValueError('Potentially malicious content detected')
        return v

    @validator('user_id')
    def validate_user_id(cls, v):
        if v <= 0:
            raise ValueError('Invalid user ID')
        return v
```

### Безопасная работа с БД

```python
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_user_safely(session: Session, user_id: int):
    """Safe database query with parameterized statement."""
    # ✅ Безопасно - параметризованный запрос
    result = session.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    return result.fetchone()

def get_user_unsafely(session: Session, user_id: int):
    """❌ НЕ БЕЗОПАСНО - SQL инъекция возможна"""
    # НЕ ДЕЛАЙТЕ ТАК!
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = session.execute(text(query))
    return result.fetchone()
```

---

## 💡 Как использовать примеры

1. **Копируйте код** в свой проект
2. **Адаптируйте** под свои нужды
3. **Изучайте** официальную документацию для понимания
4. **Тестируйте** перед использованием в продакшене
5. **Следуйте** лучшим практикам безопасности

**Помните:** Эти примеры основаны на официальной документации и лучших практиках!
