"""
Расширенные тесты конфигурации для увеличения покрытия.
"""

import pytest

from app.config import Settings, load_config


class TestConfigEnhanced:
    """Расширенные тесты конфигурации."""

    @pytest.mark.unit
    def test_config_defaults(self):
        """Тест значений по умолчанию."""
        config = Settings(
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop", admin_ids="123456789", db_path="test.sqlite3"
        )

        assert config.bot_token.startswith("123456789:")
        assert config.admin_ids == "123456789"
        assert config.db_path == "test.sqlite3"
        assert config.redis_enabled is False
        assert config.redis_user_limit == 10
        assert config.redis_admin_limit == 100

    @pytest.mark.unit
    def test_admin_ids_list_property(self):
        """Тест свойства admin_ids_list."""
        config = Settings(
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop",
            admin_ids="123456789,987654321",
            db_path="test.sqlite3",
        )

        admin_list = config.admin_ids_list
        assert isinstance(admin_list, list)
        assert len(admin_list) == 2
        assert 123456789 in admin_list
        assert 987654321 in admin_list

    @pytest.mark.unit
    def test_load_config_function(self):
        """Тест функции load_config."""
        # Тестируем загрузку конфигурации
        config = load_config()
        assert isinstance(config, Settings)
        assert hasattr(config, "bot_token")
        assert hasattr(config, "admin_ids")
        assert hasattr(config, "db_path")

    @pytest.mark.unit
    def test_redis_configuration(self):
        """Тест Redis конфигурации."""
        config = Settings(
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop",
            admin_ids="123456789",
            db_path="test.sqlite3",
            redis_enabled=True,
            redis_url="redis://localhost:6379/0",
            redis_user_limit=15,
            redis_admin_limit=150,
            redis_strategy="sliding_window",
        )

        assert config.redis_enabled is True
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.redis_user_limit == 15
        assert config.redis_admin_limit == 150
        assert config.redis_strategy == "sliding_window"

    @pytest.mark.unit
    def test_limits_configuration(self):
        """Тест конфигурации лимитов."""
        config = Settings(
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop",
            admin_ids="123456789",
            db_path="test.sqlite3",
            max_messages_per_minute=20,
            max_links_per_message=5,
            ban_duration_hours=48,
            suspicion_threshold=0.7,
        )

        assert config.max_messages_per_minute == 20
        assert config.max_links_per_message == 5
        assert config.ban_duration_hours == 48
        assert config.suspicion_threshold == 0.7

    @pytest.mark.unit
    def test_channel_configuration(self):
        """Тест конфигурации каналов."""
        config = Settings(
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop",
            admin_ids="123456789",
            db_path="test.sqlite3",
            native_channel_ids="-1001234567890,-1009876543210",
            ignore_channel_ids="-1001111111111,-1002222222222",
        )

        assert config.native_channel_ids == "-1001234567890,-1009876543210"
        assert config.ignore_channel_ids == "-1001111111111,-1002222222222"

    @pytest.mark.unit
    def test_media_configuration(self):
        """Тест конфигурации медиа."""
        config = Settings(
            bot_token="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop",
            admin_ids="123456789",
            db_path="test.sqlite3",
            allow_photos_without_caption=False,
            allow_videos_without_caption=False,
            check_media_without_caption=True,
        )

        assert config.allow_photos_without_caption is False
        assert config.allow_videos_without_caption is False
        assert config.check_media_without_caption is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
