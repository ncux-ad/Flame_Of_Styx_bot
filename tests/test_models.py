"""
Тесты для моделей данных.
"""

from datetime import datetime

import pytest

from app.models.bot import Bot
from app.models.channel import Channel
from app.models.moderation_log import ModerationAction, ModerationLog
from app.models.suspicious_profile import SuspiciousProfile
from app.models.user import User


class TestBotModel:
    """Тесты модели Bot."""

    def test_bot_creation(self):
        """Тест создания бота."""
        bot = Bot(username="testbot", first_name="Test Bot", is_whitelisted=True, added_by=123456789)

        assert bot.username == "testbot"
        assert bot.first_name == "Test Bot"
        assert bot.is_whitelisted is True
        assert bot.added_by == 123456789
        assert bot.last_name is None

    def test_bot_str_representation(self):
        """Тест строкового представления бота."""
        bot = Bot(username="testbot", first_name="Test Bot")

        str_repr = str(bot)
        assert "testbot" in str_repr or "Test Bot" in str_repr


class TestChannelModel:
    """Тесты модели Channel."""

    def test_channel_creation(self):
        """Тест создания канала."""
        channel = Channel(
            chat_id=-1001234567890, title="Test Channel", username="testchannel", is_native=True, is_comment_group=False
        )

        assert channel.chat_id == -1001234567890
        assert channel.title == "Test Channel"
        assert channel.username == "testchannel"
        assert channel.is_native is True
        assert channel.is_comment_group is False

    def test_channel_without_username(self):
        """Тест канала без username."""
        channel = Channel(chat_id=-1001234567890, title="Private Channel", is_native=False)

        assert channel.chat_id == -1001234567890
        assert channel.title == "Private Channel"
        assert channel.username is None
        assert channel.is_native is False

    def test_channel_str_representation(self):
        """Тест строкового представления канала."""
        channel = Channel(chat_id=-1001234567890, title="Test Channel")

        str_repr = str(channel)
        assert "Test Channel" in str_repr or str(channel.chat_id) in str_repr


class TestUserModel:
    """Тесты модели User."""

    def test_user_creation(self):
        """Тест создания пользователя."""
        user = User(user_id=123456789, first_name="Test", last_name="User", username="testuser", is_banned=False)

        assert user.user_id == 123456789
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.username == "testuser"
        assert user.is_banned is False

    def test_user_without_optional_fields(self):
        """Тест пользователя без опциональных полей."""
        user = User(user_id=123456789, first_name="Test")

        assert user.user_id == 123456789
        assert user.first_name == "Test"
        assert user.last_name is None
        assert user.username is None
        assert user.is_banned is False

    def test_banned_user(self):
        """Тест заблокированного пользователя."""
        user = User(user_id=123456789, first_name="Banned", is_banned=True, ban_reason="Spam")

        assert user.is_banned is True
        assert user.ban_reason == "Spam"


class TestModerationLogModel:
    """Тесты модели ModerationLog."""

    def test_moderation_log_creation(self):
        """Тест создания лога модерации."""
        log = ModerationLog(
            action=ModerationAction.BAN, user_id=123456789, admin_id=987654321, reason="Spam messages", chat_id=-1001234567890
        )

        assert log.action == ModerationAction.BAN
        assert log.user_id == 123456789
        assert log.admin_id == 987654321
        assert log.reason == "Spam messages"
        assert log.chat_id == -1001234567890

    def test_moderation_action_enum(self):
        """Тест enum действий модерации."""
        # Проверяем, что все действия доступны
        assert hasattr(ModerationAction, "BAN")
        assert hasattr(ModerationAction, "UNBAN")
        assert hasattr(ModerationAction, "WARN")

        # Проверяем значения
        ban_action = ModerationAction.BAN
        assert isinstance(ban_action, ModerationAction)

    def test_moderation_log_without_optional_fields(self):
        """Тест лога модерации без опциональных полей."""
        log = ModerationLog(action=ModerationAction.WARN, user_id=123456789, admin_id=987654321)

        assert log.action == ModerationAction.WARN
        assert log.user_id == 123456789
        assert log.admin_id == 987654321
        assert log.reason is None
        assert log.chat_id is None


class TestSuspiciousProfileModel:
    """Тесты модели SuspiciousProfile."""

    def test_suspicious_profile_creation(self):
        """Тест создания подозрительного профиля."""
        profile = SuspiciousProfile(
            user_id=123456789,
            first_name="Suspicious",
            last_name="User",
            username="sususer",
            suspicion_score=0.85,
            reasons="Short username, suspicious patterns",
        )

        assert profile.user_id == 123456789
        assert profile.first_name == "Suspicious"
        assert profile.last_name == "User"
        assert profile.username == "sususer"
        assert profile.suspicion_score == 0.85
        assert "suspicious patterns" in profile.reasons

    def test_high_suspicion_score(self):
        """Тест высокого балла подозрительности."""
        profile = SuspiciousProfile(user_id=123456789, first_name="Bot", suspicion_score=0.95, reasons="GPT-like responses")

        assert profile.suspicion_score == 0.95
        assert profile.suspicion_score > 0.8  # Высокий уровень подозрительности

    def test_suspicious_profile_without_optional_fields(self):
        """Тест подозрительного профиля без опциональных полей."""
        profile = SuspiciousProfile(user_id=123456789, suspicion_score=0.6)

        assert profile.user_id == 123456789
        assert profile.suspicion_score == 0.6
        assert profile.first_name is None
        assert profile.last_name is None
        assert profile.username is None


class TestModelRelationships:
    """Тесты взаимосвязей между моделями."""

    def test_user_moderation_relationship(self):
        """Тест связи между пользователем и логами модерации."""
        user_id = 123456789
        admin_id = 987654321

        # Создаем пользователя
        user = User(user_id=user_id, first_name="Test", is_banned=True)

        # Создаем лог модерации для этого пользователя
        log = ModerationLog(action=ModerationAction.BAN, user_id=user_id, admin_id=admin_id, reason="Violating rules")

        # Проверяем связь через user_id
        assert user.user_id == log.user_id
        assert user.is_banned is True

    def test_channel_moderation_relationship(self):
        """Тест связи между каналом и логами модерации."""
        chat_id = -1001234567890

        # Создаем канал
        channel = Channel(chat_id=chat_id, title="Test Channel", is_native=True)

        # Создаем лог модерации в этом канале
        log = ModerationLog(action=ModerationAction.BAN, user_id=123456789, admin_id=987654321, chat_id=chat_id)

        # Проверяем связь через chat_id
        assert channel.chat_id == log.chat_id

    def test_user_suspicious_profile_relationship(self):
        """Тест связи между пользователем и подозрительным профилем."""
        user_id = 123456789

        # Создаем пользователя
        user = User(user_id=user_id, first_name="Suspicious", username="sususer")

        # Создаем подозрительный профиль для этого пользователя
        profile = SuspiciousProfile(user_id=user_id, first_name="Suspicious", username="sususer", suspicion_score=0.75)

        # Проверяем связь
        assert user.user_id == profile.user_id
        assert user.first_name == profile.first_name
        assert user.username == profile.username


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
