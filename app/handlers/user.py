"""User message handlers."""

import logging

from aiogram import F, Router
from aiogram.filters import KICKED, LEFT, MEMBER, ChatMemberUpdatedFilter, Command
from aiogram.types import ChatMemberUpdated, Message

from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)

# Create router
user_router = Router()


# Help command moved to admin.py to avoid duplication


@user_router.message(Command("start"))
async def handle_start_command(message: Message, **kwargs) -> None:
    """Handle /start command for admins only."""
    try:
        welcome_text = (
            "🤖 <b>AntiSpam Bot</b>\n\n"
            "Добро пожаловать в панель администратора!\n\n"
            "Доступные команды:\n"
            "/status - статистика\n"
            "/channels - управление каналами\n"
            "/bots - управление ботами\n"
            "/suspicious - подозрительные профили\n"
            "/help - помощь"
        )

        await message.answer(welcome_text)

    except Exception as e:
        logger.error(safe_format_message("Error handling start command: {error}", error=sanitize_for_logging(e)))


@user_router.message()
async def handle_user_message(
    message: Message,
    data: dict = None
) -> None:
    """Handle user messages with spam detection."""
    try:
        # Skip if message is from bot
        if message.from_user and message.from_user.is_bot:
            return

        # Skip if message is from channel (handled by channel handler)
        if message.sender_chat:
            return

        # Get services from data
        if not data:
            logger.error("Data not provided to handler")
            return

        link_service = data.get('link_service')
        profile_service = data.get('profile_service')

        if not link_service or not profile_service:
            logger.error("Services not injected properly")
            return

        # Check for bot links in message
        bot_links = await link_service.check_message_for_bot_links(message)

        if bot_links:
            # Handle bot link detection
            await link_service.handle_bot_link_detection(message, bot_links)
            return

        # Check user profile for suspicious patterns
        if message.from_user:
            # Get admin ID from config
            from app.config import load_config
            config = load_config()
            admin_id = config.admin_ids_list[0] if config.admin_ids_list else 0

            suspicious_profile = await profile_service.analyze_user_profile(
                user=message.from_user,
                admin_id=admin_id
            )

            if suspicious_profile:
                # Notify admin about suspicious user
                await _notify_admin_about_suspicious_user(message)

    except Exception as e:
        logger.error(safe_format_message("Error handling user message: {error}", error=sanitize_for_logging(e)))


async def _notify_admin_about_suspicious_user(message: Message) -> None:
    """Notify admin about suspicious user."""
    try:
        from app.config import load_config

        config = load_config()

        if message.from_user:
            user_info = f"🚨 <b>Подозрительный пользователь</b>\n\n"
            user_info += f"<b>ID:</b> {message.from_user.id}\n"
            if message.from_user.username:
                user_info += f"<b>Username:</b> @{message.from_user.username}\n"
            user_info += f"<b>Имя:</b> {message.from_user.first_name}"
            if message.from_user.last_name:
                user_info += f" {message.from_user.last_name}"
            user_info += f"\n\n<b>Сообщение:</b> {message.text[:200]}..."

            # Send notification to all admins
            for admin_id in config.admin_ids_list:
                try:
                    await message.bot.send_message(
                        chat_id=admin_id,
                        text=user_info,
                        reply_to_message_id=message.message_id
                    )
                except Exception as e:
                    logger.error(safe_format_message("Error notifying admin {admin_id}: {error}", admin_id=sanitize_for_logging(admin_id), error=sanitize_for_logging(e)))

    except Exception as e:
        logger.error(safe_format_message("Error notifying admin about suspicious user: {error}", error=sanitize_for_logging(e)))


@user_router.my_chat_member()
async def handle_new_member(update: ChatMemberUpdated) -> None:
    """Handle new chat member."""
    try:
        # Check if user was added to chat
        if update.new_chat_member.status in [MEMBER, KICKED, LEFT]:
            user = update.new_chat_member.user

            # Skip if it's a bot and not whitelisted
            if user.is_bot:
                # TODO: Implement bot banning
                # This will be implemented when services are properly integrated
                logger.info(safe_format_message("Bot {username} joined chat {chat_id}", username=sanitize_for_logging(user.username), chat_id=sanitize_for_logging(update.chat.id)))

    except Exception as e:
        logger.error(safe_format_message("Error handling new member: {error}", error=sanitize_for_logging(e)))


@user_router.chat_member()
async def handle_chat_member_update(update: ChatMemberUpdated) -> None:
    """Handle chat member updates."""
    try:
        # Check if user was banned or left
        if update.new_chat_member.status in [KICKED, LEFT]:
            user = update.new_chat_member.user

            # Log the event
            logger.info(safe_format_message(
                "User {username} {status} from chat {chat_id}",
                username=sanitize_for_logging(user.username),
                status=sanitize_for_logging(update.new_chat_member.status),
                chat_id=sanitize_for_logging(update.chat.id)
            ))

    except Exception as e:
        logger.error(safe_format_message("Error handling chat member update: {error}", error=sanitize_for_logging(e)))
