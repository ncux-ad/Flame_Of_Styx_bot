"""
Tests for configuration module
"""

import pytest
from app.config import load_config, Settings


@pytest.mark.unit


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_load_config_default(self):
        """Test loading configuration with default values."""
        # Set test environment variables
        import os
        os.environ['BOT_TOKEN'] = 'test_token_123456789'
        os.environ['ADMIN_IDS'] = '123456789'
        os.environ['DB_PATH'] = 'test.db'
        os.environ['REDIS_ENABLED'] = 'false'
        os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
        
        config = load_config()
        assert isinstance(config, Settings)
        assert config.redis_enabled is False  # Default should be False
        assert config.redis_user_limit == 10
        assert config.redis_admin_limit == 100
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid configuration
        config = Settings(
            bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            admin_ids="123456789,987654321",
            db_path="test.db"
        )
        assert config.bot_token == "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        assert config.admin_ids_list == [123456789, 987654321]
    
    def test_redis_strategy_validation(self):
        """Test Redis strategy validation."""
        # Valid strategies
        valid_strategies = ["fixed_window", "sliding_window", "token_bucket"]
        for strategy in valid_strategies:
            config = Settings(
                bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                admin_ids="123456789",
                db_path="test.db",
                redis_strategy=strategy
            )
            assert config.redis_strategy == strategy
        
        # Invalid strategy should raise error
        with pytest.raises(ValueError):
            Settings(
                bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                admin_ids="123456789",
                db_path="test.db",
                redis_strategy="invalid_strategy"
            )
    
    def test_redis_url_validation(self):
        """Test Redis URL validation."""
        # Valid URLs
        valid_urls = [
            "redis://localhost:6379/0",
            "rediss://localhost:6380/0",
            "redis://user:pass@localhost:6379/0"
        ]
        for url in valid_urls:
            config = Settings(
                bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                admin_ids="123456789",
                db_path="test.db",
                redis_url=url
            )
            assert config.redis_url == url
        
        # Invalid URL should raise error
        with pytest.raises(ValueError):
            Settings(
                bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                admin_ids="123456789",
                db_path="test.db",
                redis_url="invalid://url"
            )
    
    def test_admin_ids_parsing(self):
        """Test admin IDs parsing."""
        config = Settings(
            bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            admin_ids="123456789,987654321,555666777",
            db_path="test.db"
        )
        assert config.admin_ids_list == [123456789, 987654321, 555666777]
    
    def test_native_channel_ids_parsing(self):
        """Test native channel IDs parsing."""
        config = Settings(
            bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            admin_ids="123456789",
            db_path="test.db",
            native_channel_ids="-1001234567890,-1009876543210"
        )
        assert config.native_channel_ids_list == [-1001234567890, -1009876543210]
    
    def test_limits_dict(self):
        """Test limits dictionary generation."""
        config = Settings(
            bot_token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            admin_ids="123456789",
            db_path="test.db",
            max_messages_per_minute=15,
            max_links_per_message=5,
            ban_duration_hours=48
        )
        
        limits = config.get_limits_dict()
        assert limits["max_messages_per_minute"] == 15
        assert limits["max_links_per_message"] == 5
        assert limits["ban_duration_hours"] == 48
