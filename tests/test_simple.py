"""
Simple unit tests for basic functionality.
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
        admin_ids_list=[123456789],
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
        result = validator.validate_command("/help")
        assert result["valid"] is True
        assert result["reason"] == "OK"

        # Test valid command with arguments
        result = validator.validate_command("/suspicious_analyze 123456789")
        assert result["valid"] is True
        assert result["reason"] == "OK"

    def test_validate_command_invalid_characters(self, mock_config):
        """Test command validation with invalid characters."""
        validator = InputValidator()

        # Test command with suspicious characters
        result = validator.validate_command("/help<script>alert('xss')</script>")
        assert result["valid"] is False
        assert "suspicious" in result["reason"].lower()

    def test_validate_command_too_long(self, mock_config):
        """Test command validation with too long input."""
        validator = InputValidator()

        # Test very long command
        long_command = "/help " + "a" * 1000
        result = validator.validate_command(long_command)
        assert result["valid"] is False
        assert "too long" in result["reason"].lower()

    def test_validate_command_empty(self, mock_config):
        """Test command validation with empty input."""
        validator = InputValidator()

        # Test empty command
        result = validator.validate_command("")
        assert result["valid"] is False
        assert "empty" in result["reason"].lower()

    def test_validate_interactive_input_basic(self, mock_config):
        """Test basic interactive input validation."""
        validator = InputValidator()

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
        validator = InputValidator()

        # Test empty input
        result = validator.validate_interactive_input("")
        assert result["valid"] is False
        assert "empty" in result["reason"].lower()

        # Test too long input
        long_input = "a" * 1000
        result = validator.validate_interactive_input(long_input)
        assert result["valid"] is False
        assert "too long" in result["reason"].lower()


class TestConfig:
    """Test configuration functionality."""

    def test_config_creation(self, mock_config):
        """Test configuration creation."""
        assert mock_config.bot_token == "123456789:test_token_123456789"
        assert len(mock_config.admin_ids_list) > 0  # Check that admin IDs exist
        assert mock_config.db_path == "test.db"
        assert mock_config.max_messages_per_minute == 10
        assert mock_config.max_links_per_message == 3
        assert mock_config.ban_duration_hours == 24
        assert mock_config.suspicion_threshold == 0.5
        assert mock_config.allow_photos_without_caption is True
        assert mock_config.allow_videos_without_caption is True
        assert mock_config.redis_enabled is False

    def test_config_validation(self, mock_config):
        """Test configuration validation."""
        # Test that config is valid
        assert mock_config.bot_token is not None
        assert len(mock_config.admin_ids_list) > 0
        assert mock_config.db_path.endswith((".db", ".sqlite3"))
        assert mock_config.max_messages_per_minute > 0
        assert mock_config.max_links_per_message > 0
        assert mock_config.ban_duration_hours > 0
        assert 0 <= mock_config.suspicion_threshold <= 1


class TestBasicFunctionality:
    """Test basic functionality without complex dependencies."""

    def test_string_validation(self):
        """Test basic string validation."""
        # Test empty string
        assert not bool("")
        assert bool("hello")

        # Test length validation
        short_string = "a" * 5
        long_string = "a" * 1000

        assert len(short_string) < 100
        assert len(long_string) > 100

    def test_regex_patterns(self):
        """Test regex patterns for validation."""
        import re

        # Test username pattern
        username_pattern = r"^@?[a-zA-Z0-9_]{5,32}$"
        assert re.match(username_pattern, "@testuser")
        assert re.match(username_pattern, "testuser")
        assert not re.match(username_pattern, "@")
        assert not re.match(username_pattern, "a" * 50)

        # Test user ID pattern
        user_id_pattern = r"^\d{8,12}$"
        assert re.match(user_id_pattern, "123456789")
        assert re.match(user_id_pattern, "1234567890")
        assert not re.match(user_id_pattern, "123")
        assert not re.match(user_id_pattern, "abc")

    def test_emoji_detection(self):
        """Test emoji detection logic."""
        import re

        # Test emoji pattern
        emoji_pattern = r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]"

        # Test normal text
        normal_text = "Hello, how are you?"
        emoji_count = len(re.findall(emoji_pattern, normal_text))
        assert emoji_count == 0

        # Test text with few emojis
        text_with_emojis = "Hello! 😊 How are you? 👍"
        emoji_count = len(re.findall(emoji_pattern, text_with_emojis))
        assert emoji_count == 2

        # Test emoji spam
        emoji_spam = "😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🤗🤔🤭🤫🤥😶😐😑😬🙄😯😦😧😮😲🥱😴🤤😪😵🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😈👿👹👺🤡💩👻💀☠️👽👾🤖🎃😺😸😹😻😼😽🙀😿😾"
        emoji_count = len(re.findall(emoji_pattern, emoji_spam))
        assert emoji_count > 50  # Should detect emoji spam

    def test_caps_detection(self):
        """Test caps lock detection logic."""

        def count_caps(text):
            """Count uppercase letters in text."""
            return sum(1 for c in text if c.isupper())

        def caps_ratio(text):
            """Calculate ratio of uppercase letters."""
            if not text:
                return 0
            return count_caps(text) / len(text)

        # Test normal text
        normal_text = "Hello, how are you?"
        assert caps_ratio(normal_text) < 0.5

        # Test caps text
        caps_text = "HELLO EVERYONE! THIS IS A TEST MESSAGE!"
        assert caps_ratio(caps_text) > 0.5

        # Test mixed text
        mixed_text = "Hello! This is a TEST message."
        assert caps_ratio(mixed_text) < 0.5

    def test_link_detection(self):
        """Test link detection logic."""
        import re

        # Test URL pattern
        url_pattern = r"https?://[^\s]+"

        # Test text without links
        no_links = "Hello, how are you?"
        links = re.findall(url_pattern, no_links)
        assert len(links) == 0

        # Test text with links
        with_links = "Check this: https://example.com and this: https://t.me/bot"
        links = re.findall(url_pattern, with_links)
        assert len(links) == 2
        assert "https://example.com" in links
        assert "https://t.me/bot" in links

        # Test t.me/bot detection
        def is_telegram_bot_link(url):
            """Check if URL is a Telegram bot link."""
            return "t.me/" in url and "bot" in url

        assert is_telegram_bot_link("https://t.me/testbot")
        assert is_telegram_bot_link("https://t.me/testbot?start=123")
        assert not is_telegram_bot_link("https://t.me/testchannel")
        assert not is_telegram_bot_link("https://example.com")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
