"""
Redis Service - централизованное управление Redis соединением
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager

try:
    import aioredis
    from aioredis import Redis, ConnectionPool
    AIOREDIS_AVAILABLE = True
except ImportError:
    try:
        import redis.asyncio as aioredis
        from redis.asyncio import Redis, ConnectionPool
        AIOREDIS_AVAILABLE = True
    except ImportError:
        aioredis = None
        Redis = None
        ConnectionPool = None
        AIOREDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisService:
    """Сервис для работы с Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Установить соединение с Redis."""
        if not AIOREDIS_AVAILABLE:
            raise RuntimeError("Redis не доступен. Установите: pip install redis>=5.0.0")
        
        try:
            if self._is_connected:
                return
            
            # Создаем connection pool
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Создаем Redis клиент
            self._redis = Redis(connection_pool=self._pool)
            
            # Тестируем соединение
            await self._redis.ping()
            self._is_connected = True
            
            logger.info(f"Redis подключен: {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            self._is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """Закрыть соединение с Redis."""
        try:
            if self._redis:
                await self._redis.close()
                self._redis = None
            
            if self._pool:
                await self._pool.disconnect()
                self._pool = None
            
            self._is_connected = False
            logger.info("Redis соединение закрыто")
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии Redis: {e}")
    
    @property
    def redis(self) -> Redis:
        """Получить Redis клиент."""
        if not self._is_connected or not self._redis:
            raise RuntimeError("Redis не подключен. Вызовите connect() сначала.")
        return self._redis
    
    async def is_connected(self) -> bool:
        """Проверить, подключен ли Redis."""
        try:
            if not self._is_connected or not self._redis:
                return False
            await self._redis.ping()
            return True
        except Exception:
            self._is_connected = False
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Получить значение по ключу."""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Ошибка получения ключа {key}: {e}")
            return None
    
    async def set(self, key: str, value: Union[str, int, float], expire: Optional[int] = None) -> bool:
        """Установить значение по ключу."""
        try:
            return await self.redis.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Ошибка установки ключа {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить ключ."""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Ошибка удаления ключа {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа."""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Ошибка проверки ключа {key}: {e}")
            return False
    
    async def incr(self, key: str, expire: Optional[int] = None) -> int:
        """Увеличить значение на 1."""
        try:
            result = await self.redis.incr(key)
            if expire:
                await self.redis.expire(key, expire)
            return result
        except Exception as e:
            logger.error(f"Ошибка инкремента ключа {key}: {e}")
            return 0
    
    async def decr(self, key: str) -> int:
        """Уменьшить значение на 1."""
        try:
            return await self.redis.decr(key)
        except Exception as e:
            logger.error(f"Ошибка декремента ключа {key}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Установить время жизни ключа."""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Ошибка установки TTL для ключа {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Получить время жизни ключа."""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Ошибка получения TTL для ключа {key}: {e}")
            return -1
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Получить значение из hash."""
        try:
            return await self.redis.hget(name, key)
        except Exception as e:
            logger.error(f"Ошибка получения hash {name}.{key}: {e}")
            return None
    
    async def hset(self, name: str, key: str, value: Union[str, int, float]) -> bool:
        """Установить значение в hash."""
        try:
            result = await self.redis.hset(name, key, value)
            return result >= 0
        except Exception as e:
            logger.error(f"Ошибка установки hash {name}.{key}: {e}")
            return False
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Получить все значения из hash."""
        try:
            return await self.redis.hgetall(name)
        except Exception as e:
            logger.error(f"Ошибка получения hash {name}: {e}")
            return {}
    
    async def hdel(self, name: str, key: str) -> bool:
        """Удалить ключ из hash."""
        try:
            result = await self.redis.hdel(name, key)
            return result > 0
        except Exception as e:
            logger.error(f"Ошибка удаления hash {name}.{key}: {e}")
            return False
    
    async def lpush(self, key: str, *values: Union[str, int, float]) -> int:
        """Добавить значения в начало списка."""
        try:
            return await self.redis.lpush(key, *values)
        except Exception as e:
            logger.error(f"Ошибка lpush для ключа {key}: {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[str]:
        """Удалить и вернуть последний элемент списка."""
        try:
            return await self.redis.rpop(key)
        except Exception as e:
            logger.error(f"Ошибка rpop для ключа {key}: {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Получить длину списка."""
        try:
            return await self.redis.llen(key)
        except Exception as e:
            logger.error(f"Ошибка llen для ключа {key}: {e}")
            return 0
    
    @asynccontextmanager
    async def pipeline(self):
        """Контекстный менеджер для pipeline операций."""
        try:
            pipe = self.redis.pipeline()
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.error(f"Ошибка в pipeline: {e}")
            raise


# Глобальный экземпляр Redis сервиса
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """Получить глобальный экземпляр Redis сервиса."""
    global _redis_service
    
    if _redis_service is None:
        if not AIOREDIS_AVAILABLE:
            raise RuntimeError("Redis не доступен. Установите: pip install redis>=5.0.0")
        
        from app.config import load_config
        config = load_config()
        
        redis_url = getattr(config, 'redis_url', 'redis://localhost:6379/0')
        _redis_service = RedisService(redis_url)
        await _redis_service.connect()
    
    return _redis_service


async def close_redis_service() -> None:
    """Закрыть глобальный Redis сервис."""
    global _redis_service
    
    if _redis_service:
        try:
            await _redis_service.disconnect()
            logger.info("Redis service closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis service: {e}")
        finally:
            _redis_service = None
    else:
        logger.info("Redis service was not initialized, nothing to close")
