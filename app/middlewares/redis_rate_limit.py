"""
Redis Rate Limit Middleware
Middleware для централизованного rate limiting через Redis
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.services.redis_rate_limiter import (
    check_admin_rate_limit,
    check_spam_analysis_rate_limit,
    check_user_rate_limit,
    get_redis_rate_limiter,
)
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class RedisRateLimitMiddleware(BaseMiddleware):
    """Middleware для Redis rate limiting."""

    def __init__(
        self,
        user_limit: int = 10,
        admin_limit: int = 100,
        interval: int = 60,
        strategy: str = "sliding_window",
        block_duration: int = 300,
        redis_service=None,
    ):
        super().__init__()
        self.user_limit = user_limit
        self.admin_limit = admin_limit
        self.interval = interval
        self.strategy = strategy
        self.block_duration = block_duration
        self.redis_service = redis_service

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка rate limiting."""

        # Пропускаем CallbackQuery для упрощения
        if isinstance(event, CallbackQuery):
            return await handler(event, data)

        message = event
        if not isinstance(message, Message) or not message.from_user:
            return await handler(event, data)

        try:
            # Проверяем доступность Redis
            if not self.redis_service or not self.redis_service.is_available():
                # Fallback на локальный rate limiting
                return await self._check_local_rate_limit(message, handler, event, data)

            # Используем Redis rate limiting
            rate_limit_result = await self._check_redis_rate_limit(message)

            if not rate_limit_result["allowed"]:
                logger.warning(
                    f"Redis rate limit exceeded for user {sanitize_for_logging(str(message.from_user.id))} "
                    f"in chat {message.chat.id}"
                )

                # Отправляем сообщение о превышении лимита
                await self._send_rate_limit_message(message, rate_limit_result)
                return  # Блокируем обработку

            # Логируем успешную проверку
            logger.debug(
                f"Redis rate limit check passed for user {sanitize_for_logging(str(message.from_user.id))} "
                f"({rate_limit_result['remaining']} remaining)"
            )

            # Передаем информацию о rate limit в данные
            data["rate_limit_info"] = {
                "remaining": rate_limit_result["remaining"],
                "reset_time": rate_limit_result["reset_time"],
                "strategy": self.strategy,
            }

        except Exception as e:
            logger.error(f"Redis rate limit middleware error: {e}")
            # В случае ошибки разрешаем обработку

        return await handler(event, data)

    async def _check_redis_rate_limit(self, message: Message) -> dict:
        """Проверка rate limit через Redis."""
        user_id = message.from_user.id

        # Определяем тип лимита
        if message.text and message.text.startswith("/"):
            command = message.text.split()[0].lower()

            # Админские команды
            admin_commands = {
                "/status",
                "/settings",
                "/channels",
                "/bots",
                "/suspicious",
                "/unban",
                "/banned",
                "/sync_bans",
                "/force_unban",
                "/sync_channels",
                "/my_chats",
                "/find_chat",
                "/ban_history",
                "/help",
                "/instructions",
            }

            if command in admin_commands:
                limit = self.admin_limit
                key_type = "admin_cmd"
            else:
                limit = self.user_limit
                key_type = "user_msg"
        else:
            limit = self.user_limit
            key_type = "user_msg"

        # Проверяем лимит в Redis
        return await self.redis_service.check_rate_limit(
            user_id=user_id, limit=limit, interval=self.interval, key_type=key_type
        )

    async def _check_local_rate_limit(self, message: Message, handler, event, data):
        """Fallback на локальный rate limiting."""
        logger.info("Using local rate limiting fallback")

        # Создаем простой локальный rate limiter
        from app.middlewares.ratelimit import RateLimitMiddleware

        local_middleware = RateLimitMiddleware(
            user_limit=self.user_limit, admin_limit=self.admin_limit, interval=self.interval
        )

        return await local_middleware(handler, event, data)

    async def _get_rate_limit_for_message(self, message: Message):
        """Определение типа rate limit для сообщения."""

        # Проверяем, является ли это админской командой
        if message.text and message.text.startswith("/"):
            command = message.text.split()[0].lower()

            # Админские команды
            admin_commands = {
                "/status",
                "/settings",
                "/channels",
                "/bots",
                "/suspicious",
                "/unban",
                "/banned",
                "/sync_bans",
                "/force_unban",
                "/sync_channels",
                "/my_chats",
                "/find_chat",
                "/ban_history",
                "/help",
                "/instructions",
            }

            if command in admin_commands:
                return await check_admin_rate_limit(message)

            # Команды анализа спама
            spam_commands = {"/spam_analysis"}
            if command in spam_commands:
                return await check_spam_analysis_rate_limit(message)

        # Обычные сообщения пользователей
        return await check_user_rate_limit(message)

    async def _send_rate_limit_message(self, message: Message, rate_limit_result):
        """Отправка сообщения о превышении rate limit."""
        try:
            retry_after = rate_limit_result.get("retry_after", 60)
            if retry_after:
                retry_after_minutes = int(retry_after / 60)
                retry_after_seconds = int(retry_after % 60)

                if retry_after_minutes > 0:
                    retry_text = f"{retry_after_minutes}м {retry_after_seconds}с"
                else:
                    retry_text = f"{retry_after_seconds}с"

                rate_limit_message = (
                    "⏰ <b>Превышен лимит запросов</b>\n\n"
                    f"Попробуйте снова через {retry_text}\n"
                    "Это защита от спама и перегрузки бота"
                )
            else:
                rate_limit_message = (
                    "⏰ <b>Превышен лимит запросов</b>\n\n" "Попробуйте снова позже\n" "Это защита от спама и перегрузки бота"
                )

            await message.answer(rate_limit_message)

        except Exception as e:
            logger.error(f"Error sending rate limit message: {e}")


