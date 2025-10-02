"""
Конфигурация для интеграционных тестов
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, User
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import Settings
from app.database import Base, get_db
from app.middlewares.di_middleware import DIMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware
from app.middlewares.validation import ValidationMiddleware


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Тестовая конфигурация"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name
    
    return Settings(
        bot_token="123456789:test_token_for_integration_tests",
        admin_ids="123456789,987654321",
        db_path=db_path,
        max_messages_per_minute=10,
        max_links_per_message=3,
        ban_duration_hours=24,
        redis_enabled=False,  # Отключаем Redis для интеграционных тестов
    )


@pytest_asyncio.fixture
async def test_engine(test_config):
    """Тестовый движок базы данных"""
    # Используем SQLite в памяти для тестов
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очистка
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine):
    """Тестовая сессия базы данных"""
    async with AsyncSession(test_engine) as session:
        yield session


@pytest.fixture
def mock_bot():
    """Мок бота для тестов"""
    bot = MagicMock(spec=Bot)
    bot.id = 123456789
    bot.username = "test_bot"
    bot.first_name = "Test Bot"
    
    # Мокаем основные методы
    bot.send_message = AsyncMock()
    bot.ban_chat_member = AsyncMock(return_value=True)
    bot.unban_chat_member = AsyncMock(return_value=True)
    bot.get_chat = AsyncMock()
    bot.get_chat_member = AsyncMock()
    bot.get_me = AsyncMock()
    
    return bot


@pytest.fixture
def test_dispatcher(mock_bot, test_config):
    """Тестовый диспетчер с настроенными middleware"""
    dp = Dispatcher()
    
    # Добавляем middleware в правильном порядке
    dp.message.middleware(ValidationMiddleware())
    dp.message.middleware(RateLimitMiddleware(
        user_limit=test_config.max_messages_per_minute,
        admin_limit=100,
        interval=60
    ))
    dp.message.middleware(DIMiddleware())
    
    return dp


@pytest.fixture
def test_user():
    """Тестовый пользователь"""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser"
    )


@pytest.fixture
def test_admin_user():
    """Тестовый админ пользователь"""
    return User(
        id=987654321,
        is_bot=False,
        first_name="Admin",
        last_name="User",
        username="adminuser"
    )


@pytest.fixture
def test_chat():
    """Тестовый чат"""
    return Chat(
        id=-1001234567890,
        type="supergroup",
        title="Test Chat"
    )


@pytest.fixture
def test_private_chat(test_user):
    """Тестовый приватный чат"""
    return Chat(
        id=test_user.id,
        type="private"
    )


@pytest.fixture
def create_test_message():
    """Фабрика для создания тестовых сообщений (MagicMock для избежания frozen instance)"""
    def _create_message(
        text: str = "Test message",
        user_id: int = 123456789,
        chat_id: int = -1001234567890,
        message_id: int = 1,
        is_admin: bool = False
    ):
        message = MagicMock()
        message.message_id = message_id
        message.date = 1234567890
        message.text = text
        
        # Настраиваем пользователя
        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.from_user.is_bot = False
        message.from_user.first_name = "Admin" if is_admin else "Test"
        message.from_user.last_name = "User"
        message.from_user.username = "adminuser" if is_admin else "testuser"
        
        # Настраиваем чат
        message.chat = MagicMock()
        message.chat.id = chat_id
        message.chat.type = "supergroup" if int(chat_id) < 0 else "private"
        message.chat.title = "Test Chat" if int(chat_id) < 0 else None
        
        # Добавляем методы для ответов
        message.answer = AsyncMock()
        message.reply = AsyncMock()
        message.edit_text = AsyncMock()
        
        return message
    
    return _create_message


@pytest.fixture
def create_test_callback():
    """Фабрика для создания тестовых callback query"""
    def _create_callback(
        data: str = "test_data",
        user_id: int = 123456789,
        callback_id: str = "test_callback_id"
    ):
        callback = MagicMock()
        callback.id = callback_id
        callback.data = data
        callback.chat_instance = "test_chat_instance"
        
        # Настраиваем пользователя
        callback.from_user = MagicMock()
        callback.from_user.id = user_id
        callback.from_user.is_bot = False
        callback.from_user.first_name = "Test"
        callback.from_user.last_name = "User"
        callback.from_user.username = "testuser"
        
        # Настраиваем сообщение
        callback.message = MagicMock()
        callback.message.message_id = 1
        callback.message.edit_text = AsyncMock()
        callback.message.edit_reply_markup = AsyncMock()
        
        # Добавляем методы для ответов
        callback.answer = AsyncMock()
        
        return callback
    
    return _create_callback


@pytest.fixture
def create_test_update():
    """Фабрика для создания тестовых Update объектов"""
    def _create_update(message=None, callback_query=None, update_id: int = 1):
        # Создаем правильную структуру для Update
        update_data = {
            "update_id": update_id,
            "message": message,
            "callback_query": callback_query,
            "edited_message": None,
            "channel_post": None,
            "edited_channel_post": None,
            "inline_query": None,
            "chosen_inline_result": None,
            "shipping_query": None,
            "pre_checkout_query": None,
            "poll": None,
            "poll_answer": None,
            "my_chat_member": None,
            "chat_member": None,
            "chat_join_request": None
        }
        
        # Создаем MagicMock с правильными атрибутами
        update = MagicMock()
        update.update_id = update_id
        update.message = message
        update.callback_query = callback_query
        update.edited_message = None
        update.channel_post = None
        update.edited_channel_post = None
        update.inline_query = None
        update.chosen_inline_result = None
        update.shipping_query = None
        update.pre_checkout_query = None
        update.poll = None
        update.poll_answer = None
        update.my_chat_member = None
        update.chat_member = None
        update.chat_join_request = None
        
        # Добавляем методы для совместимости с Pydantic
        update.model_dump = MagicMock(return_value=update_data)
        update.model_validate = MagicMock(return_value=update)
        
        # Добавляем атрибуты для совместимости с Aiogram
        update.bot = None
        update._bot = None
        
        return update
    
    return _create_update
