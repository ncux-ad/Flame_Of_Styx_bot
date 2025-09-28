"""
Unit tests for existing services.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.profiles import ProfileService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.config import Settings


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


@pytest.fixture
def mock_user():
    """Mock user for tests."""
    user = Mock()
    user.id = 123456789
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.is_bot = False
    return user


@pytest.fixture
def mock_message(mock_user):
    """Mock message for tests."""
    message = Mock()
    message.from_user = mock_user
    message.chat = Mock()
    message.chat.id = -1001234567890
    message.text = "Test message"
    message.entities = []
    message.caption = None
    return message


class TestProfileService:
    """Test profile analysis service."""

    @pytest.mark.asyncio
    async def test_analyze_profile_normal(self, mock_config, mock_user):
        """Test analysis of normal profile."""
        service = ProfileService(mock_config)
        
        result = await service.analyze_profile(mock_user)
        assert result["suspicious"] is False
        assert result["score"] < 0.5
        assert len(result["patterns"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_profile_suspicious(self, mock_config):
        """Test analysis of suspicious profile."""
        service = ProfileService(mock_config)
        
        # Create suspicious user
        suspicious_user = Mock()
        suspicious_user.id = 123456789
        suspicious_user.first_name = "Assistant"
        suspicious_user.last_name = "Bot"
        suspicious_user.username = "assistant_bot"
        suspicious_user.is_bot = False
        
        result = await service.analyze_profile(suspicious_user)
        assert result["suspicious"] is True
        assert result["score"] >= 0.5
        assert "bot_like_username" in result["patterns"]

    @pytest.mark.asyncio
    async def test_analyze_profile_incomplete(self, mock_config):
        """Test analysis of incomplete profile."""
        service = ProfileService(mock_config)
        
        # Create incomplete user
        incomplete_user = Mock()
        incomplete_user.id = 123456789
        incomplete_user.first_name = "A"
        incomplete_user.last_name = None
        incomplete_user.username = None
        incomplete_user.is_bot = False
        
        result = await service.analyze_profile(incomplete_user)
        assert result["suspicious"] is True
        assert result["score"] >= 0.5
        assert "short_first_name" in result["patterns"]
        assert "no_username" in result["patterns"]
        assert "no_last_name" in result["patterns"]


class TestLinkService:
    """Test link service functionality."""

    @pytest.mark.asyncio
    async def test_extract_links(self, mock_config, mock_message):
        """Test link extraction from message."""
        service = LinkService(mock_config)
        
        # Mock message with links
        mock_message.text = "Check these links: https://t.me/bot and https://example.com"
        mock_message.entities = [
            Mock(type="url", offset=20, length=16),
            Mock(type="url", offset=41, length=19)
        ]
        
        links = await service.extract_links(mock_message)
        assert len(links) == 2
        assert "https://t.me/bot" in links
        assert "https://example.com" in links

    @pytest.mark.asyncio
    async def test_is_telegram_bot_link(self, mock_config):
        """Test Telegram bot link detection."""
        service = LinkService(mock_config)
        
        # Test t.me/bot link
        assert await service.is_telegram_bot_link("https://t.me/testbot") is True
        assert await service.is_telegram_bot_link("https://t.me/testbot?start=123") is True
        
        # Test regular t.me link
        assert await service.is_telegram_bot_link("https://t.me/testchannel") is False
        assert await service.is_telegram_bot_link("https://t.me/testgroup") is False
        
        # Test non-telegram links
        assert await service.is_telegram_bot_link("https://example.com") is False
        assert await service.is_telegram_bot_link("https://google.com") is False

    @pytest.mark.asyncio
    async def test_count_links(self, mock_config, mock_message):
        """Test link counting."""
        service = LinkService(mock_config)
        
        # Mock message with links
        mock_message.text = "Link1: https://t.me/bot1 Link2: https://t.me/bot2 Link3: https://example.com"
        mock_message.entities = [
            Mock(type="url", offset=7, length=17),
            Mock(type="url", offset=30, length=17),
            Mock(type="url", offset=53, length=19)
        ]
        
        count = await service.count_links(mock_message)
        assert count == 3

    @pytest.mark.asyncio
    async def test_check_links(self, mock_config, mock_message):
        """Test link checking with limits."""
        service = LinkService(mock_config)
        
        # Test within limits
        mock_message.text = "Check this: https://example.com"
        mock_message.entities = [Mock(type="url", offset=12, length=19)]
        
        result = await service.check_links(mock_message)
        assert result["allowed"] is True
        assert result["link_count"] == 1
        
        # Test exceeding limits
        mock_message.text = "Link1: https://t.me/bot1 Link2: https://t.me/bot2 Link3: https://t.me/bot3 Link4: https://t.me/bot4"
        mock_message.entities = [
            Mock(type="url", offset=6, length=17),
            Mock(type="url", offset=29, length=17),
            Mock(type="url", offset=52, length=17),
            Mock(type="url", offset=75, length=17)
        ]
        
        result = await service.check_links(mock_message)
        assert result["allowed"] is False
        assert result["link_count"] == 4
        assert "too many links" in result["reason"].lower()


class TestModerationService:
    """Test moderation service functionality."""

    @pytest.mark.asyncio
    async def test_ban_user(self, mock_config, mock_user):
        """Test user banning."""
        service = ModerationService(mock_config)
        
        # Mock database operations
        with patch('app.services.moderation.get_database') as mock_db:
            mock_db.return_value = Mock()
            
            result = await service.ban_user(mock_user.id, 24, "Test ban")
            assert result["success"] is True
            assert "banned" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unban_user(self, mock_config, mock_user):
        """Test user unbanning."""
        service = ModerationService(mock_config)
        
        # Mock database operations
        with patch('app.services.moderation.get_database') as mock_db:
            mock_db.return_value = Mock()
            
            result = await service.unban_user(mock_user.id)
            assert result["success"] is True
            assert "unbanned" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_mute_user(self, mock_config, mock_user):
        """Test user muting."""
        service = ModerationService(mock_config)
        
        # Mock database operations
        with patch('app.services.moderation.get_database') as mock_db:
            mock_db.return_value = Mock()
            
            result = await service.mute_user(mock_user.id, 60, "Test mute")
            assert result["success"] is True
            assert "muted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unmute_user(self, mock_config, mock_user):
        """Test user unmuting."""
        service = ModerationService(mock_config)
        
        # Mock database operations
        with patch('app.services.moderation.get_database') as mock_db:
            mock_db.return_value = Mock()
            
            result = await service.unmute_user(mock_user.id)
            assert result["success"] is True
            assert "unmuted" in result["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
