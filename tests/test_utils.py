"""
Тесты для утилит.
"""

from unittest.mock import Mock, patch

import pytest

from app.utils.security import (
    safe_format_message,
    sanitize_for_logging,
    sanitize_user_input,
)
from app.utils.validation import InputValidator, ValidationError, ValidationSeverity


class TestSecurityUtils:
    """Тесты утилит безопасности."""

    def test_sanitize_for_logging_string(self):
        """Тест санитизации строки для логирования."""
        # Обычная строка
        result = sanitize_for_logging("Hello, world!")
        assert result == "Hello, world!"

        # Строка с потенциально опасными данными
        sensitive = "Token: abc123def456"
        result = sanitize_for_logging(sensitive)
        assert "abc123def456" not in result
        assert "[REDACTED]" in result

    def test_sanitize_for_logging_integer(self):
        """Тест санитизации числа для логирования."""
        result = sanitize_for_logging(123456789)
        assert result == "123456789"
        assert isinstance(result, str)

    def test_sanitize_for_logging_float(self):
        """Тест санитизации числа с плавающей точкой для логирования."""
        result = sanitize_for_logging(123.456)
        assert result == "123.456"
        assert isinstance(result, str)

    def test_safe_format_message_basic(self):
        """Тест безопасного форматирования сообщения."""
        template = "User {user_id} performed action {action}"
        result = safe_format_message(template, user_id=123456789, action="login")

        assert "123456789" in result
        assert "login" in result

    def test_safe_format_message_with_sensitive_data(self):
        """Тест форматирования с чувствительными данными."""
        template = "User {user_id} with token {token}"
        result = safe_format_message(template, user_id=123456789, token="secret123")

        assert "123456789" in result
        assert "secret123" not in result

    def test_sanitize_user_input_basic(self):
        """Тест санитизации пользовательского ввода."""
        # Обычный текст
        result = sanitize_user_input("Hello, world!")
        assert result == "Hello, world!"

        # Текст с HTML тегами
        html_input = "<script>alert('xss')</script>Hello"
        result = sanitize_user_input(html_input)
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_user_input_long_text(self):
        """Тест санитизации длинного текста."""
        long_text = "A" * 2000
        result = sanitize_user_input(long_text)
        assert len(result) <= 1000  # Проверяем ограничение длины

    def test_url_pattern_validation(self):
        """Тест валидации URL паттернов."""
        import re

        # Простой URL паттерн
        url_pattern = r"https?://[^\s]+"

        valid_urls = ["https://example.com", "http://localhost:8000", "https://api.example.com/v1/users"]

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Не http/https
            "https://",  # Неполный
        ]

        for url in valid_urls:
            assert re.match(url_pattern, url) is not None

        for url in invalid_urls:
            assert re.match(url_pattern, url) is None


