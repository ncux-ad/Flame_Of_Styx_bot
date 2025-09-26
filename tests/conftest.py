"""Pytest configuration and fixtures."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, User

from app.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings."""
    return Settings(
        bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz123456789",
        admin_ids="123456789,987654321",
        db_path="test.db"
    )


@pytest.fixture
def mock_bot():
    """Mock bot instance."""
    bot = AsyncMock(spec=Bot)
    bot.token = "test_token"
    return bot


@pytest.fixture
def mock_dispatcher():
    """Mock dispatcher instance."""
    return MagicMock(spec=Dispatcher)


@pytest.fixture
def mock_user():
    """Mock user instance."""
    return User(
        id=123456789, is_bot=False, first_name="Test", last_name="User", username="testuser"
    )


@pytest.fixture
def mock_bot_user():
    """Mock bot user instance."""
    return User(id=987654321, is_bot=True, first_name="Test Bot", username="testbot")


@pytest.fixture
def mock_chat():
    """Mock chat instance."""
    return Chat(id=-1001234567890, type="supergroup", title="Test Channel")


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Mock message instance."""
    return Message(
        message_id=1, from_user=mock_user, chat=mock_chat, date=1234567890, text="Test message"
    )


@pytest.fixture
def mock_channel_message(mock_chat):
    """Mock message from channel."""
    return Message(
        message_id=1,
        from_user=None,
        sender_chat=mock_chat,
        chat=mock_chat,
        date=1234567890,
        text="Test channel message",
    )
