"""
Redis Rate Limiting Middleware - централизованный rate limiting через Redis
"""

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from app.services.redis import get_redis_service
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class RedisRateLimitMiddleware(BaseMiddleware):
    """
    Middleware для rate limiting через Redis.
    
    Поддерживает различные стратегии:
    - Fixed window (фиксированное окно)
    - Sliding window (скользящее окно)
    - Token bucket (ведро токенов)
    """
    
    def __init__(
        self,
        user_limit: int = 10,
        admin_limit: int = 100,
        interval: int = 60,
        strategy: str = "sliding_window",
        redis_key_prefix: str = "rate_limit",
        block_duration: int = 300,  # 5 минут блокировки
    ):
        """
        Инициализация Redis Rate Limiting middleware.
        
        Args:
            user_limit: Лимит сообщений для обычных пользователей
            admin_limit: Лимит сообщений для администраторов
            interval: Интервал в секундах
            strategy: Стратегия rate limiting (fixed_window, sliding_window, token_bucket)
            redis_key_prefix: Префикс для ключей в Redis
            block_duration: Длительность блокировки в секундах
        """
        self.user_limit = user_limit
        self.admin_limit = admin_limit
        self.interval = interval
        self.strategy = strategy
        self.redis_key_prefix = redis_key_prefix
        self.block_duration = block_duration
        
        # Кэш для локального хранения блокировок (избегаем частых запросов к Redis)
        self._blocked_users: Dict[int, float] = {}
        self._cache_cleanup_interval = 60  # Очистка кэша каждые 60 секунд
        self._last_cache_cleanup = time.time()
    
    def _get_user_id(self, update: Update) -> Optional[int]:
        """Получить ID пользователя из update."""
        if update.message and update.message.from_user:
            return update.message.from_user.id
        elif update.callback_query and update.callback_query.from_user:
            return update.callback_query.from_user.id
        return None
    
    def _is_admin(self, user_id: int, admin_ids: list) -> bool:
        """Проверить, является ли пользователь администратором."""
        return user_id in admin_ids
    
    def _get_rate_limit_key(self, user_id: int, strategy: str) -> str:
        """Получить ключ для rate limiting в Redis."""
        if strategy == "fixed_window":
            # Фиксированное окно - ключ обновляется каждую минуту
            window = int(time.time() // self.interval)
            return f"{self.redis_key_prefix}:fixed:{user_id}:{window}"
        
        elif strategy == "sliding_window":
            # Скользящее окно - используем timestamp
            return f"{self.redis_key_prefix}:sliding:{user_id}"
        
        elif strategy == "token_bucket":
            # Ведро токенов - отдельные ключи для токенах и времени
            return f"{self.redis_key_prefix}:bucket:{user_id}"
        
        else:
            raise ValueError(f"Неизвестная стратегия: {strategy}")
    
    def _get_block_key(self, user_id: int) -> str:
        """Получить ключ для блокировки пользователя."""
        return f"{self.redis_key_prefix}:blocked:{user_id}"
    
    async def _is_user_blocked(self, redis, user_id: int) -> bool:
        """Проверить, заблокирован ли пользователь."""
        # Сначала проверяем локальный кэш
        if user_id in self._blocked_users:
            if time.time() - self._blocked_users[user_id] < self.block_duration:
                return True
            else:
                # Блокировка истекла, удаляем из кэша
                del self._blocked_users[user_id]
        
        # Проверяем Redis
        block_key = self._get_block_key(user_id)
        blocked_until = await redis.get(block_key)
        
        if blocked_until:
            blocked_until_ts = float(blocked_until)
            if time.time() < blocked_until_ts:
                # Пользователь заблокирован, обновляем кэш
                self._blocked_users[user_id] = blocked_until_ts
                return True
            else:
                # Блокировка истекла, удаляем из Redis
                await redis.delete(block_key)
        
        return False
    
    async def _block_user(self, redis, user_id: int) -> None:
        """Заблокировать пользователя."""
        block_until = time.time() + self.block_duration
        block_key = self._get_block_key(user_id)
        
        # Сохраняем в Redis
        await redis.set(block_key, block_until, expire=self.block_duration)
        
        # Обновляем локальный кэш
        self._blocked_users[user_id] = block_until
        
        logger.warning(f"Пользователь {user_id} заблокирован на {self.block_duration} секунд")
    
    async def _cleanup_cache(self) -> None:
        """Очистить устаревшие записи из локального кэша."""
        current_time = time.time()
        if current_time - self._last_cache_cleanup < self._cache_cleanup_interval:
            return
        
        expired_users = [
            user_id for user_id, blocked_until in self._blocked_users.items()
            if current_time >= blocked_until
        ]
        
        for user_id in expired_users:
            del self._blocked_users[user_id]
        
        self._last_cache_cleanup = current_time
        logger.debug(f"Очищен кэш блокировок, удалено {len(expired_users)} записей")
    
    async def _fixed_window_strategy(self, redis, user_id: int, limit: int) -> bool:
        """Стратегия фиксированного окна."""
        key = self._get_rate_limit_key(user_id, "fixed_window")
        
        # Получаем текущее количество запросов
        current_count = await redis.get(key)
        count = int(current_count) if current_count else 0
        
        if count >= limit:
            return False
        
        # Увеличиваем счетчик
        await redis.incr(key)
        await redis.expire(key, self.interval)
        
        return True
    
    async def _sliding_window_strategy(self, redis, user_id: int, limit: int) -> bool:
        """Стратегия скользящего окна."""
        key = self._get_rate_limit_key(user_id, "sliding_window")
        current_time = time.time()
        window_start = current_time - self.interval
        
        # Используем Redis sorted set для хранения timestamp'ов
        pipe = redis.pipeline()
        
        # Удаляем старые записи
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Добавляем текущий timestamp
        pipe.zadd(key, {str(current_time): current_time})
        
        # Получаем количество записей в окне
        pipe.zcard(key)
        
        # Устанавливаем TTL
        pipe.expire(key, self.interval)
        
        results = await pipe.execute()
        count = results[2]  # Результат zcard
        
        return count <= limit
    
    async def _token_bucket_strategy(self, redis, user_id: int, limit: int) -> bool:
        """Стратегия ведра токенов."""
        bucket_key = self._get_rate_limit_key(user_id, "token_bucket")
        current_time = time.time()
        
        # Получаем текущее состояние ведра
        bucket_data = await redis.hgetall(bucket_key)
        
        if not bucket_data:
            # Создаем новое ведро
            tokens = limit
            last_refill = current_time
        else:
            tokens = int(bucket_data.get("tokens", 0))
            last_refill = float(bucket_data.get("last_refill", current_time))
        
        # Вычисляем, сколько токенов нужно добавить
        time_passed = current_time - last_refill
        tokens_to_add = int(time_passed * limit / self.interval)
        
        if tokens_to_add > 0:
            tokens = min(limit, tokens + tokens_to_add)
            last_refill = current_time
        
        if tokens <= 0:
            return False
        
        # Используем токен
        tokens -= 1
        
        # Сохраняем состояние ведра
        pipe = redis.pipeline()
        pipe.hset(bucket_key, "tokens", tokens)
        pipe.hset(bucket_key, "last_refill", last_refill)
        pipe.expire(bucket_key, self.interval * 2)  # TTL в 2 раза больше интервала
        await pipe.execute()
        
        return True
    
    async def _check_rate_limit(self, redis, user_id: int, is_admin: bool) -> bool:
        """Проверить rate limit для пользователя."""
        limit = self.admin_limit if is_admin else self.user_limit
        
        if self.strategy == "fixed_window":
            return await self._fixed_window_strategy(redis, user_id, limit)
        elif self.strategy == "sliding_window":
            return await self._sliding_window_strategy(redis, user_id, limit)
        elif self.strategy == "token_bucket":
            return await self._token_bucket_strategy(redis, user_id, limit)
        else:
            raise ValueError(f"Неизвестная стратегия: {self.strategy}")
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка middleware."""
        try:
            # Получаем ID пользователя
            user_id = self._get_user_id(event)
            if not user_id:
                return await handler(event, data)
            
            # Получаем список админов из data
            admin_ids = data.get("admin_ids", [])
            is_admin = self._is_admin(user_id, admin_ids)
            
            # Очищаем кэш при необходимости
            await self._cleanup_cache()
            
            # Получаем Redis сервис
            redis_service = await get_redis_service()
            
            # Проверяем, не заблокирован ли пользователь
            if await self._is_user_blocked(redis_service.redis, user_id):
                logger.warning(f"Заблокированный пользователь {user_id} попытался отправить сообщение")
                return  # Блокируем обработку
            
            # Проверяем rate limit
            if not await self._check_rate_limit(redis_service.redis, user_id, is_admin):
                # Превышен лимит, блокируем пользователя
                await self._block_user(redis_service.redis, user_id)
                
                # Отправляем предупреждение админу
                if event.message:
                    try:
                        await event.message.answer(
                            f"⚠️ <b>Rate limit превышен!</b>\n\n"
                            f"Вы отправляете сообщения слишком часто.\n"
                            f"Блокировка на {self.block_duration // 60} минут.\n\n"
                            f"Лимит: {self.admin_limit if is_admin else self.user_limit} сообщений в {self.interval} секунд"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки сообщения о блокировке: {e}")
                
                logger.warning(
                    f"Rate limit превышен для пользователя {user_id} "
                    f"(admin: {is_admin}, limit: {self.admin_limit if is_admin else self.user_limit})"
                )
                return  # Блокируем обработку
            
            # Rate limit не превышен, продолжаем обработку
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Ошибка в RedisRateLimitMiddleware: {e}")
            # В случае ошибки пропускаем middleware и продолжаем обработку
            return await handler(event, data)
