"""Security tests for vulnerability detection."""

import pytest
from app.utils.security import sanitize_for_logging, sanitize_user_input
from app.auth.authorization import AuthorizationService
from app.models.secure_models import SecureUser, SecureMessage


class TestSecurityUtils:
    """Test security utilities."""
    
    def test_sanitize_for_logging(self):
        """Test log sanitization."""
        # Test XSS prevention
        malicious_input = '<script>alert("xss")</script>'
        sanitized = sanitize_for_logging(malicious_input)
        assert '<script>' not in sanitized
        assert '&lt;script&gt;' in sanitized
        
        # Test newline removal
        input_with_newlines = 'test\n\r\x00'
        sanitized = sanitize_for_logging(input_with_newlines)
        assert '\n' in sanitized
        assert '\r' in sanitized
        assert '\x00' not in sanitized
    
    def test_sanitize_user_input(self):
        """Test user input sanitization."""
        malicious_input = '<script>alert("xss")</script>'
        sanitized = sanitize_user_input(malicious_input)
        assert '<script>' not in sanitized
        assert '&lt;script&gt;' in sanitized
    
    def test_validate_user_id(self):
        """Test user ID validation."""
        from app.utils.security import validate_user_id
        
        assert validate_user_id(123456789) is True
        assert validate_user_id(0) is False
        assert validate_user_id(-1) is False
        assert validate_user_id("invalid") is False
        assert validate_user_id(None) is False


class TestAuthorization:
    """Test authorization system."""
    
    def test_authorization_service(self):
        """Test authorization service."""
        auth_service = AuthorizationService()
        
        # Test with valid admin ID (assuming 123456789 is admin)
        assert auth_service.is_admin(123456789) is True
        assert auth_service.is_super_admin(123456789) is True
        
        # Test with invalid user ID
        assert auth_service.is_admin(999999999) is False
        assert auth_service.is_super_admin(999999999) is False


class TestSecureModels:
    """Test secure models."""
    
    def test_secure_user_model(self):
        """Test secure user model."""
        # Valid user
        user = SecureUser(
            id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        assert user.id == 123456789
        assert user.username == "testuser"
        
        # Invalid user ID
        with pytest.raises(ValueError):
            SecureUser(id=0, username="testuser")
        
        # Invalid username
        with pytest.raises(ValueError):
            SecureUser(id=123456789, username="ab")  # Too short
    
    def test_secure_message_model(self):
        """Test secure message model."""
        # Valid message
        message = SecureMessage(
            message_id=1,
            text="Hello world",
            chat_id=123456789,
            date=1234567890
        )
        assert message.text == "Hello world"
        
        # XSS in text should be sanitized
        malicious_message = SecureMessage(
            message_id=1,
            text='<script>alert("xss")</script>',
            chat_id=123456789,
            date=1234567890
        )
        assert '<script>' not in malicious_message.text
        assert '&lt;script&gt;' in malicious_message.text


if __name__ == '__main__':
    pytest.main([__file__])
