"""Channel message handlers."""

import logging

from aiogram import Router
from aiogram.filters import BaseFilter

from aiogram.types import Message

from app.services.channels import ChannelService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import safe_format_message, sanitize_for_logging

# DI will inject services automatically

logger = logging.getLogger(__name__)


class ChannelFilter(BaseFilter):
    """Filter for channel and supergroup messages only."""
    
    async def __call__(self, message: Message) -> bool:
        """Check if message is from channel or supergroup."""
        return message.chat.type in ["channel", "supergroup"]


# Create router
channel_router = Router()


@channel_router.message(ChannelFilter())
async def handle_channel_message(
    message: Message,
    channel_service: ChannelService,
    link_service: LinkService,
    profile_service: ProfileService,
    moderation_service: ModerationService,
    admin_id: int,
) -> None:
    """Handle messages from channels and channel comment groups."""
    try:
        # Debug logging
        logger.info(f"Channel handler: sender_chat={message.sender_chat}, chat_type={message.chat.type}")
        logger.info(
            f"handle_channel_message called: from_user={message.from_user}, is_bot={message.from_user.is_bot if message.from_user else None}"
        )

        # Handle messages from channels (sender_chat) or channel comment groups (supergroup)
        # Filter already ensures we only get channel/supergroup messages

        # Skip if message is from bot (but allow channel messages)
        if message.from_user and message.from_user.is_bot and not message.sender_chat:
            return

        # Determine channel ID for checking
        channel_id = message.sender_chat.id if message.sender_chat else message.chat.id

        # Логируем детали для отладки
        logger.info(
            f"Channel handler debug: chat_id={message.chat.id}, sender_chat={message.sender_chat.id if message.sender_chat else None}, channel_id={channel_id}"
        )

        # Save channel information to database
        await channel_service.save_channel_info(message.chat, message.sender_chat)

        # Check if this is the native channel (where bot is connected)
        is_native_channel = await channel_service.is_native_channel(channel_id)
        logger.info(f"Channel check: channel_id={channel_id}, is_native={is_native_channel}")

        if is_native_channel:
            # Native channel - check for spam but allow more freedom
            logger.info("Processing as native channel message")
            await _handle_native_channel_message(
                message,
                channel_service,
                link_service,
                profile_service,
                moderation_service,
                admin_id,
            )
        else:
            # Foreign channel - check for spam and rate limiting
            logger.info("Processing as foreign channel message")
            await _handle_foreign_channel_message(
                message,
                channel_service,
                link_service,
                profile_service,
                moderation_service,
                admin_id,
            )

    except Exception as e:
        logger.error(safe_format_message("Error handling channel message: {error}", error=sanitize_for_logging(e)))


async def _handle_native_channel_message(
    message: Message,
    channel_service: ChannelService,
    link_service: LinkService,
    profile_service: ProfileService,
    moderation_service: ModerationService,
    admin_id: int,
) -> None:
    """Handle messages from native channel with basic spam checking."""
    try:
        logger.info(f"Native channel message: {sanitize_for_logging(message.text) if message.text else 'None'}")

        # Check for bot links in message
        bot_links = await link_service.check_message_for_bot_links(message)
        logger.info(f"Bot links found: {bot_links}")

        if bot_links:
            # Handle bot link detection
            logger.info("Handling bot link detection in native channel")
            await link_service.handle_bot_link_detection(message, bot_links)
            return

        # Check for rate limiting (more lenient for native channel)
        channel_id = message.sender_chat.id if message.sender_chat else message.chat.id
        is_rate_limited = await channel_service.check_channel_rate_limit(channel_id=channel_id)
        if is_rate_limited:
            # Just log, don't block native channel
            logger.warning(f"Rate limit exceeded in native channel {channel_id}")
            return

        # Handle normal channel message
        await channel_service.handle_channel_message(message, admin_id)

    except Exception as e:
        logger.error(safe_format_message("Error handling native channel message: {error}", error=sanitize_for_logging(e)))


async def _handle_foreign_channel_message(
    message: Message,
    channel_service: ChannelService,
    link_service: LinkService,
    profile_service: ProfileService,
    moderation_service: ModerationService,
    admin_id: int,
) -> None:
    """Handle messages from foreign channels with spam checking."""
    try:
        logger.info(f"Foreign channel message: {message.text}")

        # Determine channel ID
        channel_id = message.sender_chat.id if message.sender_chat else message.chat.id

        # Check for bot links and suspicious content in message
        bot_links = await link_service.check_message_for_bot_links(message)
        logger.info(f"Bot links found in foreign channel: {bot_links}")

        # Check for suspicious media content
        suspicious_media = [
            link for link in bot_links if link[0] in ["suspicious_media", "forwarded_media", "media_without_caption"]
        ]
        if suspicious_media:
            logger.warning(f"Suspicious media content detected: {suspicious_media}")

        if bot_links:
            # Handle bot link detection
            logger.info("Handling bot link detection in foreign channel")
            await link_service.handle_bot_link_detection(message, bot_links)

            # Mark channel as suspicious
            await channel_service.mark_channel_as_suspicious(
                channel_id=channel_id,
                reason="Bot links detected in foreign channel",
                admin_id=admin_id,
            )
            return

        # Check for rate limiting
        is_rate_limited = await channel_service.check_channel_rate_limit(channel_id=channel_id)
        if is_rate_limited:
            # Block channel for too frequent messages
            await channel_service.block_channel(channel_id=channel_id, reason="Rate limit exceeded", admin_id=admin_id)
            return

        # If passed all checks, handle as normal channel
        await channel_service.handle_channel_message(message, admin_id)

    except Exception as e:
        logger.error(safe_format_message("Error handling foreign channel message: {error}", error=sanitize_for_logging(e)))


