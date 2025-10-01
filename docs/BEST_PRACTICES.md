# 🎯 Лучшие практики разработки

## 📋 Общие принципы

### 1. **Структура проекта**
```
project/
├── app/
│   ├── handlers/          # Обработчики команд
│   ├── middlewares/       # Middleware
│   ├── services/          # Бизнес-логика
│   ├── models/           # Модели данных
│   ├── filters/          # Фильтры
│   └── utils/            # Утилиты
├── docs/                 # Документация
├── tests/               # Тесты
└── scripts/             # Скрипты
```

### 2. **Именование файлов и функций**
- Используйте snake_case для файлов и функций
- Используйте PascalCase для классов
- Используйте UPPER_CASE для констант

### 3. **Документация**
- Каждая функция должна иметь docstring
- Сложная логика должна быть прокомментирована
- Ведите CHANGELOG.md

## 🔧 Разработка с aiogram 3.x

### 1. **Dependency Injection - ВСТРОЕННЫЙ DI AIOGRAM ЛУЧШИЙ ВЫБОР!**

```python
# ✅ ПРАВИЛЬНО - Встроенный DI Aiogram 3.x
@router.message(Command("start"))
async def handle_start_command(
    message: Message,                    # 1. Event объект
    moderation_service: ModerationService,  # 2. Сервис (автоматически инжектируется!)
    admin_id: int,                      # 3. Конфигурация
) -> None:
    """Handle /start command."""
    # Сервис уже готов к использованию!
    await moderation_service.ban_user(...)

# ❌ НЕПРАВИЛЬНО - Внешние DI библиотеки
@router.message(Command("start"))
async def handle_start_command(message: Message, **kwargs) -> None:
    # Получение сервисов из kwargs - устаревший подход
    service = kwargs.get("service")
    # Отсутствует параметр data
    pass
```

### 2. **DIMiddleware - Основной DI контейнер**

```python
# ✅ ПРАВИЛЬНО - Использование DIMiddleware
class DIMiddleware(BaseMiddleware):
    """Middleware для Dependency Injection в Aiogram 3.x."""
    
    async def __call__(self, handler, event, data):
        # Создаем сервисы один раз и кэшируем
        if not self._initialized:
            await self._initialize_services(data)
            self._initialized = True
        
        # Добавляем все сервисы в data для хендлеров
        data.update(self._services)
        return await handler(event, data)

# ❌ НЕПРАВИЛЬНО - Внешние DI библиотеки
from punq import Container  # НЕ ИСПОЛЬЗУЙТЕ!
from dependency_injector import containers  # НЕ ИСПОЛЬЗУЙТЕ!
```

### 3. **Middleware**
```python
# ✅ ПРАВИЛЬНО
class CustomMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
        **kwargs
    ) -> Any:
        # Логика middleware
        return await handler(event, data)

# ❌ НЕПРАВИЛЬНО
class CustomMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data) -> Any:
        # Отсутствует **kwargs
        return await handler(event, data)
```

### 3. **Dependency Injection**
```python
# ✅ ПРАВИЛЬНО
class DependencyInjectionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data, **kwargs) -> Any:
        # Создание сервисов
        services = {
            "service1": Service1(bot, db_session),
            "service2": Service2(bot, db_session),
        }

        # Добавление в data
        data.update(services)

        # Передача в обработчик
        return await handler(event, data)
```

## 🐳 Docker разработка

### 1. **Dockerfile**
```dockerfile
# ✅ ПРАВИЛЬНО
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --fix-missing \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Запуск приложения
CMD ["python", "bot.py"]
```

