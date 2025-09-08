import time
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 1, interval: float = 2.0):
        self.limit = limit
        self.interval = interval
        self.users = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()
        history = self.users.get(user_id, [])
        history = [t for t in history if now - t < self.interval]
        history.append(now)
        self.users[user_id] = history

        if len(history) > self.limit:
            return await event.answer("⏳ Слишком часто пишешь, притормози.")
        return await handler(event, data)