@channel_router.my_chat_member(ChannelFilter())
async def handle_channel_member_update(update, channel_service: ChannelService, admin_id: int) -> None:
    """Handle channel member updates."""
    try:
        # Log the event
        logger.info(
            safe_format_message(
                "Channel member update: chat_id={chat_id}, chat_type={chat_type}, old_status={old_status}, new_status={new_status}",
                chat_id=sanitize_for_logging(update.chat.id if hasattr(update, "chat") and update.chat else "unknown"),
                chat_type=sanitize_for_logging(update.chat.type if hasattr(update, "chat") and update.chat else "unknown"),
                old_status=sanitize_for_logging(
                    update.old_chat_member.status
                    if hasattr(update, "old_chat_member") and update.old_chat_member
                    else "unknown"
                ),
                new_status=sanitize_for_logging(
                    update.new_chat_member.status
                    if hasattr(update, "new_chat_member") and update.new_chat_member
                    else "unknown"
                ),
            )
        )

        # Check if bot was added to a channel
        if (
            hasattr(update, "new_chat_member")
            and hasattr(update, "old_chat_member")
            and update.new_chat_member
            and update.old_chat_member
        ):

            # Bot was added (was not member, now is member)
            if update.old_chat_member.status == "left" and update.new_chat_member.status in ["member", "administrator"]:

                # Save channel information to database
                if hasattr(update, "chat") and update.chat:
                    await channel_service.save_channel_info(update.chat, None)

                    # Notify admin about bot being added to channel (always)
                    await _notify_admin_bot_added(update, admin_id)

            # Bot was removed (was member, now left)
            elif update.old_chat_member.status in ["member", "administrator"] and update.new_chat_member.status == "left":

                # Notify admin about bot being removed (always)
                await _notify_admin_bot_removed(update, admin_id)

    except Exception as e:
        logger.error(safe_format_message("Error handling channel member update: {error}", error=sanitize_for_logging(e)))


async def _notify_admin_bot_added(update, admin_id: int) -> None:
    """Notify admin that bot was added to a channel."""
    try:
        chat = update.chat
        # bot_username = update.bot.username or "your_bot"  # Не используется

        # Determine chat type for appropriate message
        if chat.type == "channel":
            chat_type_name = "канал"
            chat_emoji = "📢"
        elif chat.type == "supergroup":
            chat_type_name = "группу комментариев"
            chat_emoji = "💬"
        else:
            chat_type_name = "чат"
            chat_emoji = "💬"

        channel_info = (
            f"🤖 <b>Бот добавлен в {chat_type_name}!</b>\n\n"
            f"{chat_emoji} <b>{chat_type_name.title()}:</b> {chat.title or 'Без названия'}\n"
            f"🆔 <b>ID:</b> <code>{chat.id}</code>\n"
        )

        if hasattr(chat, "username") and chat.username:
            channel_info += f"👤 <b>Username:</b> @{chat.username}\n"

        channel_info += (
            f"👥 <b>Тип:</b> {chat.type}\n"
            f"⏰ <b>Время:</b> {update.date.strftime('%d.%m.%Y %H:%M')}\n\n"
            "✅ <b>Бот готов к работе!</b>\n"
            "🔍 Антиспам мониторинг активирован\n\n"
        )

        # Add instructions only for channels, not comment groups
        if chat.type == "channel":
            channel_info += (
                "📋 <b>Инструкция для админа канала:</b>\n"
                "• Настройте права бота в канале\n"
                '• Включите "Удалять сообщения"\n'
                '• Включите "Блокировать пользователей"\n'
                "• Без этих прав бот не сможет модератировать\n\n"
            )

        channel_info += (
            "💡 <b>Управление:</b>\n"
            "• /channels - просмотр всех каналов\n"
            "• /status - статистика работы бота\n"
            "• /help - справка по командам"
        )

        await update.bot.send_message(chat_id=admin_id, text=channel_info)
        logger.info(f"Notified admin {admin_id} about bot being added to channel {chat.id}")

    except Exception as e:
        logger.error(f"Error notifying admin about bot addition: {e}")