### 2. **docker-compose.yml**
```yaml
# ✅ ПРАВИЛЬНО
version: '3.8'

services:
  antispam-bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - DB_PATH=${DB_PATH}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## 🔍 Отладка и логирование

### 1. **Настройка логирования**
```python
# ✅ ПРАВИЛЬНО
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Использование в коде
logger.info("Operation completed successfully")
logger.error(f"Error occurred: {error}")
logger.debug(f"Debug info: {debug_data}")
```

### 2. **Обработка ошибок**
```python
# ✅ ПРАВИЛЬНО
async def handle_command(message: Message, **kwargs) -> None:
    try:
        # Основная логика
        result = await some_operation()
        await message.answer(f"Result: {result}")

    except SpecificException as e:
        logger.error(f"Specific error: {e}")
        await message.answer("❌ Произошла ошибка")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await message.answer("❌ Неожиданная ошибка")
```

### 3. **Валидация данных**
```python
# ✅ ПРАВИЛЬНО
def validate_user_id(user_id: int) -> bool:
    """Validate user ID."""
    if not isinstance(user_id, int):
        return False
    if user_id <= 0:
        return False
    if len(str(user_id)) < 6:  # Telegram ID обычно длиннее 6 цифр
        return False
    return True
```

## 🧪 Тестирование

### 1. **Структура тестов**
```
tests/
├── __init__.py
├── conftest.py
├── test_handlers.py
├── test_services.py
└── test_middlewares.py
```

### 2. **Пример теста**
```python
# ✅ ПРАВИЛЬНО
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.handlers.admin import handle_start_command

@pytest.mark.asyncio
async def test_handle_start_command():
    # Создание мока сообщения
    message = MagicMock()
    message.from_user.id = 123456789
    message.answer = AsyncMock()

    # Вызов обработчика
    await handle_start_command(message, data={})

    # Проверка результата
    message.answer.assert_called_once()
```

## 📚 Документация

### 1. **README.md**
- Описание проекта
- Быстрый старт
- Ссылки на документацию
- Примеры использования

### 2. **API документация**
- Описание всех команд
- Параметры и возвращаемые значения
- Примеры запросов и ответов

### 3. **Troubleshooting**
- Описание частых проблем
- Пошаговые решения
- Команды для отладки

## 🔒 Безопасность

### 1. **Обработка токенов**
```python
# ✅ ПРАВИЛЬНО
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str

    class Config:
        env_file = ".env"

# ❌ НЕПРАВИЛЬНО
BOT_TOKEN = "hardcoded_token"  # Никогда не хардкодите токены
```

### 2. **Валидация входных данных**
```python
# ✅ ПРАВИЛЬНО
def sanitize_input(text: str) -> str:
    """Sanitize user input."""
    # Удаление HTML тегов
    import re
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text[:1000]  # Ограничение длины
```

### 3. **Rate Limiting**
```python
# ✅ ПРАВИЛЬНО
class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, user_limit: int = 10, admin_limit: int = 100):
        self.user_limit = user_limit
        self.admin_limit = admin_limit
        self.requests = {}
```

## 🚀 Деплой

### 1. **Подготовка к деплою**
- [ ] Все тесты проходят
- [ ] Документация обновлена
- [ ] Переменные окружения настроены
- [ ] Docker образ собран
- [ ] Логи проверены

### 2. **Мониторинг**
```bash
# Проверка статуса
docker ps

# Просмотр логов
docker logs antispam-bot -f

# Проверка ресурсов
docker stats antispam-bot
```

### 3. **Резервное копирование**
```bash
# Бэкап базы данных
docker exec antispam-bot cp /app/db.sqlite3 /app/backup/

# Бэкап конфигурации
cp .env .env.backup
```

## 📈 Мониторинг и метрики

### 1. **Логирование метрик**
```python
# ✅ ПРАВИЛЬНО
import time

async def track_performance(func):
    start_time = time.time()
    result = await func()
    duration = time.time() - start_time

    logger.info(f"Function {func.__name__} took {duration:.2f}s")
    return result
```

### 2. **Health checks**
```python
# ✅ ПРАВИЛЬНО
async def health_check():
    """Check bot health."""
    try:
        # Проверка базы данных
        await db.execute("SELECT 1")

        # Проверка API
        await bot.get_me()

        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

*Документ обновлен: 12 сентября 2025*
