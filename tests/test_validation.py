"""
Тесты валидации для AntiSpam Bot
"""

import pytest
from unittest.mock import Mock, AsyncMock
from aiogram.types import Message, User, Chat, CallbackQuery

from app.middlewares.validation import ValidationMiddleware, CommandValidationMiddleware
from app.constants import ERROR_MESSAGES


class TestValidationMiddleware:
    """Тесты ValidationMiddleware"""
    
    @pytest.fixture
    def validation_middleware(self):
        """Фикстура для ValidationMiddleware"""
        return ValidationMiddleware()
    
    @pytest.fixture
    def mock_message(self):
        """Фикстура для тестового сообщения"""
        user = User(
            id=123456789,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        chat = Chat(id=-1001234567890, type="supergroup")
        
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="Test message"
        )
        return message
    
    @pytest.fixture
    def mock_callback_query(self):
        """Фикстура для тестового callback query"""
        user = User(
            id=123456789,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
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
        return callback_query
    
    @pytest.mark.asyncio
    async def test_validate_message_success(self, validation_middleware, mock_message):
        """Тест успешной валидации сообщения"""
        result = await validation_middleware._validate_message(mock_message)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_message_missing_chat(self, validation_middleware):
        """Тест валидации сообщения без чата"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=None,  # Отсутствует чат
            from_user=user,
            text="Test message"
        )
        
        result = await validation_middleware._validate_message(message)
        
        assert result["is_valid"] is False
        assert "Отсутствует информация о чате" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_message_missing_user_id(self, validation_middleware):
        """Тест валидации сообщения без ID пользователя"""
        user = User(id=None, is_bot=False, first_name="Test")  # Отсутствует ID
        chat = Chat(id=-1001234567890, type="supergroup")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="Test message"
        )
        
        result = await validation_middleware._validate_message(message)
        
        assert result["is_valid"] is False
        assert "Отсутствует ID пользователя" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_message_too_long(self, validation_middleware, mock_message):
        """Тест валидации слишком длинного сообщения"""
        # Создаем сообщение длиннее 4096 символов
        long_text = "a" * 5000
        mock_message.text = long_text
        
        result = await validation_middleware._validate_message(mock_message)
        
        assert result["is_valid"] is False
        assert "Сообщение слишком длинное" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_message_suspicious_content(self, validation_middleware, mock_message):
        """Тест валидации подозрительного содержимого"""
        # Сообщение с JavaScript
        mock_message.text = "<script>alert('xss')</script>"
        
        result = await validation_middleware._validate_message(mock_message)
        
        assert result["is_valid"] is False
        assert "Подозрительное содержимое сообщения" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_callback_query_success(self, validation_middleware, mock_callback_query):
        """Тест успешной валидации callback query"""
        result = await validation_middleware._validate_callback_query(mock_callback_query)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_callback_query_missing_data(self, validation_middleware):
        """Тест валидации callback query без данных"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        callback_query = CallbackQuery(
            id="test_callback",
            from_user=user,
            chat_instance="test_chat",
            data=None  # Отсутствуют данные
        )
        
        result = await validation_middleware._validate_callback_query(callback_query)
        
        assert result["is_valid"] is False
        assert "Отсутствуют данные callback query" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_callback_query_too_long(self, validation_middleware, mock_callback_query):
        """Тест валидации слишком длинных данных callback query"""
        # Данные длиннее 64 символов
        long_data = "a" * 100
        mock_callback_query.data = long_data
        
        result = await validation_middleware._validate_callback_query(mock_callback_query)
        
        assert result["is_valid"] is False
        assert "Callback data слишком длинные" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_callback_query_suspicious_data(self, validation_middleware, mock_callback_query):
        """Тест валидации подозрительных данных callback query"""
        # Данные с JavaScript
        mock_callback_query.data = "<script>alert('xss')</script>"
        
        result = await validation_middleware._validate_callback_query(mock_callback_query)
        
        assert result["is_valid"] is False
        assert "Подозрительные данные callback query" in result["errors"]
    
    def test_is_suspicious_text_javascript(self, validation_middleware):
        """Тест обнаружения JavaScript в тексте"""
        suspicious_texts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "eval('malicious_code')",
            "alert('xss')",
            "confirm('xss')",
            "prompt('xss')",
        ]
        
        for text in suspicious_texts:
            assert validation_middleware._is_suspicious_text(text), f"Должен обнаружить подозрительный текст: {text}"
    
    def test_is_suspicious_text_path_traversal(self, validation_middleware):
        """Тест обнаружения path traversal в тексте"""
        suspicious_texts = [
            "../../etc/passwd",
            "..\\windows\\system32",
            "....//etc/passwd",
        ]
        
        for text in suspicious_texts:
            assert validation_middleware._is_suspicious_text(text), f"Должен обнаружить path traversal: {text}"
    
    def test_is_suspicious_text_sql_injection(self, validation_middleware):
        """Тест обнаружения SQL injection в тексте"""
        suspicious_texts = [
            "SELECT * FROM users",
            "INSERT INTO users VALUES",
            "UPDATE users SET password",
            "DELETE FROM users",
            "DROP TABLE users",
        ]
        
        for text in suspicious_texts:
            assert validation_middleware._is_suspicious_text(text), f"Должен обнаружить SQL injection: {text}"
    
    def test_is_suspicious_text_safe(self, validation_middleware):
        """Тест что безопасные тексты не блокируются"""
        safe_texts = [
            "Hello world",
            "This is a normal message",
            "User performed action",
            "Settings updated successfully",
            "Channel added",
        ]
        
        for text in safe_texts:
            assert not validation_middleware._is_suspicious_text(text), f"Не должен блокировать безопасный текст: {text}"
    
    def test_is_safe_media_document_too_large(self, validation_middleware):
        """Тест проверки слишком большого документа"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        chat = Chat(id=-1001234567890, type="supergroup")
        
        # Создаем документ размером больше 50MB
        from aiogram.types import Document
        large_document = Document(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            file_name="large_file.pdf",
            file_size=60 * 1024 * 1024,  # 60MB
            mime_type="application/pdf"
        )
        
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            document=large_document
        )
        
        assert not validation_middleware._is_safe_media(message)
    
    def test_is_safe_media_video_too_large(self, validation_middleware):
        """Тест проверки слишком большого видео"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        chat = Chat(id=-1001234567890, type="supergroup")
        
        # Создаем видео размером больше 100MB
        from aiogram.types import Video
        large_video = Video(
            file_id="test_video_id",
            file_unique_id="test_video_unique_id",
            width=1920,
            height=1080,
            duration=3600,
            file_size=150 * 1024 * 1024,  # 150MB
            mime_type="video/mp4"
        )
        
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            video=large_video
        )
        
        assert not validation_middleware._is_safe_media(message)
    
    def test_is_safe_media_safe_content(self, validation_middleware, mock_message):
        """Тест что безопасный контент проходит проверку"""
        # Обычное текстовое сообщение
        assert validation_middleware._is_safe_media(mock_message)
        
        # Сообщение с небольшим документом
        from aiogram.types import Document
        small_document = Document(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            file_name="small_file.txt",
            file_size=1024,  # 1KB
            mime_type="text/plain"
        )
        mock_message.document = small_document
        
        assert validation_middleware._is_safe_media(mock_message)


