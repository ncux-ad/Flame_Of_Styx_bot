"""
Упрощенный антиспам роутер - перехватывает ВСЕ сообщения
"""

import logging

from aiogram import Router
from aiogram.types import Message

from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)

# Create router
antispam_router = Router()


@antispam_router.edited_message()
async def handle_edited_messages(
    message: Message,
    moderation_service: ModerationService,
    link_service: LinkService,
    profile_service: ProfileService,
    channel_service: ChannelService,
    bot_service: BotService,
    admin_id: int,
) -> None:
    """
    Обрабатывает ОТРЕДАКТИРОВАННЫЕ сообщения - критично для антиспама!
    Спамер может отредактировать сообщение и добавить ссылку после постинга.
    """
    try:
        if not message.text:
            return
        logger.info(f"Edited message processing: {message.text[:50]}...")

        # НЕ пропускаем отредактированные сообщения с командами!
        # Спамеры могут отредактировать команду и добавить бот-ссылку

        # Проверяем на бот-ссылки и подозрительный контент
        results = await link_service.check_message_for_bot_links(message)

        if results:
            logger.warning(f"EDITED MESSAGE SPAM DETECTED: {results}")

            # Обрабатываем как спам (как в channels.py)
            await link_service.handle_bot_link_detection(message, results)
        else:
            logger.info("Edited message passed antispam checks")

    except Exception as e:
        logger.error(f"Error processing edited message: {e}")


@antispam_router.channel_post()
async def handle_channel_posts(
    message: Message,
    moderation_service: ModerationService,
    link_service: LinkService,
    profile_service: ProfileService,
    channel_service: ChannelService,
    bot_service: BotService,
    admin_id: int,
) -> None:
    """
    Обрабатывает посты в каналах (нативные посты канала).
    """
    try:
        logger.info(f"Channel post processing: {message.text[:50] if message.text else 'Media'}...")

        # Проверяем на бот-ссылки и подозрительный контент
        results = await link_service.check_message_for_bot_links(message)

        if results:
            logger.warning(f"CHANNEL POST SPAM DETECTED: {results}")

            # Обрабатываем как спам (как в channels.py)
            await link_service.handle_bot_link_detection(message, results)
        else:
            logger.info("Channel post passed antispam checks")

    except Exception as e:
        logger.error(f"Error processing channel post: {e}")


@antispam_router.message()
async def handle_all_messages(
    message: Message,
    moderation_service: ModerationService,
    link_service: LinkService,
    profile_service: ProfileService,
    channel_service: ChannelService,
    bot_service: BotService,
    admin_id: int,
) -> None:
    """
    Обрабатывает ВСЕ сообщения - основной антиспам фильтр.

    Args:
        message: Сообщение от пользователя
        moderation_service: Сервис модерации
        link_service: Сервис проверки ссылок
        profile_service: Сервис профилей
        channel_service: Сервис каналов
        bot_service: Сервис ботов
        admin_id: ID администратора
    """
    try:
        # Пропускаем команды - они обрабатываются админ-роутером
        if message.text and message.text.startswith("/"):
            logger.info(f"Command message skipped by antispam: {sanitize_for_logging(message.text)}")
            return

        # Сохраняем информацию о канале, если сообщение от канала
        if message.sender_chat or message.chat.type in ["channel", "supergroup"]:
            await channel_service.save_channel_info(message.chat, message.sender_chat)

        logger.info(
            f"Anti-spam processing: user_id={message.from_user.id if message.from_user else 'unknown'}, "
            f"chat_id={message.chat.id}, text='{sanitize_for_logging(message.text[:50]) if message.text else 'None'}'"
        )

        # Определяем тип чата
        chat_type = message.chat.type
        is_channel_message = chat_type in ["channel", "supergroup"]

        # Для каналов и супергрупп - проверяем антиспам
        if is_channel_message:
            await handle_channel_antispam(
                message,
                moderation_service,
                link_service,
                channel_service,
                profile_service,
                admin_id,
            )
        else:
            # Для личных сообщений - только rate limiting (уже обработан в middleware)
            if message.from_user:
                logger.info(f"Private message from {message.from_user.id}: {sanitize_for_logging(message.text) if message.text else 'None'}")

    except Exception as e:
        logger.error(f"Error in anti-spam handler: {e}")


async def handle_channel_antispam(
    message: Message,
    moderation_service: ModerationService,
    link_service: LinkService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Обрабатывает антиспам для сообщений в каналах/группах."""
    try:
        # Определяем ID канала
        channel_id = message.sender_chat.id if message.sender_chat else message.chat.id

        # Логируем детали сообщения для отладки
        logger.info(
            f"Channel antispam debug: chat_id={message.chat.id}, sender_chat={message.sender_chat.id if message.sender_chat else None}, channel_id={channel_id}"
        )

        # Проверяем, является ли это нативным каналом (где бот админ)
        is_native_channel = await channel_service.is_native_channel(channel_id)

        logger.info(f"Channel antispam: channel_id={channel_id}, is_native={is_native_channel}")

        # Проверяем на бот-ссылки и подозрительный контент
        bot_links = await link_service.check_message_for_bot_links(message)

        if bot_links:
            logger.warning(f"Bot links detected: {bot_links}")

            # Обрабатываем обнаружение бот-ссылок
            await link_service.handle_bot_link_detection(message, bot_links)

            # Помечаем канал как подозрительный
            await channel_service.mark_channel_as_suspicious(
                channel_id=channel_id, reason="Bot links detected in channel", admin_id=admin_id
            )

            logger.info(f"Message deleted and user banned due to bot links: {bot_links}")
        else:
            logger.info("No bot links detected, message allowed")

            # Если нет бот-ссылок, но есть отправитель - анализируем его профиль
            if message.from_user:
                try:
                    suspicious_profile = await profile_service.analyze_user_profile(user=message.from_user, admin_id=admin_id)
                    if suspicious_profile:
                        logger.warning(
                            f"Suspicious profile detected in channel: user_id={message.from_user.id}, score={suspicious_profile.suspicion_score}"
                        )
                except Exception as e:
                    logger.error(f"Error analyzing user profile in channel: {e}")

    except Exception as e:
        logger.error(f"Error in channel antispam: {e}")
