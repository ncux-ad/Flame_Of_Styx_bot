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
        bot = Bot()
        bot.username = "testbot"
        bot.first_name = "Test Bot"
        bot.is_whitelisted = True

        assert bot.username == "testbot"
        assert bot.first_name == "Test Bot"
        assert bot.is_whitelisted is True
        assert bot.last_name is None

    def test_bot_str_representation(self):
        """Тест строкового представления бота."""
        bot = Bot()
        bot.username = "testbot"
        bot.first_name = "Test Bot"

        str_repr = str(bot)
        assert "testbot" in str_repr or "Test Bot" in str_repr


class TestChannelModel:
    """Тесты модели Channel."""

    def test_channel_creation(self):
        """Тест создания канала."""
        channel = Channel()
        channel.telegram_id = -1001234567890
        channel.title = "Test Channel"
        channel.username = "testchannel"
        channel.is_native = True
        channel.is_comment_group = False

        assert channel.telegram_id == -1001234567890
        assert channel.title == "Test Channel"
        assert channel.username == "testchannel"
        assert channel.is_native is True
        assert channel.is_comment_group is False

    def test_channel_without_username(self):
        """Тест канала без username."""
        channel = Channel()
        channel.telegram_id = -1001234567890
        channel.title = "Private Channel"
        channel.is_native = False

        assert channel.telegram_id == -1001234567890
        assert channel.title == "Private Channel"
        assert channel.username is None
        assert channel.is_native is False

    def test_channel_str_representation(self):
        """Тест строкового представления канала."""
        channel = Channel()
        channel.telegram_id = -1001234567890
        channel.title = "Test Channel"

        str_repr = str(channel)
        assert "Test Channel" in str_repr or str(channel.telegram_id) in str_repr


class TestUserModel:
    """Тесты модели User."""

    def test_user_creation(self):
        """Тест создания пользователя."""
        user = User()
        user.telegram_id = 123456789
        user.first_name = "Test"
        user.last_name = "User"
        user.username = "testuser"
        user.is_banned = False

        assert user.telegram_id == 123456789
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.username == "testuser"
        assert user.is_banned is False

    def test_user_without_optional_fields(self):
        """Тест пользователя без опциональных полей."""
        user = User()
        user.telegram_id = 123456789
        user.first_name = "Test"

        assert user.telegram_id == 123456789
        assert user.first_name == "Test"
        assert user.last_name is None
        assert user.username is None
        assert user.is_banned is False or user.is_banned is None  # default value может быть None

    def test_banned_user(self):
        """Тест заблокированного пользователя."""
        user = User()
        user.telegram_id = 123456789
        user.first_name = "Banned"
        user.is_banned = True
        user.ban_reason = "Spam"

        assert user.telegram_id == 123456789
        assert user.first_name == "Banned"
        assert user.is_banned is True
        assert user.ban_reason == "Spam"


class TestModerationLogModel:
    """Тесты модели ModerationLog."""

    def test_moderation_log_creation(self):
        """Тест создания лога модерации."""
        log = ModerationLog()
        log.action = ModerationAction.BAN
        log.admin_telegram_id = 987654321
        log.reason = "Spam messages"
        log.chat_id = -1001234567890

        assert log.action == ModerationAction.BAN
        assert log.admin_telegram_id == 987654321
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
        log = ModerationLog()
        log.action = ModerationAction.WARN
        log.admin_telegram_id = 987654321

        assert log.action == ModerationAction.WARN
        assert log.admin_telegram_id == 987654321
        assert log.reason is None
        assert log.chat_id is None


class TestSuspiciousProfileModel:
    """Тесты модели SuspiciousProfile."""

    def test_suspicious_profile_creation(self):
        """Тест создания подозрительного профиля."""
        profile = SuspiciousProfile()
        profile.user_id = 123456789
        profile.first_name = "Suspicious"
        profile.last_name = "User"
        profile.username = "sususer"
        profile.suspicion_score = 0.85
        profile.analysis_reason = "Short username, suspicious patterns"

        assert profile.user_id == 123456789
        assert profile.first_name == "Suspicious"
        assert profile.last_name == "User"
        assert profile.username == "sususer"
        assert profile.suspicion_score == 0.85
        assert "suspicious patterns" in profile.analysis_reason

    def test_high_suspicion_score(self):
        """Тест высокого балла подозрительности."""
        profile = SuspiciousProfile()
        profile.user_id = 123456789
        profile.first_name = "Bot"
        profile.suspicion_score = 0.95
        profile.analysis_reason = "GPT-like responses"

        assert profile.suspicion_score == 0.95
        assert profile.suspicion_score > 0.8  # Высокий уровень подозрительности
        assert profile.first_name == "Bot"
        assert "GPT-like" in profile.analysis_reason

    def test_suspicious_profile_without_optional_fields(self):
        """Тест подозрительного профиля без опциональных полей."""
        profile = SuspiciousProfile()
        profile.user_id = 123456789
        profile.suspicion_score = 0.6

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
        user = User()
        user.telegram_id = user_id
        user.first_name = "Test"
        user.is_banned = True

        # Создаем лог модерации для этого пользователя
        log = ModerationLog()
        log.action = ModerationAction.BAN
        log.admin_telegram_id = admin_id
        log.reason = "Violating rules"

        # Проверяем связь через user_id
        assert user.telegram_id == user_id
        assert user.is_banned is True

    def test_channel_moderation_relationship(self):
        """Тест связи между каналом и логами модерации."""
        chat_id = -1001234567890

        # Создаем канал
        channel = Channel()
        channel.telegram_id = chat_id
        channel.title = "Test Channel"
        channel.is_native = True

        # Создаем лог модерации в этом канале
        log = ModerationLog()
        log.action = ModerationAction.BAN
        log.admin_telegram_id = 987654321
        log.chat_id = chat_id

        # Проверяем связь через chat_id
        assert channel.telegram_id == log.chat_id

    def test_user_suspicious_profile_relationship(self):
        """Тест связи между пользователем и подозрительным профилем."""
        user_id = 123456789

        # Создаем пользователя
        user = User()
        user.telegram_id = user_id
        user.first_name = "Suspicious"
        user.username = "sususer"

        # Создаем подозрительный профиль для этого пользователя
        profile = SuspiciousProfile()
        profile.user_id = user_id
        profile.first_name = "Suspicious"
        profile.username = "sususer"
        profile.suspicion_score = 0.75

        # Проверяем связь
        assert user.telegram_id == profile.user_id
        assert user.first_name == profile.first_name
        assert user.username == profile.username


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