class TestCommandValidationMiddleware:
    """Тесты CommandValidationMiddleware"""
    
    @pytest.fixture
    def command_middleware(self):
        """Фикстура для CommandValidationMiddleware"""
        return CommandValidationMiddleware()
    
    @pytest.fixture
    def mock_command_message(self):
        """Фикстура для тестового сообщения с командой"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        chat = Chat(id=-1001234567890, type="supergroup")
        
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text="/help admin"
        )
        return message
    
    @pytest.mark.asyncio
    async def test_validate_command_success(self, command_middleware, mock_command_message):
        """Тест успешной валидации команды"""
        result = await command_middleware._validate_command(mock_command_message)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_command_missing_text(self, command_middleware):
        """Тест валидации команды без текста"""
        user = User(id=123456789, is_bot=False, first_name="Test")
        chat = Chat(id=-1001234567890, type="supergroup")
        
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            text=None  # Отсутствует текст
        )
        
        result = await command_middleware._validate_command(message)
        
        assert result["is_valid"] is False
        assert "Отсутствует текст команды" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_command_too_long(self, command_middleware, mock_command_message):
        """Тест валидации слишком длинной команды"""
        # Команда длиннее 32 символов
        long_command = "/" + "a" * 35
        mock_command_message.text = long_command
        
        result = await command_middleware._validate_command(mock_command_message)
        
        assert result["is_valid"] is False
        assert "Команда слишком длинная" in result["errors"]
    
    @pytest.mark.asyncio
    async def test_validate_command_suspicious_parameter(self, command_middleware, mock_command_message):
        """Тест валидации команды с подозрительным параметром"""
        # Команда с JavaScript в параметре
        mock_command_message.text = "/help <script>alert('xss')</script>"
        
        result = await command_middleware._validate_command(mock_command_message)
        
        assert result["is_valid"] is False
        assert "Подозрительный параметр команды" in result["errors"]
    
    def test_is_suspicious_text_command_middleware(self, command_middleware):
        """Тест обнаружения подозрительного текста в CommandValidationMiddleware"""
        suspicious_texts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "eval('malicious_code')",
            "../../etc/passwd",
            "SELECT * FROM users",
        ]
        
        for text in suspicious_texts:
            assert command_middleware._is_suspicious_text(text), f"Должен обнаружить подозрительный текст: {text}"
    
    def test_is_suspicious_text_safe_command_middleware(self, command_middleware):
        """Тест что безопасные тексты не блокируются в CommandValidationMiddleware"""
        safe_texts = [
            "admin",
            "help",
            "status",
            "channels",
            "bans",
        ]
        
        for text in safe_texts:
            assert not command_middleware._is_suspicious_text(text), f"Не должен блокировать безопасный текст: {text}"


if __name__ == "__main__":
    pytest.main([__file__])
