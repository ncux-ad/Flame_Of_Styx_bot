"""
Simple unit tests for input validation functionality.
"""

import pytest
from unittest.mock import Mock

from app.utils.validation import InputValidator
from app.config import Settings


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return Settings(
        bot_token="test_token_123456789",
        admin_ids_list=[123456789],
        db_path=":memory:",
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
        validator = InputValidator(mock_config)
        
        # Test valid command
        result = validator.validate_command("/help")
        assert result["valid"] is True
        assert result["reason"] == "OK"
        
        # Test valid command with arguments
        result = validator.validate_command("/suspicious_analyze 123456789")
        assert result["valid"] is True
        assert result["reason"] == "OK"

    def test_validate_command_invalid_characters(self, mock_config):
        """Test command validation with invalid characters."""
        validator = InputValidator(mock_config)
        
        # Test command with suspicious characters
        result = validator.validate_command("/help<script>alert('xss')</script>")
        assert result["valid"] is False
        assert "suspicious" in result["reason"].lower()

    def test_validate_command_too_long(self, mock_config):
        """Test command validation with too long input."""
        validator = InputValidator(mock_config)
        
        # Test very long command
        long_command = "/help " + "a" * 1000
        result = validator.validate_command(long_command)
        assert result["valid"] is False
        assert "too long" in result["reason"].lower()

    def test_validate_command_empty(self, mock_config):
        """Test command validation with empty input."""
        validator = InputValidator(mock_config)
        
        # Test empty command
        result = validator.validate_command("")
        assert result["valid"] is False
        assert "empty" in result["reason"].lower()

    def test_validate_interactive_input_basic(self, mock_config):
        """Test basic interactive input validation."""
        validator = InputValidator(mock_config)
        
        # Test valid interactive input
        result = validator.validate_interactive_input("123456789")
        assert result["valid"] is True
        assert result["reason"] == "OK"
        
        # Test valid username
        result = validator.validate_interactive_input("@testuser")
        assert result["valid"] is True
        assert result["reason"] == "OK"

    def test_validate_interactive_input_invalid(self, mock_config):
        """Test interactive input validation with invalid input."""
        validator = InputValidator(mock_config)
        
        # Test empty input
        result = validator.validate_interactive_input("")
        assert result["valid"] is False
        assert "empty" in result["reason"].lower()
        
        # Test too long input
        long_input = "a" * 1000
        result = validator.validate_interactive_input(long_input)
        assert result["valid"] is False
        assert "too long" in result["reason"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
