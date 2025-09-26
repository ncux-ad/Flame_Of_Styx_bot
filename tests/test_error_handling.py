"""
Тесты обработки ошибок для AntiSpam Bot
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiogram.types import Message, User, Chat, CallbackQuery

from app.utils.error_handling import (
    ErrorHandler, BotError, ValidationError, AuthenticationError,
    AuthorizationError, RateLimitError, DatabaseError, TelegramAPIError,
    SecurityError, ErrorSeverity, ErrorCategory, handle_errors,
    send_error_message, get_error_summary
)


class TestBotError:
    """Тесты базового класса BotError"""
    
    def test_bot_error_creation(self):
        """Тест создания BotError"""
        error = BotError(
            message="Test error",
            code=100,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details={"key": "value"},
            user_message="User message"
        )
        
        assert error.message == "Test error"
        assert error.code == 100
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details == {"key": "value"}
        assert error.user_message == "User message"
    
    def test_bot_error_defaults(self):
        """Тест создания BotError с значениями по умолчанию"""
        error = BotError("Test error")
        
        assert error.message == "Test error"
        assert error.code == 1  # UNKNOWN_ERROR
        assert error.category == ErrorCategory.INTERNAL
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details == {}
        assert error.user_message == "❌ Произошла ошибка бота. Попробуйте позже."


class TestSpecificErrors:
    """Тесты специфических типов ошибок"""
    
    def test_validation_error(self):
        """Тест ValidationError"""
        error = ValidationError("Invalid input", {"field": "username"})
        
        assert error.message == "Invalid input"
        assert error.code == 2  # INVALID_REQUEST
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details == {"field": "username"}
        assert error.user_message == "❌ Некорректные входные данные"
    
    def test_authentication_error(self):
        """Тест AuthenticationError"""
        error = AuthenticationError("Invalid token")
        
        assert error.message == "Invalid token"
        assert error.code == 3  # UNAUTHORIZED
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.user_message == "❌ У вас нет прав для выполнения этой команды"
    
    def test_authorization_error(self):
        """Тест AuthorizationError"""
        error = AuthorizationError("Access denied")
        
        assert error.message == "Access denied"
        assert error.code == 4  # FORBIDDEN
        assert error.category == ErrorCategory.AUTHORIZATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.user_message == "❌ У вас нет прав для выполнения этой команды"
    
    def test_rate_limit_error(self):
        """Тест RateLimitError"""
        error = RateLimitError("Too many requests")
        
        assert error.message == "Too many requests"
        assert error.code == 200  # RATE_LIMIT_EXCEEDED
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.user_message == "⏳ Слишком часто пишешь, притормози."
    
    def test_database_error(self):
        """Тест DatabaseError"""
        error = DatabaseError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.code == 301  # DB_QUERY_ERROR
        assert error.category == ErrorCategory.DATABASE
        assert error.severity == ErrorSeverity.HIGH
        assert error.user_message == "❌ Произошла ошибка бота. Попробуйте позже."
    
    def test_telegram_api_error(self):
        """Тест TelegramAPIError"""
        error = TelegramAPIError("API error")
        
        assert error.message == "API error"
        assert error.code == 1  # UNKNOWN_ERROR
        assert error.category == ErrorCategory.TELEGRAM_API
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.user_message == "❌ Произошла ошибка бота. Попробуйте позже."
    
    def test_security_error(self):
        """Тест SecurityError"""
        error = SecurityError("Security violation")
        
        assert error.message == "Security violation"
        assert error.code == 1  # UNKNOWN_ERROR
        assert error.category == ErrorCategory.SECURITY
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.user_message == "❌ Произошла ошибка бота. Попробуйте позже."


class TestErrorHandler:
    """Тесты ErrorHandler"""
    
    @pytest.fixture
    def error_handler(self):
        """Фикстура для ErrorHandler"""
        return ErrorHandler()
    
    @pytest.mark.asyncio
    async def test_handle_bot_error(self, error_handler):
        """Тест обработки BotError"""
        error = ValidationError("Test validation error")
        context = {"field": "username"}
        
        with patch.object(error_handler, '_log_error') as mock_log:
            await error_handler.handle_error(error, context, user_id=123, chat_id=456)
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == error
            assert call_args[0][1] == context
            assert call_args[0][2] == 123
            assert call_args[0][3] == 456
    
    @pytest.mark.asyncio
    async def test_handle_standard_error(self, error_handler):
        """Тест обработки стандартной ошибки"""
        error = ValueError("Test value error")
        
        with patch.object(error_handler, '_log_error') as mock_log:
            await error_handler.handle_error(error, user_id=123)
            
            mock_log.assert_called_once()
            logged_error = mock_log.call_args[0][0]
            assert isinstance(logged_error, ValidationError)
            assert "Test value error" in logged_error.message
    
    @pytest.mark.asyncio
    async def test_handle_telegram_error(self, error_handler):
        """Тест обработки Telegram ошибки"""
        from aiogram.exceptions import TelegramBadRequest
        
        error = TelegramBadRequest("Bad request")
        
        with patch.object(error_handler, '_log_error') as mock_log:
            await error_handler.handle_error(error, user_id=123)
            
            mock_log.assert_called_once()
            logged_error = mock_log.call_args[0][0]
            assert isinstance(logged_error, TelegramAPIError)
            assert "Telegram Bad Request" in logged_error.message
    
    def test_classify_error_bot_error(self, error_handler):
        """Тест классификации BotError"""
        error = ValidationError("Test error")
        result = error_handler._classify_error(error)
        
        assert result == error
    
    def test_classify_error_value_error(self, error_handler):
        """Тест классификации ValueError"""
        error = ValueError("Test value error")
        result = error_handler._classify_error(error)
        
        assert isinstance(result, ValidationError)
        assert "Test value error" in result.message
    
    def test_classify_error_permission_error(self, error_handler):
        """Тест классификации PermissionError"""
        error = PermissionError("Permission denied")
        result = error_handler._classify_error(error)
        
        assert isinstance(result, AuthorizationError)
        assert "Permission denied" in result.message
    
    def test_classify_error_unknown(self, error_handler):
        """Тест классификации неизвестной ошибки"""
        error = RuntimeError("Unknown error")
        result = error_handler._classify_error(error)
        
        assert isinstance(result, BotError)
        assert "Unknown Error" in result.message
        assert "traceback" in result.details
    
    @pytest.mark.asyncio
    async def test_log_error_critical(self, error_handler):
        """Тест логирования критической ошибки"""
        error = SecurityError("Critical security issue")
        
        with patch('app.utils.error_handling.logger') as mock_logger:
            await error_handler._log_error(error, {}, 123, 456)
            
            mock_logger.critical.assert_called_once()
            log_message = mock_logger.critical.call_args[0][0]
            assert "CRITICAL" in log_message
            assert "User: 123" in log_message
            assert "Chat: 456" in log_message
    
    @pytest.mark.asyncio
    async def test_log_error_high(self, error_handler):
        """Тест логирования высокой ошибки"""
        error = DatabaseError("Database connection failed")
        
        with patch('app.utils.error_handling.logger') as mock_logger:
            await error_handler._log_error(error, {}, 123, 456)
            
            mock_logger.error.assert_called_once()
            log_message = mock_logger.error.call_args[0][0]
            assert "HIGH" in log_message
    
    @pytest.mark.asyncio
    async def test_log_error_medium(self, error_handler):
        """Тест логирования средней ошибки"""
        error = ValidationError("Validation failed")
        
        with patch('app.utils.error_handling.logger') as mock_logger:
            await error_handler._log_error(error, {}, 123, 456)
            
            mock_logger.warning.assert_called_once()
            log_message = mock_logger.warning.call_args[0][0]
            assert "MEDIUM" in log_message
    
    @pytest.mark.asyncio
    async def test_log_error_low(self, error_handler):
        """Тест логирования низкой ошибки"""
        error = BotError("Low severity error", severity=ErrorSeverity.LOW)
        
        with patch('app.utils.error_handling.logger') as mock_logger:
            await error_handler._log_error(error, {}, 123, 456)
            
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "LOW" in log_message
    
    @pytest.mark.asyncio
    async def test_check_error_limits(self, error_handler):
        """Тест проверки лимитов ошибок"""
        error = BotError("Test error", severity=ErrorSeverity.MEDIUM)
        
        # Добавляем ошибки до превышения лимита
        for _ in range(51):  # Лимит для MEDIUM = 50
            await error_handler._check_error_limits(error)
        
        # Проверяем что счетчик обновился
        assert error_handler.error_counts["internal_medium"] == 51
    
    @pytest.mark.asyncio
    async def test_log_security_event(self, error_handler):
        """Тест логирования события безопасности"""
        error = SecurityError("Critical security issue")
        
        with patch('app.utils.error_handling.log_security_event') as mock_log_security:
            await error_handler._log_security_event(error, {}, 123, 456)
            
            mock_log_security.assert_called_once()
            call_args = mock_log_security.call_args
            assert call_args[0][0] == "critical_error"
            assert call_args[0][1] == 123
            assert call_args[0][2]["error_code"] == error.code
            assert call_args[0][2]["error_category"] == error.category.value


class TestHandleErrorsDecorator:
    """Тесты декоратора handle_errors"""
    
    @pytest.mark.asyncio
    async def test_handle_errors_success(self):
        """Тест успешного выполнения функции с декоратором"""
        @handle_errors()
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_handle_errors_with_exception(self):
        """Тест обработки исключения с декоратором"""
        @handle_errors(user_message="Test error message")
        async def test_function():
            raise ValueError("Test error")
        
        result = await test_function()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_errors_with_message_context(self):
        """Тест обработки ошибки с контекстом сообщения"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        chat = Chat(id=-1001234567890, type="supergroup")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="Test message"
        )
        
        @handle_errors(user_message="Test error message")
        async def test_function(msg: Message):
            raise ValueError("Test error")
        
        with patch('app.utils.error_handling.error_handler.handle_error') as mock_handle:
            result = await test_function(message)
            
            assert result is None
            mock_handle.assert_called_once()
            call_args = mock_handle.call_args
            assert call_args[0][2]["message_text"] == "Test message"
            assert call_args[0][3] == 123456789
            assert call_args[0][4] == -1001234567890
    
    @pytest.mark.asyncio
    async def test_handle_errors_with_callback_context(self):
        """Тест обработки ошибки с контекстом callback query"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        chat = Chat(id=-1001234567890, type="supergroup")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="Test message"
        )
        callback_query = CallbackQuery(
            id="test_callback",
            from_user=user,
            chat_instance="test_chat",
            data="test_data"
        )
        callback_query.message = message
        
        @handle_errors(user_message="Test error message")
        async def test_function(cb: CallbackQuery):
            raise ValueError("Test error")
        
        with patch('app.utils.error_handling.error_handler.handle_error') as mock_handle:
            result = await test_function(callback_query)
            
            assert result is None
            mock_handle.assert_called_once()
            call_args = mock_handle.call_args
            assert call_args[0][2]["callback_data"] == "test_data"
            assert call_args[0][3] == 123456789
            assert call_args[0][4] == -1001234567890
    
    @pytest.mark.asyncio
    async def test_handle_errors_reraise(self):
        """Тест декоратора с reraise=True"""
        @handle_errors(reraise=True)
        async def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await test_function()
    
    @pytest.mark.asyncio
    async def test_handle_errors_no_log(self):
        """Тест декоратора с log_error=False"""
        @handle_errors(log_error=False)
        async def test_function():
            raise ValueError("Test error")
        
        with patch('app.utils.error_handling.error_handler.handle_error') as mock_handle:
            result = await test_function()
            
            assert result is None
            mock_handle.assert_not_called()


class TestSendErrorMessage:
    """Тесты функции send_error_message"""
    
    @pytest.mark.asyncio
    async def test_send_error_message_to_message(self):
        """Тест отправки сообщения об ошибке в Message"""
        # Создаем мок объекты вместо реальных Telegram объектов
        mock_message = Mock()
        mock_message.answer = AsyncMock()
        
        error = ValidationError("Test validation error")
        
        await send_error_message(mock_message, error)
        
        mock_message.answer.assert_called_once_with(error.user_message)
    
    @pytest.mark.asyncio
    async def test_send_error_message_to_callback_query(self):
        """Тест отправки сообщения об ошибке в CallbackQuery"""
        # Создаем мок объекты вместо реальных Telegram объектов
        mock_callback = Mock()
        mock_callback.answer = AsyncMock()
        
        error = ValidationError("Test validation error")
        
        await send_error_message(mock_callback, error)
        
        mock_callback.answer.assert_called_once_with(error.user_message)
    
    @pytest.mark.asyncio
    async def test_send_error_message_with_custom_message(self):
        """Тест отправки сообщения об ошибке с пользовательским сообщением"""
        # Создаем мок объекты вместо реальных Telegram объектов
        mock_message = Mock()
        mock_message.answer = AsyncMock()
        
        error = ValidationError("Test validation error")
        custom_message = "Custom error message"
        
        await send_error_message(mock_message, error, custom_message)
        
        mock_message.answer.assert_called_once_with(custom_message)
    
    @pytest.mark.asyncio
    async def test_send_error_message_exception_handling(self):
        """Тест обработки исключений при отправке сообщения об ошибке"""
        # Создаем мок объекты вместо реальных Telegram объектов
        mock_message = Mock()
        mock_message.answer = AsyncMock(side_effect=Exception("Send error"))
        
        error = ValidationError("Test validation error")
        
        with patch('app.utils.error_handling.logger') as mock_logger:
            await send_error_message(mock_message, error)
            
            mock_logger.error.assert_called_once()
            assert "Ошибка отправки сообщения об ошибке" in mock_logger.error.call_args[0][0]


class TestGetErrorSummary:
    """Тесты функции get_error_summary"""
    
    def test_get_error_summary(self):
        """Тест получения сводки по ошибкам"""
        # Добавляем несколько ошибок
        from app.utils.error_handling import error_handler
        
        error_handler.error_counts = {
            "validation_medium": 10,
            "database_high": 5,
            "security_critical": 2
        }
        
        summary = get_error_summary()
        
        assert "error_counts" in summary
        assert "total_errors" in summary
        assert "error_thresholds" in summary
        
        assert summary["error_counts"]["validation_medium"] == 10
        assert summary["error_counts"]["database_high"] == 5
        assert summary["error_counts"]["security_critical"] == 2
        assert summary["total_errors"] == 17
        
        assert ErrorSeverity.LOW in summary["error_thresholds"]
        assert ErrorSeverity.MEDIUM in summary["error_thresholds"]
        assert ErrorSeverity.HIGH in summary["error_thresholds"]
        assert ErrorSeverity.CRITICAL in summary["error_thresholds"]


if __name__ == "__main__":
    pytest.main([__file__])