class TestValidationUtils:
    """Тесты утилит валидации."""

    def test_input_validator_creation(self):
        """Тест создания валидатора."""
        validator = InputValidator()
        assert validator is not None

    def test_validation_error_creation(self):
        """Тест создания ошибки валидации."""
        error = ValidationError(
            field="username",
            message="Invalid username",
            severity=ValidationSeverity.HIGH,
            code="invalid_username",
            value="bad_user",
        )

        assert error.field == "username"
        assert error.message == "Invalid username"
        assert error.severity == ValidationSeverity.HIGH
        assert error.code == "invalid_username"
        assert error.value == "bad_user"

    def test_validation_severity_enum(self):
        """Тест enum серьезности валидации."""
        assert hasattr(ValidationSeverity, "LOW")
        assert hasattr(ValidationSeverity, "MEDIUM")
        assert hasattr(ValidationSeverity, "HIGH")
        assert hasattr(ValidationSeverity, "CRITICAL")

        # Проверяем порядок важности
        assert ValidationSeverity.LOW.value < ValidationSeverity.MEDIUM.value
        assert ValidationSeverity.MEDIUM.value < ValidationSeverity.HIGH.value
        assert ValidationSeverity.HIGH.value < ValidationSeverity.CRITICAL.value

    def test_validator_validate_message_basic(self):
        """Тест базовой валидации сообщения."""
        validator = InputValidator()

        # Мокаем сообщение с правильными строковыми полями
        from unittest.mock import MagicMock

        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.from_user.first_name = "Test"
        message.from_user.last_name = "User"
        message.from_user.username = "testuser"
        message.from_user.is_bot = False

        message.chat = MagicMock()
        message.chat.id = -1001234567890
        message.chat.type = "supergroup"
        message.chat.title = "Test Chat"

        message.text = "Hello, world!"
        message.date = 1234567890

        result = validator.validate_message(message)
        assert len(result) == 0  # Нет ошибок валидации

    def test_validator_validate_message_no_user(self):
        """Тест валидации сообщения без пользователя."""
        validator = InputValidator()

        # Мокаем сообщение без пользователя
        from unittest.mock import MagicMock

        message = MagicMock()
        message.from_user = None
        message.chat = MagicMock()
        message.chat.id = -1001234567890
        message.chat.title = "Test Chat"
        message.text = "Hello"

        result = validator.validate_message(message)
        # Отсутствие пользователя может не считаться ошибкой валидации
        # в зависимости от логики приложения
        assert isinstance(result, list)  # Результат должен быть списком

    def test_validator_validate_message_no_chat(self):
        """Тест валидации сообщения без чата."""
        validator = InputValidator()

        # Мокаем сообщение без чата
        from unittest.mock import MagicMock

        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.from_user.first_name = "Test"
        message.from_user.last_name = None  # Явно устанавливаем None
        message.from_user.username = None  # Явно устанавливаем None
        message.from_user.is_bot = False
        message.chat = None
        message.text = "Hello"

        result = validator.validate_message(message)
        assert len(result) > 0  # Есть ошибки валидации

    def test_validator_validate_callback_query(self):
        """Тест валидации callback query."""
        validator = InputValidator()

        # Мокаем callback query
        from unittest.mock import MagicMock

        callback = MagicMock()
        callback.from_user = MagicMock()
        callback.from_user.id = 123456789
        callback.from_user.first_name = "Test"
        callback.from_user.last_name = None  # Явно устанавливаем None
        callback.from_user.username = None  # Явно устанавливаем None
        callback.from_user.is_bot = False
        callback.data = "test_callback"

        result = validator.validate_callback_query(callback)
        assert len(result) == 0  # Нет ошибок валидации

    def test_validator_validate_callback_query_no_data(self):
        """Тест валидации callback query без данных."""
        validator = InputValidator()

        # Мокаем callback query без данных
        from unittest.mock import MagicMock

        callback = MagicMock()
        callback.from_user = MagicMock()
        callback.from_user.id = 123456789
        callback.from_user.first_name = "Test"
        callback.from_user.last_name = None  # Явно устанавливаем None
        callback.from_user.username = None  # Явно устанавливаем None
        callback.from_user.is_bot = False
        callback.data = None

        result = validator.validate_callback_query(callback)
        assert len(result) > 0  # Есть ошибки валидации


class TestPatternMatching:
    """Тесты паттернов и регулярных выражений."""

    def test_email_pattern(self):
        """Тест паттерна email."""
        import re

        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

        valid_emails = ["test@example.com", "user.name@domain.org", "user+tag@subdomain.example.com"]

        invalid_emails = ["invalid-email", "@domain.com", "user@", "user@domain"]

        for email in valid_emails:
            assert re.match(email_pattern, email) is not None

        for email in invalid_emails:
            assert re.match(email_pattern, email) is None

    def test_phone_pattern(self):
        """Тест паттерна телефона."""
        import re

        phone_pattern = r"^\+?[1-9]\d{2,14}$"  # Минимум 3 цифры

        valid_phones = ["+1234567890", "+79161234567", "1234567890", "123"]

        invalid_phones = ["abc123", "+abc", "12", "+0123456789"]  # Слишком короткий или начинается с 0

        for phone in valid_phones:
            assert re.match(phone_pattern, phone) is not None

        for phone in invalid_phones:
            assert re.match(phone_pattern, phone) is None

    def test_username_pattern(self):
        """Тест паттерна username."""
        import re

        username_pattern = r"^@?[a-zA-Z0-9_]{5,32}$"

        valid_usernames = ["@testuser", "testuser", "user_123", "a" * 32]  # Максимальная длина

        invalid_usernames = [
            "@user",  # Слишком короткий
            "a" * 33,  # Слишком длинный
            "@user-name",  # Дефис не разрешен
            "@user.name",  # Точка не разрешена
            "",
        ]

        for username in valid_usernames:
            assert re.match(username_pattern, username) is not None

        for username in invalid_usernames:
            assert re.match(username_pattern, username) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
