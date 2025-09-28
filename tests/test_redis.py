"""
Tests for Redis service
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.redis import RedisService


@pytest.mark.unit


class TestRedisService:
    """Test Redis service functionality."""
    
    @pytest.fixture
    def redis_service(self):
        """Create Redis service instance for testing."""
        return RedisService("redis://localhost:6379/0")
    
    @pytest.mark.asyncio
    async def test_redis_service_initialization(self, redis_service):
        """Test Redis service initialization."""
        assert redis_service.redis_url == "redis://localhost:6379/0"
        assert redis_service._redis is None
        assert redis_service._is_connected is False
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, redis_service):
        """Test Redis connection failure handling."""
        # Mock Redis connection failure
        with pytest.raises(Exception):
            await redis_service.connect()
    
    @pytest.mark.asyncio
    async def test_redis_operations_with_mock(self):
        """Test Redis operations with mocked connection."""
        redis_service = RedisService("redis://localhost:6379/0")
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = "test_value"
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 1
        mock_redis.incr.return_value = 2
        mock_redis.decr.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.ttl.return_value = 60
        mock_redis.hget.return_value = "hash_value"
        mock_redis.hset.return_value = 1
        mock_redis.hgetall.return_value = {"key1": "value1", "key2": "value2"}
        mock_redis.hdel.return_value = 1
        mock_redis.lpush.return_value = 3
        mock_redis.rpop.return_value = "last_item"
        mock_redis.llen.return_value = 2
        mock_redis.close.return_value = None
        
        # Mock connection pool
        mock_pool = AsyncMock()
        mock_pool.disconnect.return_value = None
        
        # Set mocked objects
        redis_service._redis = mock_redis
        redis_service._pool = mock_pool
        redis_service._is_connected = True
        
        # Test basic operations
        assert await redis_service.get("test_key") == "test_value"
        assert await redis_service.set("test_key", "test_value", expire=60) is True
        assert await redis_service.delete("test_key") is True
        assert await redis_service.exists("test_key") is True
        assert await redis_service.incr("counter") == 2
        assert await redis_service.decr("counter") == 1
        assert await redis_service.expire("key", 60) is True
        assert await redis_service.ttl("key") == 60
        
        # Test hash operations
        assert await redis_service.hget("hash", "key") == "hash_value"
        assert await redis_service.hset("hash", "key", "value") is True
        assert await redis_service.hgetall("hash") == {"key1": "value1", "key2": "value2"}
        assert await redis_service.hdel("hash", "key") is True
        
        # Test list operations
        assert await redis_service.lpush("list", "item1", "item2") == 3
        assert await redis_service.rpop("list") == "last_item"
        assert await redis_service.llen("list") == 2
        
        # Test connection status
        assert await redis_service.is_connected() is True
        
        # Test disconnect
        await redis_service.disconnect()
        assert redis_service._is_connected is False
    
    @pytest.mark.asyncio
    async def test_redis_pipeline(self):
        """Test Redis pipeline operations."""
        redis_service = RedisService("redis://localhost:6379/0")
        
        # Mock pipeline
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [True, 1, 2]
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        redis_service._redis = mock_redis
        redis_service._is_connected = True
        
        # Test pipeline context manager
        async with redis_service.pipeline() as pipe:
            pipe.set("key1", "value1")
            pipe.incr("counter")
            pipe.get("key2")
        
        # Verify pipeline was executed
        mock_pipeline.execute.assert_called_once()
    
    def test_redis_service_properties(self, redis_service):
        """Test Redis service properties."""
        # Test when not connected
        with pytest.raises(RuntimeError):
            _ = redis_service.redis
        
        # Test when connected
        mock_redis = AsyncMock()
        redis_service._redis = mock_redis
        redis_service._is_connected = True
        
        assert redis_service.redis == mock_redis
