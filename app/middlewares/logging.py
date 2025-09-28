import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.utils.security import hash_user_id, sanitize_for_logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[..., Awaitable[Any]], event: Message, data: Dict[str, Any], **kwargs) -> Any:
        # Enhanced logging with more details
        user_id = getattr(event.from_user, "id", "unknown") if hasattr(event, "from_user") and event.from_user else "unknown"

        # Hash user_id for security
        hashed_user_id = hash_user_id(user_id) if user_id != "unknown" else "unknown"
        
        # Санитизируем текст сообщения для защиты персональных данных
        raw_text = getattr(event, "text", "None") if hasattr(event, "text") else "None"
        text = sanitize_for_logging(raw_text) if raw_text != "None" else "None"
        chat_id = getattr(event.chat, "id", "unknown") if hasattr(event, "chat") and event.chat else "unknown"
        chat_type = getattr(event.chat, "type", "unknown") if hasattr(event, "chat") and event.chat else "unknown"
        sender_chat = getattr(event, "sender_chat", None) if hasattr(event, "sender_chat") else None

        # Получаем название чата для лучшего понимания (санитизированное)
        chat_title = "Unknown"
        if hasattr(event, "chat") and event.chat:
            raw_chat_title = getattr(event.chat, "title", "Unknown")
            if raw_chat_title and raw_chat_title != "Unknown":
                chat_title = sanitize_for_logging(raw_chat_title)
            elif hasattr(event.chat, "username"):
                chat_title = f"@{event.chat.username}"

        # Получаем название канала-отправителя (санитизированное)
        sender_title = "None"
        if sender_chat:
            raw_sender_title = getattr(sender_chat, "title", "Unknown Channel")
            if raw_sender_title and raw_sender_title != "Unknown Channel":
                sender_title = sanitize_for_logging(raw_sender_title)
            elif hasattr(sender_chat, "username"):
                sender_title = f"@{sender_chat.username}"

        logger.info(
            f"[LOG] user_id:{hashed_user_id} chat_id:{chat_id} chat_type:{chat_type} chat_title:'{chat_title}' sender_chat:{sender_chat is not None} sender_title:'{sender_title}' text:{text}"
        )
        print(
            f"[LOG] user_id:{hashed_user_id} chat_id:{chat_id} chat_type:{chat_type} chat_title:'{chat_title}' sender_chat:{sender_chat is not None} sender_title:'{sender_title}' text:{text}"
        )

        return await handler(event, data)
