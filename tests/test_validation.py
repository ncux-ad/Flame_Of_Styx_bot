"""
Тесты валидации для AntiSpam Bot
"""

from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from app.constants import ERROR_MESSAGES
from app.middlewares.validation import CommandValidationMiddleware, ValidationMiddleware


class TestValidationMiddleware:
    """Тесты ValidationMiddleware"""

    @pytest.fixture
    def validation_middleware(self):
        """Фикстура для ValidationMiddleware"""
        return ValidationMiddleware()

    @pytest.fixture
    def mock_message(self):
        """Фикстура для тестового сообщения"""
        user = User(id=123456789, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=-1001234567890, type="supergroup")

        message = Message(message_id=1, date=1234567890, chat=chat, from_user=user, text="Test message")
        return message

    @pytest.fixture
    def mock_callback_query(self):
        """Фикстура для тестового callback query"""
        user = User(id=123456789, is_bot=False, first_name="Test", username="testuser")
        chat = Chat(id=-1001234567890, type="supergroup")
        message = Message(message_id=1, date=1234567890, chat=chat, from_user=user, text="Test message")

        callback_query = CallbackQuery(id="test_callback", from_user=user, chat_instance="test_chat", data="test_data")
        return callback_query

    @pytest.mark.asyncio
    async def test_validate_message_success(self, validation_middleware, mock_message):
        """Тест успешной валидации сообщения"""
        result = await validation_middleware._validate_event(mock_message, {})

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_message_missing_chat(self, validation_middleware):
        """Тест валидации сообщения без чата"""
        from unittest.mock import Mock

        # Создаем мок-объекты вместо реальных Pydantic объектов
        user = Mock()
        user.id = 123456789
        user.is_bot = False

        message = Mock()
        message.chat = None  # Отсутствует чат
        message.from_user = user
        message.text = "Test message"
        message.photo = None
        message.video = None
        message.document = None

        result = await validation_middleware._validate_message(message)

        assert "Отсутствует информация о чате" in result

    @pytest.mark.asyncio
    async def test_validate_message_missing_user_id(self, validation_middleware):
        """Тест валидации сообщения без ID пользователя"""
        from unittest.mock import Mock

        # Создаем мок-объекты
        user = Mock()
        user.id = None  # Отсутствует ID
        user.is_bot = False

        chat = Mock()
        chat.id = -1001234567890

        message = Mock()
        message.chat = chat
        message.from_user = user
        message.text = "Test message"
        message.photo = None
        message.video = None
        message.document = None

        result = await validation_middleware._validate_message(message)

        assert "Отсутствует ID пользователя" in result

    @pytest.mark.asyncio
    async def test_validate_message_too_long(self, validation_middleware):
        """Тест валидации слишком длинного сообщения"""
        from unittest.mock import Mock

        # Создаем мок-объекты с длинным текстом
        user = Mock()
        user.id = 123456789
        user.is_bot = False

        chat = Mock()
        chat.id = -1001234567890

        message = Mock()
        message.chat = chat
        message.from_user = user
        message.text = "a" * 5000  # Длинное сообщение
        message.photo = None
        message.video = None
        message.document = None

        result = await validation_middleware._validate_message(message)

        assert "Сообщение слишком длинное" in result

    @pytest.mark.asyncio
    async def test_validate_message_suspicious_content(self, validation_middleware):
        """Тест валидации подозрительного содержимого"""
        from unittest.mock import Mock

        # Создаем мок-объекты с подозрительным содержимым
        user = Mock()
        user.id = 123456789
        user.is_bot = False

        chat = Mock()
        chat.id = -1001234567890

        message = Mock()
        message.chat = chat
        message.from_user = user
        message.text = "<script>alert('xss')</script>"  # Подозрительное содержимое
        message.photo = None
        message.video = None
        message.document = None

        result = await validation_middleware._validate_message(message)

        assert "Подозрительное содержимое сообщения" in result

    @pytest.mark.asyncio
    async def test_validate_callback_query_success(self, validation_middleware, mock_callback_query):
        """Тест успешной валидации callback query"""
        result = await validation_middleware._validate_callback_query(mock_callback_query)

        assert len(result) == 0  # Пустой список ошибок

    @pytest.mark.asyncio
    async def test_validate_callback_query_missing_data(self, validation_middleware):
        """Тест валидации callback query без данных"""
        from unittest.mock import Mock

        # Создаем мок-объекты
        user = Mock()
        user.id = 123456789
        user.is_bot = False

        callback_query = Mock()
        callback_query.data = None  # Отсутствуют данные

        result = await validation_middleware._validate_callback_query(callback_query)

        assert "Отсутствуют данные callback query" in result

    @pytest.mark.asyncio
    async def test_validate_callback_query_too_long(self, validation_middleware):
        """Тест валидации слишком длинных данных callback query"""
        from unittest.mock import Mock

        # Создаем мок-объекты с длинными данными
        callback_query = Mock()
        callback_query.data = "a" * 100  # Данные длиннее 64 символов

        result = await validation_middleware._validate_callback_query(callback_query)

        assert "Callback data слишком длинные" in result

    @pytest.mark.asyncio
    async def test_validate_callback_query_suspicious_data(self, validation_middleware):
        """Тест валидации подозрительных данных callback query"""
        from unittest.mock import Mock

        # Создаем мок-объекты с подозрительными данными
        callback_query = Mock()
        callback_query.data = "<script>alert('xss')</script>"  # Подозрительные данные

        result = await validation_middleware._validate_callback_query(callback_query)

        assert "Подозрительные данные callback query" in result

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
            mime_type="application/pdf",
        )

        message = Message(message_id=1, date=1234567890, chat=chat, from_user=user, document=large_document)

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
            mime_type="video/mp4",
        )

        message = Message(message_id=1, date=1234567890, chat=chat, from_user=user, video=large_video)

        assert not validation_middleware._is_safe_media(message)

    def test_is_safe_media_safe_content(self, validation_middleware):
        """Тест что безопасный контент проходит проверку"""
        from unittest.mock import Mock

        # Обычное текстовое сообщение
        message = Mock()
        message.document = None
        message.video = None
        message.photo = None
        assert validation_middleware._is_safe_media(message)

        # Сообщение с небольшим документом
        message_with_doc = Mock()
        message_with_doc.document = Mock()
        message_with_doc.document.file_size = 1024  # 1KB
        message_with_doc.video = None
        message_with_doc.photo = None
        assert validation_middleware._is_safe_media(message_with_doc)


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

        message = Message(message_id=1, date=1234567890, chat=chat, from_user=user, text="/help admin")
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

        message = Message(message_id=1, date=1234567890, chat=chat, from_user=user, text=None)  # Отсутствует текст

        result = await command_middleware._validate_command(message)

        assert result["is_valid"] is False
        assert "Отсутствует текст команды" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_command_too_long(self, command_middleware):
        """Тест валидации слишком длинной команды"""
        from unittest.mock import Mock

        # Создаем мок-объекты с длинной командой
        message = Mock()
        message.text = "/" + "a" * 35  # Команда длиннее 32 символов

        result = await command_middleware._validate_command(message)

        assert not result["is_valid"]
        assert "Команда слишком длинная" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_command_suspicious_parameter(self, command_middleware):
        """Тест валидации команды с подозрительным параметром"""
        from unittest.mock import Mock

        # Создаем мок-объекты с подозрительным параметром
        message = Mock()
        message.text = "/help <script>alert('xss')</script>"  # Команда с JavaScript в параметре

        result = await command_middleware._validate_command(message)

        assert not result["is_valid"]
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
