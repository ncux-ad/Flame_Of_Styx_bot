"""
Тесты безопасности для AntiSpam Bot
"""

import pytest
from unittest.mock import Mock, patch
from app.constants import PATTERNS, SENSITIVE_PATTERNS, ErrorCodes
from app.config import Settings


class TestSecurityValidation:
    """Тесты валидации безопасности"""
    
    def test_bot_token_validation(self):
        """Тест валидации токена бота"""
        # Валидные токены
        valid_tokens = [
            "123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789",
            "987654321:ZYXwvuTSRqpoNMLkjihGFEdcba987654321",
        ]
        
        for token in valid_tokens:
            assert PATTERNS["BOT_TOKEN"].match(token), f"Токен должен быть валидным: {token}"
    
    def test_bot_token_invalidation(self):
        """Тест невалидных токенов бота"""
        invalid_tokens = [
            "123456789",  # Без двоеточия
            "123:short",   # Слишком короткий
            "short:ABCdefGHIjklMNOpqrsTUVwxyz123456789",  # Слишком короткий ID
            "123456789:invalid_chars!@#",  # Недопустимые символы
            "",  # Пустой
            None,  # None
        ]
        
        for token in invalid_tokens:
            if token is not None:
                assert not PATTERNS["BOT_TOKEN"].match(token), f"Токен должен быть невалидным: {token}"
    
    def test_admin_id_validation(self):
        """Тест валидации ID администратора"""
        # Валидные ID
        valid_ids = ["123456789", "987654321", "1", "999999999999"]
        
        for admin_id in valid_ids:
            assert PATTERNS["ADMIN_ID"].match(admin_id), f"ID должен быть валидным: {admin_id}"
    
    def test_admin_id_invalidation(self):
        """Тест невалидных ID администратора"""
        invalid_ids = ["abc", "123abc", "12.34", "-123", ""]
        
        for admin_id in invalid_ids:
            assert not PATTERNS["ADMIN_ID"].match(admin_id), f"ID должен быть невалидным: {admin_id}"
    
    def test_channel_username_validation(self):
        """Тест валидации username канала"""
        # Валидные username
        valid_usernames = ["@channel", "@test123", "@my_channel", "@a" + "b" * 31]
        
        for username in valid_usernames:
            assert PATTERNS["CHANNEL_USERNAME"].match(username), f"Username должен быть валидным: {username}"
    
    def test_channel_username_invalidation(self):
        """Тест невалидных username каналов"""
        invalid_usernames = [
            "channel",  # Без @
            "@",  # Только @
            "@ab",  # Слишком короткий
            "@" + "a" * 33,  # Слишком длинный
            "@invalid!",  # Недопустимые символы
        ]
        
        for username in invalid_usernames:
            assert not PATTERNS["CHANNEL_USERNAME"].match(username), f"Username должен быть невалидным: {username}"


class TestSensitiveDataFiltering:
    """Тесты фильтрации чувствительных данных"""
    
    def test_sensitive_patterns_detection(self):
        """Тест обнаружения чувствительных данных"""
        sensitive_messages = [
            "token=abc123def456",
            "password: mysecretpass",
            "secret=very_secret_value",
            "key: my_api_key_here",
        ]
        
        for message in sensitive_messages:
            detected = any(pattern.search(message) for pattern in SENSITIVE_PATTERNS)
            assert detected, f"Чувствительные данные должны быть обнаружены: {message}"
    
    def test_safe_messages_pass(self):
        """Тест что безопасные сообщения проходят фильтр"""
        safe_messages = [
            "Hello world",
            "User performed action",
            "Channel added successfully",
            "Settings updated",
        ]
        
        for message in safe_messages:
            detected = any(pattern.search(message) for pattern in SENSITIVE_PATTERNS)
            assert not detected, f"Безопасные сообщения не должны блокироваться: {message}"