class RedisRateLimitAdminMiddleware(BaseMiddleware):
    """Middleware для rate limiting админских команд."""

    def __init__(self):
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка rate limiting для админских команд."""

        if isinstance(event, CallbackQuery):
            return await handler(event, data)

        message = event
        if not isinstance(message, Message) or not message.from_user:
            return await handler(event, data)

        # Проверяем только команды
        if not message.text or not message.text.startswith("/"):
            return await handler(event, data)

        try:
            rate_limit_result = await check_admin_rate_limit(message)

            if not rate_limit_result.allowed:
                logger.warning(f"Admin rate limit exceeded for user {sanitize_for_logging(str(message.from_user.id))}")

                await self._send_admin_rate_limit_message(message, rate_limit_result)
                return

            # Передаем информацию о rate limit
            data["admin_rate_limit_info"] = {
                "remaining": rate_limit_result.remaining,
                "reset_time": rate_limit_result.reset_time,
            }

        except Exception as e:
            logger.error(f"Admin rate limit middleware error: {e}")

        return await handler(event, data)

    async def _send_admin_rate_limit_message(self, message: Message, rate_limit_result):
        """Отправка сообщения о превышении админского rate limit."""
        try:
            if rate_limit_result.retry_after:
                retry_after_minutes = int(rate_limit_result.retry_after / 60)
                retry_after_seconds = int(rate_limit_result.retry_after % 60)

                if retry_after_minutes > 0:
                    retry_text = f"{retry_after_minutes}м {retry_after_seconds}с"
                else:
                    retry_text = f"{retry_after_seconds}с"

                rate_limit_message = (
                    "⏰ <b>Превышен лимит админских команд</b>\n\n"
                    f"Попробуйте снова через {retry_text}\n"
                    "Это защита от перегрузки системы"
                )
            else:
                rate_limit_message = (
                    "⏰ <b>Превышен лимит админских команд</b>\n\n"
                    "Попробуйте снова позже\n"
                    "Это защита от перегрузки системы"
                )

            await message.answer(rate_limit_message)

        except Exception as e:
            logger.error(f"Error sending admin rate limit message: {e}")
