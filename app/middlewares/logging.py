import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[..., Awaitable[Any]], event: Message, data: Dict[str, Any], **kwargs
    ) -> Any:
        # Enhanced logging with more details
        user_id = (
            getattr(event.from_user, "id", "unknown")
            if hasattr(event, "from_user") and event.from_user
            else "unknown"
        )
        text = getattr(event, "text", "None") if hasattr(event, "text") else "None"
        chat_id = (
            getattr(event.chat, "id", "unknown")
            if hasattr(event, "chat") and event.chat
            else "unknown"
        )
        chat_type = (
            getattr(event.chat, "type", "unknown")
            if hasattr(event, "chat") and event.chat
            else "unknown"
        )
        sender_chat = getattr(event, "sender_chat", None) if hasattr(event, "sender_chat") else None

        # Получаем название чата для лучшего понимания
        chat_title = "Unknown"
        if hasattr(event, "chat") and event.chat:
            chat_title = getattr(event.chat, "title", "Unknown")
            if not chat_title and hasattr(event.chat, "username"):
                chat_title = f"@{event.chat.username}"

        # Получаем название канала-отправителя
        sender_title = "None"
        if sender_chat:
            sender_title = getattr(sender_chat, "title", "Unknown Channel")
            if not sender_title and hasattr(sender_chat, "username"):
                sender_title = f"@{sender_chat.username}"

        logger.info(
            f"[LOG] user_id:{user_id} chat_id:{chat_id} chat_type:{chat_type} chat_title:'{chat_title}' sender_chat:{sender_chat is not None} sender_title:'{sender_title}' text:{text}"
        )
        print(
            f"[LOG] user_id:{user_id} chat_id:{chat_id} chat_type:{chat_type} chat_title:'{chat_title}' sender_chat:{sender_chat is not None} sender_title:'{sender_title}' text:{text}"
        )

        return await handler(event, data)
