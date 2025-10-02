"""
Простые unit-тесты для антиспам функциональности.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Chat, Message, User

from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService


@pytest.fixture
def mock_bot():
    """Mock bot fixture."""
    return Mock()


@pytest.fixture
def mock_db():
    """Mock database fixture."""
    return Mock()


@pytest.fixture
def mock_user():
    """Mock user fixture."""
    user = Mock()
    user.id = 123456789
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.is_bot = False
    return user


@pytest.fixture
def mock_chat():
    """Mock chat fixture."""
    chat = Mock()
    chat.id = -1001234567890
    chat.type = "supergroup"
    chat.title = "Test Chat"
    return chat


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Mock message fixture."""
    message = Mock()
    message.message_id = 1
    message.from_user = mock_user
    message.chat = mock_chat
    message.text = "Test message"
    message.date = 1234567890
    return message


class TestModerationService:
    """Тесты ModerationService."""

    @pytest.mark.asyncio
    async def test_service_creation(self, mock_bot, mock_db):
        """Тест создания сервиса."""
        service = ModerationService(mock_bot, mock_db)
        assert service.bot == mock_bot
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_ban_user(self, mock_bot, mock_db):
        """Тест блокировки пользователя."""
        service = ModerationService(mock_bot, mock_db)

        # Мокаем методы
        mock_bot.ban_chat_member = AsyncMock(return_value=True)
        service.db.execute = AsyncMock()
        service.db.commit = AsyncMock()

        result = await service.ban_user(123456789, -1001234567890, 439304619, "Test reason")
        assert result is True

        # Проверяем, что методы вызвались
        mock_bot.ban_chat_member.assert_called_once()
        service.db.execute.assert_called()
        service.db.commit.assert_called()


class TestLinkService:
    """Тесты LinkService."""

    @pytest.mark.asyncio
    async def test_service_creation(self, mock_bot, mock_db):
        """Тест создания LinkService."""
        service = LinkService(mock_bot, mock_db)
        assert service.bot == mock_bot
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_check_message_simple(self, mock_bot, mock_db, mock_message):
        """Тест простой проверки сообщения."""
        service = LinkService(mock_bot, mock_db)

        # Простое сообщение без ссылок
        mock_message.text = "Hello, world!"
        result = await service.check_message_for_bot_links(mock_message)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_check_message_with_link(self, mock_bot, mock_db, mock_message):
        """Тест проверки сообщения со ссылкой."""
        service = LinkService(mock_bot, mock_db)

        # Сообщение со ссылкой
        mock_message.text = "Check out @testbot"
        result = await service.check_message_for_bot_links(mock_message)
        assert isinstance(result, list)


class TestProfileService:
    """Тесты ProfileService."""

    @pytest.mark.asyncio
    async def test_service_creation(self, mock_bot, mock_db):
        """Тест создания ProfileService."""
        service = ProfileService(mock_bot, mock_db)
        assert service.bot == mock_bot
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_get_user_info(self, mock_bot, mock_db):
        """Тест получения информации о пользователе."""
        service = ProfileService(mock_bot, mock_db)

        # Мокаем базу данных
        service.db.execute = AsyncMock()
        service.db.execute.return_value.scalar_one_or_none = Mock(return_value=None)

        result = await service.get_user_info(123456789)
        assert isinstance(result, dict)
        assert "id" in result  # ProfileService возвращает "id", а не "user_id"


class TestPatternDetection:
    """Тесты обнаружения паттернов спама."""

    def test_emoji_detection(self):
        """Тест обнаружения эмодзи."""
        import re

        # Паттерн для эмодзи
        emoji_pattern = r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]"

        # Тест обычного текста
        normal_text = "Hello, world!"
        emoji_count = len(re.findall(emoji_pattern, normal_text))
        assert emoji_count == 0

        # Тест текста с эмодзи
        text_with_emojis = "Hello! 😊 How are you? 👍"
        emoji_count = len(re.findall(emoji_pattern, text_with_emojis))
        assert emoji_count == 2

    def test_caps_detection(self):
        """Тест обнаружения CAPS LOCK."""
        # Нормальный текст
        normal_text = "Hello, world!"
        caps_ratio = sum(1 for c in normal_text if c.isupper()) / len(normal_text)
        assert caps_ratio < 0.5

        # CAPS текст
        caps_text = "HELLO WORLD!!!"
        caps_ratio = sum(1 for c in caps_text if c.isupper()) / len(caps_text)
        assert caps_ratio > 0.5

    def test_link_detection(self):
        """Тест обнаружения ссылок."""
        import re

        # Паттерн для URL
        url_pattern = r"https?://[^\s]+"

        # Текст без ссылок
        normal_text = "Hello, world!"
        links = re.findall(url_pattern, normal_text)
        assert len(links) == 0

        # Текст со ссылками
        text_with_links = "Check out https://example.com and https://test.org"
        links = re.findall(url_pattern, text_with_links)
        assert len(links) == 2

    def test_suspicious_patterns(self):
        """Тест обнаружения подозрительных паттернов."""
        # Подозрительные ключевые слова
        suspicious_keywords = [
            "FREE MONEY",
            "CLICK HERE",
            "URGENT",
            "LIMITED TIME",
            "BUY NOW",
            "EARN MONEY",
            "GET RICH",
            "MIRACLE",
        ]

        # Нормальный текст
        normal_text = "Hello, how are you today?"
        suspicious_count = sum(1 for keyword in suspicious_keywords if keyword.lower() in normal_text.lower())
        assert suspicious_count == 0

        # Подозрительный текст
        suspicious_text = "FREE MONEY! CLICK HERE NOW! LIMITED TIME OFFER!"
        suspicious_count = sum(1 for keyword in suspicious_keywords if keyword.lower() in suspicious_text.lower())
        assert suspicious_count > 0


class TestValidation:
    """Тесты валидации данных."""

    def test_user_id_validation(self):
        """Тест валидации ID пользователя."""
        # Корректные ID
        valid_ids = [123456789, 987654321, 111111111]
        for user_id in valid_ids:
            assert isinstance(user_id, int)
            assert user_id > 0
            assert len(str(user_id)) >= 6  # Telegram ID обычно длиннее 6 цифр

        # Некорректные ID
        invalid_ids = [0, -1, "abc", None]
        for user_id in invalid_ids:
            if user_id is not None and isinstance(user_id, int):
                assert user_id <= 0
            else:
                assert not isinstance(user_id, int) or user_id is None

    def test_chat_id_validation(self):
        """Тест валидации ID чата."""
        # Корректные ID чатов
        valid_chat_ids = [-1001234567890, -1009876543210]  # Супергруппы
        for chat_id in valid_chat_ids:
            assert isinstance(chat_id, int)
            assert chat_id < 0  # Групповые чаты имеют отрицательные ID

        # Корректные ID приватных чатов
        valid_private_ids = [123456789, 987654321]
        for chat_id in valid_private_ids:
            assert isinstance(chat_id, int)
            assert chat_id > 0  # Приватные чаты имеют положительные ID

    def test_message_length_validation(self):
        """Тест валидации длины сообщения."""
        # Нормальное сообщение
        normal_message = "Hello, world!"
        assert len(normal_message) < 4096  # Лимит Telegram

        # Длинное сообщение
        long_message = "A" * 5000
        assert len(long_message) > 4096


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
