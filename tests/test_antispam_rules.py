"""
Unit tests for anti-spam rules and detection logic.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from aiogram.types import Chat, Message, MessageEntity, User

from app.config import Settings
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return Settings(
        bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop",  # Валидный формат токена
        admin_ids="123456789",
        db_path="test.sqlite3",  # Валидный путь к БД
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
    user = Mock(spec=User)
    user.id = 123456789
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.is_bot = False
    return user


@pytest.fixture
def mock_chat():
    """Mock chat for tests."""
    chat = Mock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "supergroup"
    chat.title = "Test Group"
    return chat


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Mock message for tests."""
    message = Mock(spec=Message)
    message.message_id = 1
    message.from_user = mock_user
    message.chat = mock_chat
    message.date = datetime.now()
    message.text = "Test message"
    message.entities = []
    message.caption = None
    message.photo = None
    message.video = None
    message.document = None
    message.animation = None
    message.sticker = None
    message.voice = None
    message.video_note = None
    message.contact = None
    message.location = None
    message.venue = None
    message.poll = None
    message.dice = None
    message.new_chat_members = []
    message.left_chat_member = None
    message.group_chat_created = False
    message.supergroup_chat_created = False
    message.channel_chat_created = False
    message.migrate_to_chat_id = None
    message.migrate_from_chat_id = None
    message.pinned_message = None
    message.invoice = None
    message.successful_payment = None
    message.connected_website = None
    message.passport_data = None
    message.proximity_alert_triggered = None
    message.video_chat_scheduled = None
    message.video_chat_started = None
    message.video_chat_ended = None
    message.video_chat_participants_invited = None
    message.web_app_data = None
    message.reply_to_message = None
    message.forward_from = None
    message.forward_from_chat = None
    message.forward_from_message_id = None
    message.forward_signature = None
    message.forward_sender_name = None
    message.forward_date = None
    message.is_automatic_forward = False
    message.reply_markup = None
    message.edit_date = None
    message.has_protected_content = False
    message.media_group_id = None
    message.author_signature = None
    message.text_entities = []
    message.caption_entities = []
    message.has_media_spoiler = False
    return message


