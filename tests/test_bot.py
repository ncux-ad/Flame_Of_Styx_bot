"""Basic bot tests."""

# from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import Settings
from app.models.user import User as UserModel


class TestBot:
    """Test bot functionality."""

    def test_settings_validation(self, test_settings):
        """Test settings validation."""
        assert test_settings.bot_token == "test_token"
        assert test_settings.admin_ids == [123456789]
        assert test_settings.db_path == ":memory:"

    def test_user_model_creation(self):
        """Test user model creation."""
        user = UserModel(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            is_bot=False,
        )

        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_bot is False
        assert user.is_banned is False
        assert user.is_muted is False

    def test_user_model_repr(self):
        """Test user model string representation."""
        user = UserModel(telegram_id=123456789, username="testuser", is_bot=False)

        repr_str = repr(user)
        assert "User" in repr_str
        assert "123456789" in repr_str
        assert "testuser" in repr_str
        assert "False" in repr_str


class TestConfig:
    """Test configuration."""

    def test_load_config(self):
        """Test config loading."""
        from app.config import load_config

        config = load_config()
        assert isinstance(config, Settings)
        assert hasattr(config, "bot_token")
        assert hasattr(config, "admin_ids")
        assert hasattr(config, "db_path")


class TestDatabase:
    """Test database functionality."""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection."""
        from app.database import get_db

        async for session in get_db():
            assert session is not None
            break
