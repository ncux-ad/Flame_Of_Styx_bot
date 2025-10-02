"""
Middleware для тихого логирования в каналах и группах.
Отправляет ответы только в личных сообщениях.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class SilentLoggingMiddleware(BaseMiddleware):
    """
    Middleware для тихого логирования в каналах и группах.

    Отправляет ответы только в личных сообщениях (private).
    В каналах и группах только логирует события.
    """

    async def __call__(
        self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие с тихим логированием.

        Args:
            handler: Следующий обработчик
            event: Telegram событие
            data: Данные события
        """
        # Определяем тип чата
        chat_type = None
        chat_id = None

        if isinstance(event, Message):
            chat_type = event.chat.type
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_type = event.message.chat.type
            chat_id = event.message.chat.id

        # Логируем событие
        if chat_type and chat_id:
            if chat_type == "private":
                logger.debug(f"Личное сообщение: {chat_type} {chat_id}")
            else:
                logger.info(f"Тихое логирование: {chat_type} {chat_id}")

        # Вызываем следующий обработчик
        return await handler(event, data)


def should_send_response(event: TelegramObject) -> bool:
    """
    Определяет, нужно ли отправлять ответ пользователю.

    Args:
        event: Telegram событие

    Returns:
        True если нужно отправлять ответ, False иначе
    """
    if isinstance(event, Message):
        return event.chat.type == "private"
    elif isinstance(event, CallbackQuery) and event.message:
        return event.message.chat.type == "private"

    return False


async def send_silent_response(event: TelegramObject, message: str) -> None:
    """
    Отправляет ответ с учетом тихого логирования.

    Args:
        event: Telegram событие
        message: Сообщение для отправки
    """
    if not should_send_response(event):
        # В каналах и группах только логируем
        if isinstance(event, Message):
            logger.info(f"Тихое логирование: {message} в {event.chat.type} {event.chat.id}")
        elif isinstance(event, CallbackQuery) and event.message:
            logger.info(f"Тихое логирование: {message} в {event.message.chat.type} {event.message.chat.id}")
        return

    # В личных сообщениях отправляем ответ
    try:
        if isinstance(event, Message):
            await event.answer(message)
        elif isinstance(event, CallbackQuery):
            await event.answer(message)
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}")


async def send_silent_callback_answer(event: CallbackQuery, text: str = None, show_alert: bool = False) -> None:
    """
    Отправляет ответ на callback query с учетом тихого логирования.

    Args:
        event: CallbackQuery событие
        text: Текст ответа
        show_alert: Показывать ли alert
    """
    if not should_send_response(event):
        # В каналах и группах только логируем
        if event.message:
            logger.info(f"Тихое логирование callback: {text} в {event.message.chat.type} {event.message.chat.id}")
        return

    # В личных сообщениях отправляем ответ
    try:
        await event.answer(text, show_alert=show_alert)
    except Exception as e:
        logger.error(f"Ошибка отправки callback ответа: {e}")
