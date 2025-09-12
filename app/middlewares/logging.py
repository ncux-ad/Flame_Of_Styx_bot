from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[..., Awaitable[Any]], event: Message, data: Dict[str, Any], **kwargs
    ) -> Any:
        print(f"[LOG] {event.from_user.id}: {event.text}")
        return await handler(event, data)
