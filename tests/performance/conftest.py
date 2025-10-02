"""
Configuration for performance tests
"""

import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import Settings
from app.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def perf_config():
    """Performance test configuration"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name
    
    return Settings(
        bot_token="123456789:performance_test_token",
        admin_ids="123456789",
        db_path=db_path,
        max_messages_per_minute=100,  # Within validation limits
        max_links_per_message=10,
        ban_duration_hours=24,
        redis_enabled=False,  # Disable Redis for consistent benchmarks
    )


@pytest_asyncio.fixture
async def perf_engine(perf_config):
    """Performance test database engine"""
    # Use SQLite in memory for fastest performance
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def perf_db_session(perf_engine):
    """Performance test database session"""
    async with AsyncSession(perf_engine) as session:
        yield session


@pytest.fixture
def perf_bot():
    """Mock bot for performance tests"""
    bot = MagicMock(spec=Bot)
    bot.id = 123456789
    bot.username = "perf_test_bot"
    bot.first_name = "Performance Test Bot"
    
    # Mock methods with fast responses
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))
    bot.ban_chat_member = AsyncMock(return_value=True)
    bot.unban_chat_member = AsyncMock(return_value=True)
    bot.get_chat = AsyncMock()
    bot.get_chat_member = AsyncMock()
    bot.get_me = AsyncMock()
    
    return bot


@pytest.fixture
def create_perf_message():
    """Factory for creating performance test messages"""
    def _create_message(
        text: str = "Test message",
        user_id: int = 123456789,
        chat_id: int = -1001234567890,
        message_id: int = 1
    ):
        message = MagicMock()
        message.message_id = message_id
        message.date = 1234567890
        message.text = text
        
        # Setup user
        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.from_user.is_bot = False
        message.from_user.first_name = "TestUser"
        message.from_user.last_name = "Performance"
        message.from_user.username = f"testuser{user_id}"
        
        # Setup chat
        message.chat = MagicMock()
        message.chat.id = chat_id
        message.chat.type = "supergroup" if int(chat_id) < 0 else "private"
        message.chat.title = f"Test Chat {chat_id}"
        
        # Add response methods
        message.answer = AsyncMock()
        message.reply = AsyncMock()
        message.edit_text = AsyncMock()
        
        return message
    
    return _create_message


@pytest.fixture
def benchmark_data_generator():
    """Generator for creating test data in bulk"""
    def _generate_users(count: int):
        """Generate test users"""
        return [
            {
                "telegram_id": 100000000 + i,
                "username": f"user_{i}",
                "first_name": f"User{i}",
                "last_name": "Test",
                "is_banned": i % 10 == 0,  # 10% banned
                "is_muted": i % 20 == 0,   # 5% muted
            }
            for i in range(count)
        ]
    
    def _generate_channels(count: int):
        """Generate test channels"""
        return [
            {
                "telegram_id": -1001000000000 - i,
                "title": f"Test Channel {i}",
                "username": f"testchannel{i}",
                "is_native": i % 3 == 0,  # 33% native
                "status": "ALLOWED" if i % 5 != 0 else "BLOCKED",  # 80% allowed
            }
            for i in range(count)
        ]
    
    def _generate_moderation_logs(count: int):
        """Generate test moderation logs"""
        actions = ["ban", "unban", "mute", "unmute", "warn", "delete_message"]
        return [
            {
                "user_id": 100000000 + (i % 1000),  # Cycle through users
                "chat_id": -1001000000000 - (i % 100),  # Cycle through chats
                "admin_telegram_id": 123456789,
                "action": actions[i % len(actions)],
                "reason": f"Test reason {i}",
                "is_active": i % 10 != 0,  # 90% active
            }
            for i in range(count)
        ]
    
    return {
        "users": _generate_users,
        "channels": _generate_channels,
        "moderation_logs": _generate_moderation_logs,
    }
