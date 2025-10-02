"""
Unit tests for Redis rate limiting functionality.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.config import Settings
from app.middlewares.redis_rate_limit import RedisRateLimitMiddleware
from app.services.redis import RedisService


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return Settings(
        bot_token="test_token_123456789",
        admin_ids_list=[123456789],
        db_path=":memory:",
        redis_enabled=True,
        redis_url="redis://localhost:6379/0",
        redis_user_limit=10,
        redis_admin_limit=50,
        redis_interval=60,
        redis_strategy="fixed_window",
        redis_block_duration=300,
    )


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for tests."""
    service = Mock(spec=RedisService)
    service.is_available = AsyncMock(return_value=True)
    service.get_user_message_count = AsyncMock(return_value=0)
    service.increment_user_message_count = AsyncMock(return_value=1)
    service.is_user_blocked = AsyncMock(return_value=False)
    service.block_user = AsyncMock(return_value=True)
    service.get_user_block_ttl = AsyncMock(return_value=0)
    return service


@pytest.fixture
def mock_user():
    """Mock user for tests."""
    user = Mock()
    user.id = 123456789
    user.is_bot = False
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user for tests."""
    user = Mock()
    user.id = 123456789  # Admin ID
    user.is_bot = False
    return user


@pytest.fixture
def mock_message(mock_user):
    """Mock message for tests."""
    message = Mock()
    message.from_user = mock_user
    message.chat = Mock()
    message.chat.id = -1001234567890
    message.date = datetime.now()
    return message


class TestRedisRateLimitMiddleware:
    """Test Redis rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_middleware_initialization(self, mock_config, mock_redis_service):
        """Test middleware initialization."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        assert middleware.user_limit == 10
        assert middleware.admin_limit == 50
        assert middleware.interval == 60
        assert middleware.strategy == "fixed_window"
        assert middleware.block_duration == 300

    @pytest.mark.asyncio
    async def test_user_rate_limiting_within_limits(self, mock_config, mock_redis_service, mock_message):
        """Test user rate limiting within limits."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses
        mock_redis_service.get_user_message_count.return_value = 5
        mock_redis_service.is_user_blocked.return_value = False

        result = await middleware.check_rate_limit(mock_message)

        assert result["allowed"] is True
        assert result["reason"] == "OK"
        assert result["remaining"] == 5
        assert result["reset_time"] > 0

    @pytest.mark.asyncio
    async def test_user_rate_limiting_exceeded(self, mock_config, mock_redis_service, mock_message):
        """Test user rate limiting when exceeded."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses - user exceeded limit
        mock_redis_service.get_user_message_count.return_value = 15
        mock_redis_service.is_user_blocked.return_value = False
        mock_redis_service.block_user.return_value = True

        result = await middleware.check_rate_limit(mock_message)

        assert result["allowed"] is False
        assert "rate limit" in result["reason"].lower()
        assert result["remaining"] == 0
        assert result["reset_time"] > 0

    @pytest.mark.asyncio
    async def test_user_blocked(self, mock_config, mock_redis_service, mock_message):
        """Test blocked user."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses - user is blocked
        mock_redis_service.is_user_blocked.return_value = True
        mock_redis_service.get_user_block_ttl.return_value = 250

        result = await middleware.check_rate_limit(mock_message)

        assert result["allowed"] is False
        assert "blocked" in result["reason"].lower()
        assert result["remaining"] == 0
        assert result["reset_time"] == 250

    @pytest.mark.asyncio
    async def test_admin_rate_limiting(self, mock_config, mock_redis_service, mock_admin_user):
        """Test admin rate limiting with higher limits."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock admin message
        admin_message = Mock()
        admin_message.from_user = mock_admin_user
        admin_message.chat = Mock()
        admin_message.chat.id = -1001234567890
        admin_message.date = datetime.now()

        # Mock Redis responses - admin within limits
        mock_redis_service.get_user_message_count.return_value = 25
        mock_redis_service.is_user_blocked.return_value = False

        result = await middleware.check_rate_limit(admin_message)

        assert result["allowed"] is True
        assert result["reason"] == "OK"
        assert result["remaining"] == 25

    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(self, mock_config, mock_message):
        """Test fallback when Redis is unavailable."""
        # Mock Redis service as unavailable
        mock_redis_service = Mock(spec=RedisService)
        mock_redis_service.is_available.return_value = False

        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        result = await middleware.check_rate_limit(mock_message)

        # Should fallback to local rate limiting
        assert result["allowed"] is True
        assert result["reason"] == "OK"

    @pytest.mark.asyncio
    async def test_fixed_window_strategy(self, mock_config, mock_redis_service, mock_message):
        """Test fixed window rate limiting strategy."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses
        mock_redis_service.get_user_message_count.return_value = 5
        mock_redis_service.is_user_blocked.return_value = False

        result = await middleware.check_rate_limit(mock_message)

        assert result["allowed"] is True
        assert result["strategy"] == "fixed_window"

    @pytest.mark.asyncio
    async def test_sliding_window_strategy(self, mock_config, mock_redis_service, mock_message):
        """Test sliding window rate limiting strategy."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="sliding_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses
        mock_redis_service.get_user_message_count.return_value = 5
        mock_redis_service.is_user_blocked.return_value = False

        result = await middleware.check_rate_limit(mock_message)

        assert result["allowed"] is True
        assert result["strategy"] == "sliding_window"

    @pytest.mark.asyncio
    async def test_token_bucket_strategy(self, mock_config, mock_redis_service, mock_message):
        """Test token bucket rate limiting strategy."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="token_bucket",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses
        mock_redis_service.get_user_message_count.return_value = 5
        mock_redis_service.is_user_blocked.return_value = False

        result = await middleware.check_rate_limit(mock_message)

        assert result["allowed"] is True
        assert result["strategy"] == "token_bucket"

    @pytest.mark.asyncio
    async def test_message_processing(self, mock_config, mock_redis_service, mock_message):
        """Test message processing through middleware."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses
        mock_redis_service.get_user_message_count.return_value = 5
        mock_redis_service.is_user_blocked.return_value = False
        mock_redis_service.increment_user_message_count.return_value = 6

        # Mock handler
        handler = AsyncMock()

        # Process message
        await middleware(handler, mock_message, {})

        # Verify handler was called
        handler.assert_called_once_with(mock_message, {})

    @pytest.mark.asyncio
    async def test_message_blocked_by_rate_limit(self, mock_config, mock_redis_service, mock_message):
        """Test message blocked by rate limit."""
        middleware = RedisRateLimitMiddleware(
            user_limit=10,
            admin_limit=50,
            interval=60,
            strategy="fixed_window",
            block_duration=300,
            redis_service=mock_redis_service,
        )

        # Mock Redis responses - user exceeded limit
        mock_redis_service.get_user_message_count.return_value = 15
        mock_redis_service.is_user_blocked.return_value = False
        mock_redis_service.block_user.return_value = True

        # Mock handler
        handler = AsyncMock()

        # Process message
        await middleware(handler, mock_message, {})

        # Verify handler was NOT called
        handler.assert_not_called()


class TestRedisService:
    """Test Redis service functionality."""

    @pytest.mark.asyncio
    async def test_redis_service_initialization(self, mock_config):
        """Test Redis service initialization."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True

            service = RedisService(mock_config.redis_url)

            assert service.redis_url == mock_config.redis_url
            assert service.is_available() is True

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, mock_config):
        """Test Redis connection failure handling."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis.return_value.ping.side_effect = Exception("Connection failed")

            service = RedisService(mock_config.redis_url)

            assert service.is_available() is False

    @pytest.mark.asyncio
    async def test_get_user_message_count(self, mock_config):
        """Test getting user message count."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.get.return_value = "5"
            mock_redis.return_value = mock_redis_instance

            service = RedisService(mock_config.redis_url)
            count = await service.get_user_message_count(123456789, 60)

            assert count == 5

    @pytest.mark.asyncio
    async def test_increment_user_message_count(self, mock_config):
        """Test incrementing user message count."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.incr.return_value = 6
            mock_redis_instance.expire.return_value = True
            mock_redis.return_value = mock_redis_instance

            service = RedisService(mock_config.redis_url)
            count = await service.increment_user_message_count(123456789, 60)

            assert count == 6

    @pytest.mark.asyncio
    async def test_is_user_blocked(self, mock_config):
        """Test checking if user is blocked."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.exists.return_value = 1
            mock_redis.return_value = mock_redis_instance

            service = RedisService(mock_config.redis_url)
            blocked = await service.is_user_blocked(123456789)

            assert blocked is True

    @pytest.mark.asyncio
    async def test_block_user(self, mock_config):
        """Test blocking user."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.setex.return_value = True
            mock_redis.return_value = mock_redis_instance

            service = RedisService(mock_config.redis_url)
            result = await service.block_user(123456789, 300)

            assert result is True

    @pytest.mark.asyncio
    async def test_get_user_block_ttl(self, mock_config):
        """Test getting user block TTL."""
        with patch("app.services.redis.redis.Redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.ttl.return_value = 250
            mock_redis.return_value = mock_redis_instance

            service = RedisService(mock_config.redis_url)
            ttl = await service.get_user_block_ttl(123456789)

            assert ttl == 250


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
