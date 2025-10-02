"""
Simple unit tests for input validation functionality.
"""

from unittest.mock import Mock

import pytest

from app.config import Settings
from app.utils.validation import InputValidator


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return Settings(
        bot_token="123456789:test_token_123456789",
        admin_ids="123456789",
        db_path="test.db",
        max_messages_per_minute=10,
        max_links_per_message=3,
        ban_duration_hours=24,
        suspicion_threshold=0.5,
        allow_photos_without_caption=True,
        allow_videos_without_caption=True,
        redis_enabled=False,
    )


class TestInputValidator:
    """Test input validation functionality."""

    def test_validate_command_basic(self, mock_config):
        """Test basic command validation."""
        validator = InputValidator()

        # Test valid command
        result = validator.validate_command("/help", [])
        assert len(result) == 0  # No errors

        # Test valid command with arguments
        result = validator.validate_command("/suspicious_analyze", ["123456789"])
        assert len(result) == 0  # No errors

    def test_validate_command_invalid_characters(self, mock_config):
        """Test command validation with invalid characters."""
        validator = InputValidator()

        # Test command with suspicious characters
        result = validator.validate_command("/help<script>alert('xss')</script>", [])
        assert len(result) > 0  # Should have errors

    def test_validate_command_too_long(self, mock_config):
        """Test command validation with too long input."""
        validator = InputValidator()

        # Test very long command
        long_command = "/" + "a" * 100
        result = validator.validate_command(long_command, [])
        assert len(result) > 0  # Should have errors

    def test_validate_command_empty(self, mock_config):
        """Test command validation with empty input."""
        validator = InputValidator()

        # Test empty command
        result = validator.validate_command("", [])
        assert len(result) > 0  # Should have errors

    def test_validate_phone_number_basic(self, mock_config):
        """Test basic phone number validation."""
        validator = InputValidator()

        # Test valid phone number
        result = validator.validate_phone_number("+1234567890")
        assert len(result) == 0  # No errors

        # Test invalid phone number
        result = validator.validate_phone_number("invalid")
        assert len(result) > 0  # Should have errors

    def test_validate_email_basic(self, mock_config):
        """Test basic email validation."""
        validator = InputValidator()

        # Test valid email
        result = validator.validate_email("test@example.com")
        assert len(result) == 0  # No errors

        # Test invalid email
        result = validator.validate_email("invalid-email")
        assert len(result) > 0  # Should have errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