class TestAntiSpamRules:
    """Test anti-spam rules and detection logic."""

    @pytest.mark.asyncio
    async def test_message_rate_limiting(self, mock_config, mock_message):
        """Test message rate limiting."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test normal message rate
        for i in range(5):
            result = await service.check_message_rate(mock_message)
            assert result["allowed"] is True
            assert result["reason"] == "OK"

        # Test rate limit exceeded
        for i in range(10):
            result = await service.check_message_rate(mock_message)
            if i < 10:
                assert result["allowed"] is True
            else:
                assert result["allowed"] is False
                assert "rate limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_link_detection(self, mock_config, mock_message):
        """Test link detection and counting."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test message with links
        mock_message.text = "Check this link: https://t.me/bot and this one: https://example.com"
        result = await service.check_links(mock_message)
        assert result["allowed"] is True
        assert result["link_count"] == 2

        # Test too many links
        mock_message.text = (
            "Link1: https://t.me/bot1 Link2: https://t.me/bot2 Link3: https://t.me/bot3 Link4: https://t.me/bot4"
        )
        result = await service.check_links(mock_message)
        assert result["allowed"] is False
        assert result["link_count"] == 4
        assert "too many links" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_telegram_bot_links(self, mock_config, mock_message):
        """Test detection of t.me/bot links."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test t.me/bot link
        mock_message.text = "Check this bot: https://t.me/testbot"
        result = await service.check_links(mock_message)
        assert result["allowed"] is False
        assert "t.me/bot" in result["reason"].lower()

        # Test regular t.me link (should be allowed)
        mock_message.text = "Check this channel: https://t.me/testchannel"
        result = await service.check_links(mock_message)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_media_without_caption(self, mock_config, mock_message):
        """Test media messages without captions."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test photo without caption (should be allowed)
        mock_message.text = None
        mock_message.caption = None
        mock_message.photo = [Mock()]
        result = await service.check_media_caption(mock_message)
        assert result["allowed"] is True

        # Test video without caption (should be allowed)
        mock_message.photo = None
        mock_message.video = Mock()
        result = await service.check_media_caption(mock_message)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_suspicious_profile_detection(self, mock_config, mock_user):
        """Test suspicious profile detection."""
        service = ProfileService(mock_config)

        # Test normal profile
        result = await service.analyze_profile(mock_user)
        assert result["suspicious"] is False
        assert result["score"] < 0.5

        # Test suspicious profile (bot-like username)
        mock_user.username = "testbot123"
        mock_user.first_name = "Test"
        mock_user.last_name = None
        result = await service.analyze_profile(mock_user)
        assert result["suspicious"] is True
        assert result["score"] >= 0.5

    @pytest.mark.asyncio
    async def test_duplicate_message_detection(self, mock_config, mock_message):
        """Test duplicate message detection."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test first message
        result = await service.check_duplicate_message(mock_message)
        assert result["allowed"] is True

        # Test duplicate message
        result = await service.check_duplicate_message(mock_message)
        assert result["allowed"] is False
        assert "duplicate" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_spam_keywords_detection(self, mock_config, mock_message):
        """Test spam keywords detection."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test normal message
        mock_message.text = "Hello, how are you?"
        result = await service.check_spam_keywords(mock_message)
        assert result["allowed"] is True

        # Test message with spam keywords
        mock_message.text = "FREE MONEY! CLICK HERE NOW! URGENT!"
        result = await service.check_spam_keywords(mock_message)
        assert result["allowed"] is False
        assert "spam keywords" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_caps_lock_detection(self, mock_config, mock_message):
        """Test excessive caps detection."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test normal message
        mock_message.text = "Hello, how are you?"
        result = await service.check_caps_lock(mock_message)
        assert result["allowed"] is True

        # Test message with excessive caps
        mock_message.text = "HELLO EVERYONE! THIS IS A TEST MESSAGE!"
        result = await service.check_caps_lock(mock_message)
        assert result["allowed"] is False
        assert "caps lock" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_emoji_spam_detection(self, mock_config, mock_message):
        """Test emoji spam detection."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test normal message with few emojis
        mock_message.text = "Hello! 😊 How are you? 👍"
        result = await service.check_emoji_spam(mock_message)
        assert result["allowed"] is True

        # Test message with emoji spam (shortened for formatting)
        mock_message.text = "😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍"
        result = await service.check_emoji_spam(mock_message)
        assert result["allowed"] is False
        assert "emoji spam" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_combined_antispam_check(self, mock_config, mock_message):
        """Test combined anti-spam check."""
        from unittest.mock import Mock

        mock_bot = Mock()
        mock_db = Mock()
        service = ModerationService(mock_bot, mock_db)

        # Test normal message
        mock_message.text = "Hello, how are you?"
        result = await service.check_message(mock_message)
        assert result["allowed"] is True
        assert result["reason"] == "OK"

        # Test spam message (multiple violations)
        mock_message.text = "FREE MONEY! CLICK HERE NOW! https://t.me/bot URGENT! 😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🤗🤔🤭🤫🤥😶😐😑😬🙄😯😦😧😮😲🥱😴🤤😪😵🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😈👿👹👺🤡💩👻💀☠️👽👾🤖🎃😺😸😹😻😼😽🙀😿😾"
        result = await service.check_message(mock_message)
        assert result["allowed"] is False
        assert any(keyword in result["reason"].lower() for keyword in ["spam", "links", "emoji", "caps"])


