"""Rate limiting middleware for aiogram with different limits for admins and users."""

import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

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
        event: TelegramObject,
        data: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """Check rate limit before processing."""
        # Get user ID from different event types
        user_id = self._get_user_id(event)
        
        if not user_id:
            return await handler(event, data)

        # Determine if user is admin and set appropriate limit
        is_admin = user_id in self.config.admin_ids_list
        limit = self.admin_limit if is_admin else self.user_limit

        # Check rate limit using monotonic time for accuracy
        current_time = time.monotonic()

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
            user_type = "админ" if is_admin else "пользователь"
            remaining_time = self.interval - (current_time - self.requests[user_id][0])
            
            # Try to send rate limit message for different event types
            if isinstance(event, Message):
                await event.answer(
                    f"⏰ <b>Rate Limit превышен!</b>\n\n"
                    f"👤 Тип: {user_type}\n"
                    f"📊 Лимит: {limit} запросов в {self.interval} секунд\n"
                    f"⏳ Попробуйте через {int(remaining_time)} секунд",
                    reply_to_message_id=event.message_id,
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    f"⏰ Rate Limit превышен! Попробуйте через {int(remaining_time)} секунд",
                    show_alert=True
                )
            # For other event types (channel_post, edited_message), just log
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Rate limit exceeded for {user_type} {user_id}: "
                    f"{len(self.requests[user_id])}/{limit} requests in {self.interval}s"
                )
            return

        # Add current request
        self.requests[user_id].append(current_time)

        # Process request
        return await handler(event, data)

    def _get_user_id(self, event: TelegramObject) -> int | None:
        """Extract user ID from different event types."""
        if isinstance(event, Message):
            # Для канальных сообщений используем sender_chat.id, иначе from_user.id
            if event.sender_chat:
                return event.sender_chat.id
            else:
                return event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            return event.from_user.id if event.from_user else None
        else:
            # For other event types (channel_post, edited_message, etc.)
            # Try to get from_user if available
            if hasattr(event, 'from_user') and event.from_user:
                return event.from_user.id
            # For channel posts, try sender_chat
            if hasattr(event, 'sender_chat') and event.sender_chat:
                return event.sender_chat.id
            return None
