"""
Команды для работы с каналами
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.channels import ChannelService
from app.services.channels_admin import ChannelsAdminService
from app.services.moderation import ModerationService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)

# Создаем роутер для команд каналов
channels_router = Router()


@channels_router.message(Command("channels"))
async def handle_channels_command(
    message: Message,
    channel_service: ChannelService,
    channels_admin_service: ChannelsAdminService,
    admin_id: int,
) -> None:
    """Показать список каналов."""
    try:
        if not message.from_user:
            return
        logger.info(f"Channels command from {sanitize_for_logging(str(message.from_user.id))}")

        channels_text = await channels_admin_service.get_channels_list()
        await message.answer(channels_text)
        logger.info(f"Channels list sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in channels command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка каналов")


@channels_router.message(Command("sync_channels"))
async def handle_sync_channels_command(
    message: Message,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Синхронизация статуса каналов."""
    try:
        if not message.from_user:
            return
        logger.info(f"Sync channels command from {sanitize_for_logging(str(message.from_user.id))}")

        # Показываем сообщение о начале синхронизации
        await message.answer("🔄 Синхронизация статуса каналов...")

        # Синхронизируем все каналы
        updated_count = await channel_service.sync_all_channels_native_status()

        if updated_count > 0:
            await message.answer(f"✅ Синхронизация завершена! Обновлено каналов: {updated_count}")
        else:
            await message.answer("✅ Синхронизация завершена! Изменений не требуется.")

        logger.info(f"Sync channels completed: {updated_count} channels updated")

    except Exception as e:
        logger.error(f"Error in sync channels command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка синхронизации каналов")


@channels_router.message(Command("find_chat"))
async def handle_find_chat_command(
    message: Message,
    moderation_service: ModerationService,
    admin_id: int,
) -> None:
    """Найти чат по ID или username."""
    try:
        if not message.from_user:
            return
        logger.info(f"Find chat command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            await message.answer(
                "❌ <b>Использование:</b> /find_chat &lt;chat_id&gt; или /find_chat @username\n\n"
                "💡 <b>Примеры:</b>\n"
                "• /find_chat -1001234567890\n"
                "• /find_chat @channel_username"
            )
            return

        chat_identifier = args[0]
        
        try:
            # Пытаемся получить информацию о чате
            if chat_identifier.startswith("@"):
                # Это username
                chat_info = await moderation_service.bot.get_chat(chat_identifier)
            else:
                # Это ID
                chat_id = int(chat_identifier)
                chat_info = await moderation_service.bot.get_chat(chat_id)
            
            # Формируем ответ
            chat_type = chat_info.type
            title = chat_info.title or "Без названия"
            username = f"@{chat_info.username}" if chat_info.username else "Нет username"
            description = chat_info.description or "Нет описания"
            
            text = f"🔍 <b>Информация о чате</b>\n\n"
            text += f"📝 <b>Название:</b> {title}\n"
            text += f"🆔 <b>ID:</b> <code>{chat_info.id}</code>\n"
            text += f"👤 <b>Username:</b> {username}\n"
            text += f"📋 <b>Тип:</b> {chat_type}\n"
            text += f"📄 <b>Описание:</b> {description[:200]}{'...' if len(description) > 200 else ''}\n"
            
            await message.answer(text)
            logger.info(f"Chat info sent to {sanitize_for_logging(str(message.from_user.id))}")
            
        except Exception as e:
            await message.answer(f"❌ Чат не найден: {sanitize_for_logging(str(e))}")
            logger.error(f"Error finding chat {chat_identifier}: {sanitize_for_logging(str(e))}")

    except Exception as e:
        logger.error(f"Error in find_chat command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка поиска чата")


@channels_router.message(Command("my_chats"))
async def handle_my_chats_command(
    message: Message,
    moderation_service: ModerationService,
    admin_id: int,
) -> None:
    """Показать чаты, где бот является администратором."""
    try:
        if not message.from_user:
            return
        logger.info(f"My chats command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем список чатов, где бот является администратором
        # Это упрощенная реализация - в реальности нужно использовать get_chat_administrators
        text = "📋 <b>Чаты с ботом-администратором</b>\n\n"
        text += "ℹ️ <b>Примечание:</b> Для получения полного списка чатов используйте /channels\n\n"
        text += "💡 <b>Команды для работы с каналами:</b>\n"
        text += "• /channels - список всех каналов\n"
        text += "• /sync_channels - синхронизация статуса каналов\n"
        text += "• /find_chat - найти чат по ID или username"
        
        await message.answer(text)
        logger.info(f"My chats info sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in my_chats command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка чатов")