class TestProfileAnalysis:
    """Test profile analysis and suspicious pattern detection."""

    @pytest.mark.asyncio
    async def test_normal_profile(self, mock_config):
        """Test analysis of normal profile."""
        service = ProfileService(mock_config)

        user = Mock(spec=User)
        user.id = 123456789
        user.first_name = "John"
        user.last_name = "Doe"
        user.username = "johndoe"
        user.is_bot = False

        result = await service.analyze_profile(user)
        assert result["suspicious"] is False
        assert result["score"] < 0.5
        assert len(result["patterns"]) == 0

    @pytest.mark.asyncio
    async def test_bot_like_profile(self, mock_config):
        """Test analysis of bot-like profile."""
        service = ProfileService(mock_config)

        user = Mock(spec=User)
        user.id = 123456789
        user.first_name = "Test"
        user.last_name = None
        user.username = "testbot123"
        user.is_bot = False

        result = await service.analyze_profile(user)
        assert result["suspicious"] is True
        assert result["score"] >= 0.5
        assert "bot_like_username" in result["patterns"]

    @pytest.mark.asyncio
    async def test_incomplete_profile(self, mock_config):
        """Test analysis of incomplete profile."""
        service = ProfileService(mock_config)

        user = Mock(spec=User)
        user.id = 123456789
        user.first_name = "A"
        user.last_name = None
        user.username = None
        user.is_bot = False

        result = await service.analyze_profile(user)
        assert result["suspicious"] is True
        assert result["score"] >= 0.5
        assert "short_first_name" in result["patterns"]
        assert "no_username" in result["patterns"]
        assert "no_last_name" in result["patterns"]

    @pytest.mark.asyncio
    async def test_suspicious_patterns(self, mock_config):
        """Test various suspicious patterns."""
        service = ProfileService(mock_config)

        # Test profile with suspicious patterns
        user = Mock(spec=User)
        user.id = 123456789
        user.first_name = "Assistant"
        user.last_name = "Bot"
        user.username = "assistant_bot"
        user.is_bot = False

        result = await service.analyze_profile(user)
        assert result["suspicious"] is True
        assert result["score"] >= 0.5
        assert "bot_like_username" in result["patterns"]


class TestLinkService:
    """Test link service functionality."""

    @pytest.mark.asyncio
    async def test_extract_links(self, mock_config):
        """Test link extraction from message."""
        service = LinkService(mock_config)

        message = Mock(spec=Message)
        message.text = "Check these links: https://t.me/bot and https://example.com"
        message.entities = [Mock(type="url", offset=20, length=16), Mock(type="url", offset=41, length=19)]

        links = await service.extract_links(message)
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
    async def test_count_links(self, mock_config):
        """Test link counting."""
        service = LinkService(mock_config)

        message = Mock(spec=Message)
        message.text = "Link1: https://t.me/bot1 Link2: https://t.me/bot2 Link3: https://example.com"
        message.entities = [
            Mock(type="url", offset=7, length=17),
            Mock(type="url", offset=30, length=17),
            Mock(type="url", offset=53, length=19),
        ]

        count = await service.count_links(message)
        assert count == 3

    @pytest.mark.asyncio
    async def test_check_links(self, mock_config):
        """Test link checking with limits."""
        service = LinkService(mock_config)

        # Test within limits
        message = Mock(spec=Message)
        message.text = "Check this: https://example.com"
        message.entities = [Mock(type="url", offset=12, length=19)]

        result = await service.check_links(message)
        assert result["allowed"] is True
        assert result["link_count"] == 1

        # Test exceeding limits
        message.text = "Link1: https://t.me/bot1 Link2: https://t.me/bot2 Link3: https://t.me/bot3 Link4: https://t.me/bot4"
        message.entities = [
            Mock(type="url", offset=6, length=17),
            Mock(type="url", offset=29, length=17),
            Mock(type="url", offset=52, length=17),
            Mock(type="url", offset=75, length=17),
        ]

        result = await service.check_links(message)
        assert result["allowed"] is False
        assert result["link_count"] == 4
        assert "too many links" in result["reason"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