async def _notify_channel_admin_bot_ready(update) -> None:
    """Notify channel admin that bot is ready to work."""
    try:
        chat = update.chat
        bot_info = (
            "🤖 <b>AntiSpam Bot готов к работе!</b>\n\n"
            "✅ <b>Активированы функции:</b>\n"
            "• Защита от спама\n"
            "• Анализ подозрительных профилей\n"
            "• Автоматическая модерация\n"
            "• Мониторинг бот-ссылок\n\n"
            "🔧 <b>Управление:</b>\n"
            "• Используйте команды в личных сообщениях с ботом\n"
            "• /help - справка по командам\n"
            "• /status - статистика работы\n\n"
            "🛡️ <b>Безопасность:</b>\n"
            "Бот работает автоматически и не требует дополнительных настроек"
        )

        # Try to send message to channel
        await update.bot.send_message(chat_id=chat.id, text=bot_info)
        logger.info(f"Notified channel {chat.id} that bot is ready")

        # Send detailed setup instructions to channel admin
        await _send_setup_instructions(update)

    except Exception as e:
        logger.error(f"Error notifying channel about bot readiness: {e}")


async def _send_setup_instructions(update) -> None:
    """Send detailed setup instructions to channel admin."""
    try:
        chat = update.chat

        # Get bot username for instructions
        # bot_username = update.bot.username or "your_bot"  # Не используется

        setup_instructions = (
            "📋 <b>НАСТРОЙКА ПРАВ ДЛЯ БОТА</b>\n\n"
            "🤖 <b>AntiSpam Bot добавлен в ваш канал!</b>\n"
            "Для полноценной работы боту нужны определенные права.\n\n"
            "🔧 <b>ОБЯЗАТЕЛЬНЫЕ ПРАВА (настройте сейчас):</b>\n\n"
            "1️⃣ <b>Удаление сообщений</b>\n"
            "• Перейдите в настройки канала\n"
            "• Администраторы → @your_bot\n"
            '• Включите "Удалять сообщения"\n'
            "• Без этого бот не сможет удалять спам\n\n"
            "2️⃣ <b>Блокировка пользователей</b>\n"
            '• В настройках бота включите "Добавлять участников"\n'
            '• Или "Исключать участников"\n'
            "• Без этого бот не сможет банить спамеров\n\n"
            "3️⃣ <b>Просмотр сообщений</b>\n"
            "• Убедитесь, что бот может читать сообщения\n"
            "• Это нужно для анализа контента\n\n"
            "✅ <b>ДОПОЛНИТЕЛЬНЫЕ ПРАВА (рекомендуется):</b>\n\n"
            "4️⃣ <b>Приглашение пользователей</b>\n"
            "• Полезно для разбана пользователей\n"
            "• Не обязательно, но удобно\n\n"
            "5️⃣ <b>Закрепление сообщений</b>\n"
            "• Для важных уведомлений\n"
            "• Не обязательно для основной работы\n\n"
            "⚠️ <b>ВАЖНО:</b>\n"
            "• Без прав на удаление и бан бот работать НЕ БУДЕТ!\n"
            "• Настройте права сразу после добавления бота\n"
            "• Бот начнет работать автоматически после настройки\n\n"
            "🔍 <b>Проверка работы:</b>\n"
            "• Отправьте тестовое сообщение с бот-ссылкой\n"
            "• Бот должен удалить его (если права настроены)\n"
            "• Если не удаляет - проверьте права\n\n"
            "📞 <b>Поддержка:</b>\n"
            "• Владелец бота: [@ncux-ad](https://github.com/ncux-ad)\n"
            "• GitHub: https://github.com/ncux-ad/Flame_Of_Styx_bot\n"
            "• При проблемах с настройкой - обращайтесь к владельцу\n\n"
            "💡 <b>Совет:</b> Настройте права сейчас, чтобы бот сразу начал защищать ваш канал!"
        )

        # Send instructions to channel
        await update.bot.send_message(chat_id=chat.id, text=setup_instructions)
        logger.info(f"Sent setup instructions to channel {chat.id}")

    except Exception as e:
        logger.error(f"Error sending setup instructions: {e}")


async def _notify_admin_bot_removed(update, admin_id: int) -> None:
    """Notify admin that bot was removed from a channel."""
    try:
        chat = update.chat

        # Determine chat type for appropriate message
        if chat.type == "channel":
            chat_type_name = "канал"
            chat_emoji = "📢"
        elif chat.type == "supergroup":
            chat_type_name = "группу комментариев"
            chat_emoji = "💬"
        else:
            chat_type_name = "чат"
            chat_emoji = "💬"

        channel_info = (
            f"🚫 <b>Бот удален из {chat_type_name}</b>\n\n"
            f"{chat_emoji} <b>{chat_type_name.title()}:</b> {chat.title or 'Без названия'}\n"
            f"🆔 <b>ID:</b> <code>{chat.id}</code>\n"
        )

        if hasattr(chat, "username") and chat.username:
            channel_info += f"👤 <b>Username:</b> @{chat.username}\n"

        channel_info += (
            f"👥 <b>Тип:</b> {chat.type}\n"
            f"⏰ <b>Время:</b> {update.date.strftime('%d.%m.%Y %H:%M')}\n\n"
            "❌ <b>Мониторинг остановлен</b>"
        )

        await update.bot.send_message(chat_id=admin_id, text=channel_info)
        logger.info(f"Notified admin {admin_id} about bot being removed from {chat_type_name} {chat.id}")

    except Exception as e:
        logger.error(f"Error notifying admin about bot removal: {e}")
