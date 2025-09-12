"""Rate limiting middleware for aiogram with different limits for admins and users."""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.config import load_config


class RateLimitMiddleware(BaseMiddleware):
    """Middleware for rate limiting with different limits for admins and users."""

    def __init__(self, user_limit: int = 10, admin_limit: int = 100, interval: int = 60):
        """Initialize rate limiter.

        Args:
            user_limit: Maximum number of requests per interval for regular users
            admin_limit: Maximum number of requests per interval for admins
            interval: Time interval in seconds
        """
        self.user_limit = user_limit
        self.admin_limit = admin_limit
        self.interval = interval
        self.requests = {}  # user_id -> [timestamps]
        self.config = load_config()

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """Check rate limit before processing."""
        # Get user ID
        if isinstance(event, Message):
            # Для канальных сообщений используем sender_chat.id, иначе from_user.id
            if event.sender_chat:
                user_id = event.sender_chat.id
            else:
                user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        else:
            return await handler(event, data)

        if not user_id:
            return await handler(event, data)

        # Determine if user is admin and set appropriate limit
        is_admin = user_id in self.config.admin_ids_list
        limit = self.admin_limit if is_admin else self.user_limit

        # Check rate limit
        current_time = time.time()

        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time
                for req_time in self.requests[user_id]
                if current_time - req_time < self.interval
            ]
        else:
            self.requests[user_id] = []

        # Check if limit exceeded
        if len(self.requests[user_id]) >= limit:
            # Rate limit exceeded
            if isinstance(event, Message):
                user_type = "админ" if is_admin else "пользователь"
                remaining_time = self.interval - (current_time - self.requests[user_id][0])
                await event.answer(
                    f"⏰ <b>Rate Limit превышен!</b>\n\n"
                    f"👤 Тип: {user_type}\n"
                    f"📊 Лимит: {limit} запросов в {self.interval} секунд\n"
                    f"⏳ Попробуйте через {int(remaining_time)} секунд",
                    reply_to_message_id=event.message_id,
                )
            return

        # Add current request
        self.requests[user_id].append(current_time)

        # Process request
        return await handler(event, data)