class TestErrorCodes:
    """Тесты кодов ошибок"""
    
    def test_error_codes_are_unique(self):
        """Тест что коды ошибок уникальны"""
        error_codes = [
            ErrorCodes.SUCCESS,
            ErrorCodes.UNKNOWN_ERROR,
            ErrorCodes.INVALID_REQUEST,
            ErrorCodes.UNAUTHORIZED,
            ErrorCodes.FORBIDDEN,
            ErrorCodes.NOT_FOUND,
            ErrorCodes.INVALID_TOKEN,
            ErrorCodes.INVALID_ADMIN_ID,
            ErrorCodes.INVALID_CHANNEL,
            ErrorCodes.INVALID_MESSAGE,
            ErrorCodes.RATE_LIMIT_EXCEEDED,
            ErrorCodes.TOO_MANY_REQUESTS,
            ErrorCodes.DB_CONNECTION_ERROR,
            ErrorCodes.DB_QUERY_ERROR,
            ErrorCodes.DB_TRANSACTION_ERROR,
        ]
        
        assert len(error_codes) == len(set(error_codes)), "Коды ошибок должны быть уникальными"
    
    def test_error_codes_are_positive(self):
        """Тест что коды ошибок положительные"""
        error_codes = [
            ErrorCodes.SUCCESS,
            ErrorCodes.UNKNOWN_ERROR,
            ErrorCodes.INVALID_REQUEST,
            ErrorCodes.UNAUTHORIZED,
            ErrorCodes.FORBIDDEN,
            ErrorCodes.NOT_FOUND,
        ]
        
        for code in error_codes:
            assert code >= 0, f"Код ошибки должен быть положительным: {code}"


class TestSettingsValidation:
    """Тесты валидации настроек"""
    
    def test_settings_with_valid_data(self):
        """Тест настроек с валидными данными"""
        settings = Settings(
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789",
            admin_ids="123456789,987654321",
            db_path="test.db",
            log_level="INFO",
            environment="test",
            debug=True,
            rate_limit=5,
            rate_interval=60,
            rate_limit_message="Test message",
        )
        
        assert settings.bot_token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789"
        assert len(settings.admin_ids_list) == 2
        assert 123456789 in settings.admin_ids_list
        assert 987654321 in settings.admin_ids_list
    
    def test_settings_with_invalid_token(self):
        """Тест настроек с невалидным токеном"""
        with pytest.raises(ValueError, match="BOT_TOKEN некорректный"):
            Settings(
                bot_token="invalid_token",
                admin_ids="123456789",
                db_path="test.db",
            )
    
    def test_settings_with_empty_admin_ids(self):
        """Тест настроек с пустыми ID администраторов"""
        with pytest.raises(ValueError, match="ADMIN_IDS не может быть пустым"):
            Settings(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789",
                admin_ids="",
                db_path="test.db",
            )
    
    def test_settings_with_invalid_admin_ids(self):
        """Тест настроек с невалидными ID администраторов"""
        with pytest.raises(ValueError, match="ADMIN_IDS должен содержать только числа"):
            Settings(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789",
                admin_ids="123abc,456def",
                db_path="test.db",
            )


class TestInputSanitization:
    """Тесты санитизации входных данных"""
    
    def test_sanitize_log_message(self):
        """Тест санитизации сообщений для логов"""
        from app.utils.security import sanitize_for_logging
        
        # Сообщения с чувствительными данными
        sensitive_messages = [
            "User 123 used token abc123def456",
            "Password is mysecretpass",
            "Secret key: very_secret_value",
        ]
        
        for message in sensitive_messages:
            sanitized = sanitize_for_logging(message)
            # Проверяем что чувствительные данные удалены
            assert "token" not in sanitized.lower()
            assert "password" not in sanitized.lower()
            assert "secret" not in sanitized.lower()
    
    def test_sanitize_user_input(self):
        """Тест санитизации пользовательского ввода"""
        from app.utils.security import sanitize_user_input
        
        # Потенциально опасный ввод
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../etc/passwd",
            "eval('malicious_code')",
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = sanitize_user_input(dangerous_input)
            # Проверяем что опасные конструкции удалены
            assert "<script>" not in sanitized
            assert "DROP TABLE" not in sanitized
            assert "../" not in sanitized
            assert "eval(" not in sanitized


if __name__ == "__main__":
    pytest.main([__file__])