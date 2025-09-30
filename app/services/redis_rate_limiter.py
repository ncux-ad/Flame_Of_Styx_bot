"""
Redis Rate Limiter Service
Централизованный rate limiting через Redis
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

import redis.asyncio as redis
from aiogram.types import Message

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Конфигурация rate limiting."""
    max_requests: int
    window_seconds: int
    key_prefix: str = "rate_limit"


@dataclass
class RateLimitResult:
    """Результат проверки rate limit."""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None


class RedisRateLimiter:
    """Централизованный rate limiter через Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Инициализация Redis rate limiter."""
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.configs: Dict[str, RateLimitConfig] = {}
        
        # Конфигурации по умолчанию
        self._setup_default_configs()

    def _setup_default_configs(self):
        """Настройка конфигураций по умолчанию."""
        self.configs = {
            "user_messages": RateLimitConfig(
                max_requests=10,
                window_seconds=60,
                key_prefix="user_msg"
            ),
            "admin_commands": RateLimitConfig(
                max_requests=30,
                window_seconds=60,
                key_prefix="admin_cmd"
            ),
            "spam_analysis": RateLimitConfig(
                max_requests=5,
                window_seconds=300,  # 5 минут
                key_prefix="spam_analysis"
            ),
            "channel_management": RateLimitConfig(
                max_requests=20,
                window_seconds=60,
                key_prefix="channel_mgmt"
            )
        }

    async def connect(self):
        """Подключение к Redis."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Проверяем подключение
            await self.redis_client.ping()
            logger.info("Redis rate limiter connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Отключение от Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis rate limiter disconnected")

    def _get_key(self, config_name: str, identifier: str) -> str:
        """Генерация ключа для Redis."""
        config = self.configs.get(config_name)
        if not config:
            raise ValueError(f"Unknown config: {config_name}")
        
        return f"{config.key_prefix}:{identifier}"

    async def check_rate_limit(
        self, 
        config_name: str, 
        identifier: str
    ) -> RateLimitResult:
        """
        Проверка rate limit для идентификатора.
        
        Args:
            config_name: Название конфигурации
            identifier: Уникальный идентификатор (user_id, chat_id, etc.)
            
        Returns:
            RateLimitResult с результатом проверки
        """
        if not self.redis_client:
            logger.warning("Redis not connected, allowing request")
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=time.time() + 60
            )

        config = self.configs.get(config_name)
        if not config:
            logger.error(f"Unknown rate limit config: {config_name}")
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=time.time() + 60
            )

        key = self._get_key(config_name, identifier)
        current_time = time.time()
        window_start = current_time - config.window_seconds

        try:
            # Используем Redis pipeline для атомарности
            pipe = self.redis_client.pipeline()
            
            # Удаляем старые записи
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Подсчитываем текущие запросы
            pipe.zcard(key)
            
            # Добавляем текущий запрос
            pipe.zadd(key, {str(current_time): current_time})
            
            # Устанавливаем TTL
            pipe.expire(key, config.window_seconds)
            
            results = await pipe.execute()
            current_count = results[1]
            
            if current_count < config.max_requests:
                # Разрешаем запрос
                remaining = config.max_requests - current_count - 1
                reset_time = current_time + config.window_seconds
                
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_time=reset_time
                )
            else:
                # Блокируем запрос
                oldest_request = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    reset_time = oldest_request[0][1] + config.window_seconds
                    retry_after = reset_time - current_time
                else:
                    reset_time = current_time + config.window_seconds
                    retry_after = config.window_seconds
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
                
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # В случае ошибки разрешаем запрос
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=time.time() + 60
            )

    async def get_rate_limit_info(
        self, 
        config_name: str, 
        identifier: str
    ) -> Dict:
        """Получение информации о текущем rate limit."""
        if not self.redis_client:
            return {"error": "Redis not connected"}

        config = self.configs.get(config_name)
        if not config:
            return {"error": f"Unknown config: {config_name}"}

        key = self._get_key(config_name, identifier)
        current_time = time.time()
        window_start = current_time - config.window_seconds

        try:
            # Очищаем старые записи
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Получаем статистику
            current_count = await self.redis_client.zcard(key)
            remaining = max(0, config.max_requests - current_count)
            
            # Получаем время сброса
            oldest_request = await self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = oldest_request[0][1] + config.window_seconds
            else:
                reset_time = current_time + config.window_seconds

            return {
                "config_name": config_name,
                "identifier": identifier,
                "current_count": current_count,
                "max_requests": config.max_requests,
                "remaining": remaining,
                "window_seconds": config.window_seconds,
                "reset_time": reset_time,
                "reset_in_seconds": max(0, reset_time - current_time)
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {"error": str(e)}

    async def reset_rate_limit(self, config_name: str, identifier: str) -> bool:
        """Сброс rate limit для идентификатора."""
        if not self.redis_client:
            return False

        try:
            key = self._get_key(config_name, identifier)
            await self.redis_client.delete(key)
            logger.info(f"Rate limit reset for {config_name}:{identifier}")
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False

    def add_config(self, name: str, config: RateLimitConfig):
        """Добавление новой конфигурации rate limiting."""
        self.configs[name] = config
        logger.info(f"Added rate limit config: {name}")

    def get_config(self, name: str) -> Optional[RateLimitResult]:
        """Получение конфигурации rate limiting."""
        return self.configs.get(name)

    def list_configs(self) -> Dict[str, RateLimitConfig]:
        """Получение всех конфигураций."""
        return self.configs.copy()


# Глобальный экземпляр rate limiter
_redis_rate_limiter: Optional[RedisRateLimiter] = None


async def get_redis_rate_limiter() -> RedisRateLimiter:
    """Получение глобального экземпляра Redis rate limiter."""
    global _redis_rate_limiter
    
    if _redis_rate_limiter is None:
        _redis_rate_limiter = RedisRateLimiter()
        await _redis_rate_limiter.connect()
    
    return _redis_rate_limiter


async def check_user_rate_limit(message: Message) -> RateLimitResult:
    """Проверка rate limit для пользователя."""
    if not message.from_user:
        return RateLimitResult(
            allowed=True,
            remaining=999,
            reset_time=time.time() + 60
        )
    
    rate_limiter = await get_redis_rate_limiter()
    return await rate_limiter.check_rate_limit(
        "user_messages",
        str(message.from_user.id)
    )


async def check_admin_rate_limit(message: Message) -> RateLimitResult:
    """Проверка rate limit для админских команд."""
    if not message.from_user:
        return RateLimitResult(
            allowed=True,
            remaining=999,
            reset_time=time.time() + 60
        )
    
    rate_limiter = await get_redis_rate_limiter()
    return await rate_limiter.check_rate_limit(
        "admin_commands",
        str(message.from_user.id)
    )


async def check_spam_analysis_rate_limit(message: Message) -> RateLimitResult:
    """Проверка rate limit для анализа спама."""
    if not message.from_user:
        return RateLimitResult(
            allowed=True,
            remaining=999,
            reset_time=time.time() + 60
        )
    
    rate_limiter = await get_redis_rate_limiter()
    return await rate_limiter.check_rate_limit(
        "spam_analysis",
        str(message.from_user.id)
    )
