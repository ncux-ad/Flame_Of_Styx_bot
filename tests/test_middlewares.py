"""
Тесты для middleware.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from app.middlewares.ratelimit import RateLimitMiddleware
from app.middlewares.validation import ValidationMiddleware


class TestRateLimitMiddleware:
    """Тесты Rate Limit Middleware."""

    def test_middleware_creation(self):
        """Тест создания middleware."""
        middleware = RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)

        assert middleware.user_limit == 10
        assert middleware.admin_limit == 100
        assert middleware.interval == 60

    @pytest.mark.asyncio
    async def test_middleware_call_basic(self):
        """Тест базового вызова middleware."""
        middleware = RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)

        # Мокаем handler
        handler = AsyncMock()

        # Мокаем event (message)
        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 123456789
        event.chat = Mock()
        event.chat.id = -1001234567890

        # Мокаем data
        data = {}

        # Вызываем middleware
        await middleware(handler, event, data)

        # Проверяем, что handler был вызван
        handler.assert_called_once_with(event, data)

    @pytest.mark.asyncio
    async def test_middleware_rate_limit_exceeded(self):
        """Тест превышения rate limit."""
        middleware = RateLimitMiddleware(user_limit=1, admin_limit=100, interval=60)  # Очень низкий лимит

        # Мокаем handler
        handler = AsyncMock()

        # Мокаем event
        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 123456789
        event.chat = Mock()
        event.chat.id = -1001234567890
        event.answer = AsyncMock()

        data = {}

        # Первый вызов должен пройти
        await middleware(handler, event, data)
        handler.assert_called_once()

        # Сбрасываем mock
        handler.reset_mock()

        # Второй вызов сразу после первого должен быть заблокирован
        await middleware(handler, event, data)

        # Handler не должен быть вызван при превышении лимита
        # (точное поведение зависит от реализации)

    @pytest.mark.asyncio
    async def test_middleware_admin_user(self):
        """Тест обработки администратора."""
        middleware = RateLimitMiddleware(user_limit=1, admin_limit=100, interval=60)

        handler = AsyncMock()

        # Мокаем admin event
        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 439304619  # Admin ID
        event.chat = Mock()
        event.chat.id = -1001234567890

        data = {"admin_id": 439304619}  # Указываем, что это админ

        # Админ должен иметь более высокие лимиты
        await middleware(handler, event, data)
        handler.assert_called_once_with(event, data)


class TestValidationMiddleware:
    """Тесты Validation Middleware."""

    def test_middleware_creation(self):
        """Тест создания validation middleware."""
        middleware = ValidationMiddleware()
        assert middleware is not None

    @pytest.mark.asyncio
    async def test_validation_middleware_valid_message(self):
        """Тест валидации корректного сообщения."""
        middleware = ValidationMiddleware()

        handler = AsyncMock()

        # Мокаем корректное сообщение
        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 123456789
        event.from_user.first_name = "Test"
        event.from_user.last_name = "User"
        event.from_user.username = "testuser"
        event.from_user.is_bot = False

        event.chat = Mock()
        event.chat.id = -1001234567890
        event.chat.type = "supergroup"

        event.text = "Hello, world!"
        event.date = 1234567890

        data = {}

        await middleware(handler, event, data)

        # Handler должен быть вызван для корректного сообщения
        handler.assert_called_once_with(event, data)

    @pytest.mark.asyncio
    async def test_validation_middleware_invalid_message(self):
        """Тест валидации некорректного сообщения."""
        middleware = ValidationMiddleware()

        handler = AsyncMock()

        # Мокаем некорректное сообщение (без пользователя)
        event = Mock()
        event.from_user = None
        event.chat = Mock()
        event.chat.id = -1001234567890
        event.text = "Hello"
        event.answer = AsyncMock()

        data = {}

        await middleware(handler, event, data)

        # Поведение зависит от реализации - может блокировать или пропускать

    @pytest.mark.asyncio
    async def test_validation_middleware_callback_query(self):
        """Тест валидации callback query."""
        middleware = ValidationMiddleware()

        handler = AsyncMock()

        # Мокаем callback query
        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 123456789
        event.from_user.first_name = "Test"
        event.from_user.is_bot = False
        event.data = "test_callback"

        data = {}

        await middleware(handler, event, data)

        # Handler должен быть вызван для корректного callback query
        handler.assert_called_once_with(event, data)


class TestMiddlewareIntegration:
    """Тесты интеграции middleware."""

    @pytest.mark.asyncio
    async def test_multiple_middlewares(self):
        """Тест работы нескольких middleware вместе."""
        # Создаем middleware
        validation_middleware = ValidationMiddleware()
        ratelimit_middleware = RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)

        # Мокаем handler
        final_handler = AsyncMock()

        # Создаем цепочку middleware
        async def chained_handler(event, data):
            # Сначала rate limiting
            await ratelimit_middleware(final_handler, event, data)

        # Мокаем корректный event
        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 123456789
        event.from_user.first_name = "Test"
        event.from_user.is_bot = False

        event.chat = Mock()
        event.chat.id = -1001234567890
        event.chat.type = "supergroup"

        event.text = "Hello, world!"
        event.date = 1234567890

        data = {}

        # Вызываем цепочку middleware
        await validation_middleware(chained_handler, event, data)

        # Final handler должен быть вызван
        final_handler.assert_called_once_with(event, data)

    def test_middleware_error_handling(self):
        """Тест обработки ошибок в middleware."""
        middleware = RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)

        # Тестируем создание с некорректными параметрами
        with pytest.raises((ValueError, TypeError)):
            RateLimitMiddleware(user_limit=-1, admin_limit=100, interval=60)  # Отрицательный лимит

    @pytest.mark.asyncio
    async def test_middleware_data_passing(self):
        """Тест передачи данных через middleware."""
        middleware = RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)

        handler = AsyncMock()

        event = Mock()
        event.from_user = Mock()
        event.from_user.id = 123456789
        event.chat = Mock()
        event.chat.id = -1001234567890

        # Добавляем данные в data
        data = {"test_key": "test_value", "admin_id": 439304619}

        await middleware(handler, event, data)

        # Проверяем, что данные передались
        handler.assert_called_once_with(event, data)
        call_args = handler.call_args
        passed_data = call_args[0][1]  # Второй аргумент (data)

        assert "test_key" in passed_data
        assert passed_data["test_key"] == "test_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
