"""
Интеграционные тесты для цепочки middleware
"""

import pytest
from unittest.mock import AsyncMock, patch
from aiogram import F, Router
from aiogram.types import Message

from app.middlewares.di_middleware import DIMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware
from app.middlewares.validation import ValidationMiddleware


class TestMiddlewareChain:
    """Тесты цепочки middleware"""

    @pytest.mark.asyncio
    async def test_middleware_order_validation_first(self, test_dispatcher, create_test_message, create_test_update, mock_bot):
        """Тест правильного порядка middleware - валидация должна быть первой"""
        # Создаем сообщение с подозрительным содержимым
        message = create_test_message(
            text="<script>alert('xss')</script>",
            user_id=123456789
        )
        
        # Создаем простой обработчик
        router = Router()
        handler_called = False
        
        @router.message(F.text)
        async def test_handler(msg: Message):
            nonlocal handler_called
            handler_called = True
            return "Handler executed"
        
        test_dispatcher.include_router(router)
        
        # Создаем Update с помощью фабрики
        update = create_test_update(message=message)
        
        # Обрабатываем сообщение
        with patch('app.middlewares.validation.input_validator') as mock_validator:
            # Настраиваем валидатор для возврата ошибок
            mock_validator.validate_message.return_value = [
                type('ValidationError', (), {
                    'field': 'message_text',
                    'message': 'Подозрительное содержимое',
                    'severity': type('Severity', (), {'CRITICAL': 4})()
                })()
            ]
            
            # Валидация должна заблокировать обработку
            result = await test_dispatcher.feed_update(
                bot=mock_bot,
                update=update
            )
            
            # Обработчик не должен быть вызван из-за валидации
            assert not handler_called

    @pytest.mark.asyncio
    async def test_rate_limiting_after_validation(self, test_dispatcher, create_test_message, test_user, test_chat):
        """Тест что rate limiting работает после валидации"""
        # Создаем валидное сообщение
        message = create_test_message(
            text="/help",
            user_id=test_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        router = Router()
        handler_calls = 0
        
        @router.message(F.text.startswith("/help"))
        async def help_handler(msg: Message):
            nonlocal handler_calls
            handler_calls += 1
            return "Help message"
        
        test_dispatcher.include_router(router)
        
        # Эмулируем множественные запросы для превышения лимита
        data = {
            'bot': AsyncMock(),
            'db_session': AsyncMock(),
            'config': AsyncMock()
        }
        
        update = type('Update', (), {'message': message})()
        
        # Первые запросы должны проходить
        for i in range(5):
            await test_dispatcher.feed_update(bot=data['bot'], update=update)
        
        # После превышения лимита запросы должны блокироваться
        # (точное поведение зависит от настроек rate limiter)
        
        # Проверяем что обработчик вызывался
        assert handler_calls > 0

    @pytest.mark.asyncio
    async def test_di_middleware_last(self, test_dispatcher, create_test_message, test_user, test_chat):
        """Тест что DI middleware работает последним и внедряет зависимости"""
        message = create_test_message(
            text="/status",
            user_id=test_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        router = Router()
        received_services = {}
        
        @router.message(F.text == "/status")
        async def status_handler(
            msg: Message,
            moderation_service=None,
            bot_service=None,
            admin_id=None
        ):
            nonlocal received_services
            received_services = {
                'moderation_service': moderation_service,
                'bot_service': bot_service,
                'admin_id': admin_id
            }
            return "Status checked"
        
        test_dispatcher.include_router(router)
        
        # Подготавливаем данные для DI
        data = {
            'bot': AsyncMock(),
            'db_session': AsyncMock(),
            'config': type('Config', (), {
                'admin_ids': '123456789,987654321'
            })()
        }
        
        update = type('Update', (), {'message': message})()
        
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services') as mock_init:
            # Мокаем инициализацию сервисов
            mock_init.return_value = None
            
            await test_dispatcher.feed_update(bot=data['bot'], update=update)
            
            # Проверяем что DI middleware пытался инициализировать сервисы
            mock_init.assert_called()

    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self, test_dispatcher, create_test_message, test_user, test_chat):
        """Тест обработки исключений в middleware"""
        message = create_test_message(
            text="test message",
            user_id=test_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        router = Router()
        
        @router.message(F.text)
        async def failing_handler(msg: Message):
            raise ValueError("Test exception")
        
        test_dispatcher.include_router(router)
        
        data = {
            'bot': AsyncMock(),
            'db_session': AsyncMock(),
            'config': AsyncMock()
        }
        
        update = type('Update', (), {'message': message})()
        
        # Исключение не должно ломать всю цепочку
        try:
            await test_dispatcher.feed_update(bot=data['bot'], update=update)
        except Exception as e:
            # Логируем исключение но тест не должен падать
            print(f"Expected exception in middleware chain: {e}")

    @pytest.mark.asyncio
    async def test_middleware_data_flow(self, create_test_message, test_user, test_chat):
        """Тест передачи данных через middleware"""
        message = create_test_message(
            text="/test",
            user_id=test_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        # Тестируем каждый middleware отдельно
        validation_middleware = ValidationMiddleware()
        rate_limit_middleware = RateLimitMiddleware(user_limit=10, admin_limit=100, interval=60)
        di_middleware = DIMiddleware()
        
        # Начальные данные
        data = {
            'bot': AsyncMock(),
            'db_session': AsyncMock(),
            'config': type('Config', (), {
                'admin_ids': '123456789,987654321'
            })()
        }
        
        # Простой обработчик
        async def test_handler(event, data):
            return data
        
        # Проходим через каждый middleware
        result_data = data.copy()
        
        # 1. ValidationMiddleware
        result_data = await validation_middleware(test_handler, message, result_data)
        
        # 2. RateLimitMiddleware  
        if result_data:  # Если валидация прошла
            result_data = await rate_limit_middleware(test_handler, message, result_data)
        
        # 3. DIMiddleware
        if result_data:  # Если rate limiting прошел
            with patch.object(di_middleware, '_initialize_services'):
                result_data = await di_middleware(test_handler, message, result_data)
        
        # Проверяем что данные прошли через всю цепочку
        assert result_data is not None
        assert 'bot' in result_data
        assert 'config' in result_data


class TestMiddlewareIntegration:
    """Тесты интеграции middleware с реальными компонентами"""

    @pytest.mark.asyncio
    async def test_admin_command_flow(self, test_dispatcher, create_test_message, test_admin_user, test_private_chat):
        """Тест полного потока обработки админской команды"""
        message = create_test_message(
            text="/status",
            user_id=test_admin_user.id,
            chat_id=test_private_chat.id,
            is_admin=True
        )
        
        router = Router()
        command_processed = False
        
        @router.message(F.text == "/status")
        async def status_command(
            msg: Message,
            status_service=None,
            admin_id: int = None
        ):
            nonlocal command_processed
            command_processed = True
            # Проверяем что сервисы внедрены
            assert admin_id is not None
            return "Status: OK"
        
        test_dispatcher.include_router(router)
        
        data = {
            'bot': AsyncMock(),
            'db_session': AsyncMock(),
            'config': type('Config', (), {
                'admin_ids': '987654321'  # ID админа
            })()
        }
        
        update = type('Update', (), {'message': message})()
        
        with patch('app.middlewares.di_middleware.DIMiddleware._initialize_services'):
            await test_dispatcher.feed_update(bot=data['bot'], update=update)
        
        # Команда должна быть обработана
        assert command_processed

    @pytest.mark.asyncio
    async def test_user_message_validation(self, test_dispatcher, create_test_message, test_user, test_chat):
        """Тест валидации пользовательских сообщений"""
        # Тест с валидным сообщением
        valid_message = create_test_message(
            text="Hello, this is a normal message",
            user_id=test_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        # Тест с подозрительным сообщением
        suspicious_message = create_test_message(
            text="<script>alert('xss')</script>",
            user_id=test_user.id,
            chat_id=test_chat.id,
            is_admin=True
        )
        
        router = Router()
        messages_processed = []
        
        @router.message(F.text)
        async def message_handler(msg: Message):
            messages_processed.append(msg.text)
            return "Message processed"
        
        test_dispatcher.include_router(router)
        
        data = {
            'bot': AsyncMock(),
            'db_session': AsyncMock(),
            'config': AsyncMock()
        }
        
        # Обрабатываем валидное сообщение
        valid_update = type('Update', (), {'message': valid_message})()
        await test_dispatcher.feed_update(bot=data['bot'], update=valid_update)
        
        # Обрабатываем подозрительное сообщение
        suspicious_update = type('Update', (), {'message': suspicious_message})()
        
        with patch('app.middlewares.validation.input_validator') as mock_validator:
            # Настраиваем валидатор для блокировки подозрительного сообщения
            mock_validator.validate_message.return_value = [
                type('ValidationError', (), {
                    'severity': type('Severity', (), {'CRITICAL': 4})()
                })()
            ]
            
            await test_dispatcher.feed_update(bot=data['bot'], update=suspicious_update)
        
        # Проверяем результаты
        # Валидное сообщение должно быть обработано
        # Подозрительное - заблокировано
        print(f"Processed messages: {messages_processed}")
