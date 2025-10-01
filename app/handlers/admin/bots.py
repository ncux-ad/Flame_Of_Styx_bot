"""
Команды для управления ботами
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.bots_admin import BotsAdminService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging
from app.middlewares.silent_logging import send_silent_response
from app.filters.is_admin_or_silent import IsAdminOrSilentFilter

logger = logging.getLogger(__name__)

# Создаем роутер для команд ботов
bots_router = Router()

# Добавляем общий хендлер для отладки
@bots_router.message()
async def bots_router_debug_handler(message: Message) -> None:
    """Debug handler для логирования всех сообщений в bots router."""
    logger.info(f"BOTS ROUTER DEBUG: Received message: {sanitize_for_logging(message.text)}")
    logger.info(f"BOTS ROUTER DEBUG: Message type: {type(message)}")
    logger.info(f"BOTS ROUTER DEBUG: Chat type: {message.chat.type}")
    logger.info(f"BOTS ROUTER DEBUG: From user: {message.from_user.id if message.from_user else None}")


@bots_router.message(Command("test_bots"), IsAdminOrSilentFilter())
async def handle_test_bots_command(message: Message) -> None:
    """Тестовый хендлер для проверки роутинга."""
    logger.info("TEST BOTS COMMAND HANDLER CALLED!")
    await message.answer("✅ Bots router работает!")


@bots_router.message(Command("bots"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /bots")
async def handle_bots_command(
    message: Message,
    bots_admin_service: BotsAdminService,
    admin_id: int,
) -> None:
    """Показать список ботов и управление whitelist."""
    try:
        logger.info(f"BOTS COMMAND HANDLER CALLED: {message.text}")
        if not message.from_user:
            logger.warning("Bots command: no from_user")
            return
        
        logger.info(f"Bots command from {sanitize_for_logging(str(message.from_user.id))}")
        logger.info(f"Bots admin service: {bots_admin_service}")
        logger.info(f"Admin ID: {admin_id}")

        bots_text = await bots_admin_service.get_bots_list()
        logger.info(f"Bots text length: {len(bots_text)}")
        
        await send_silent_response(message, bots_text)
        logger.info(f"Bots list sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in bots command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения списка ботов")


@bots_router.message(Command("add_bot"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /add_bot")
async def handle_add_bot_command(
    message: Message,
    bots_admin_service: BotsAdminService,
    admin_id: int,
) -> None:
    """Добавить бота в whitelist."""
    try:
        if not message.from_user:
            return
        logger.info(f"Add bot command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await send_silent_response(message, "❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            await send_silent_response(
                message,
                "❌ <b>Использование:</b> /add_bot &lt;bot_username&gt;\n\n"
                "💡 <b>Примеры:</b>\n"
                "• /add_bot @mybot\n"
                "• /add_bot mybot"
            )
            return

        bot_username = args[0].lstrip("@")
        result = await bots_admin_service.add_bot_to_whitelist(bot_username, admin_id)
        await send_silent_response(message, result)
        logger.info(f"Add bot result sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in add_bot command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка добавления бота")


@bots_router.message(Command("remove_bot"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /remove_bot")
async def handle_remove_bot_command(
    message: Message,
    bots_admin_service: BotsAdminService,
    admin_id: int,
) -> None:
    """Удалить бота из whitelist."""
    try:
        if not message.from_user:
            return
        logger.info(f"Remove bot command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await send_silent_response(message, "❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            await send_silent_response(
                message,
                "❌ <b>Использование:</b> /remove_bot &lt;bot_username&gt;\n\n"
                "💡 <b>Примеры:</b>\n"
                "• /remove_bot @mybot\n"
                "• /remove_bot mybot"
            )
            return

        bot_username = args[0].lstrip("@")
        result = await bots_admin_service.remove_bot_from_whitelist(bot_username, admin_id)
        await send_silent_response(message, result)
        logger.info(f"Remove bot result sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in remove_bot command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка удаления бота")
