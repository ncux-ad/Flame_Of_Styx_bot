"""Channel message handlers."""

import logging

from aiogram import Router
from aiogram.filters import KICKED, LEFT, MEMBER, ChatMemberUpdatedFilter
from aiogram.types import Message

from app.services.channels import ChannelService
from app.services.links import LinkService
from app.services.profiles import ProfileService
from app.utils.security import safe_format_message, sanitize_for_logging

# DI will inject services automatically

logger = logging.getLogger(__name__)

# Create router
channel_router = Router()


@channel_router.message()
async def handle_channel_message(
    message: Message,
    data: dict
) -> None:
    """Handle messages from channels (sender_chat)."""
    try:
        # Only handle messages from channels
        if not message.sender_chat:
            return

        # Skip if message is from bot
        if message.from_user and message.from_user.is_bot:
            return

        # Get services from data
        channel_service = data.get('channel_service')
        link_service = data.get('link_service')
        profile_service = data.get('profile_service')

        if not channel_service or not link_service or not profile_service:
            logger.error("Services not injected properly")
            return

        # Get admin ID from config
        from app.config import load_config
        config = load_config()
        admin_id = config.admin_ids_list[0] if config.admin_ids_list else 0

        # Check if this is the native channel (where bot is connected)
        is_native_channel = await channel_service.is_native_channel(message.sender_chat.id)

        if is_native_channel:
            # Native channel - full freedom, no spam checking
            await channel_service.handle_channel_message(message, admin_id)
        else:
            # Foreign channel - check for spam and rate limiting
            await _handle_foreign_channel_message(
                message, channel_service, link_service, profile_service, admin_id
            )

    except Exception as e:
        logger.error(safe_format_message("Error handling channel message: {error}", error=sanitize_for_logging(e)))


async def _handle_foreign_channel_message(
    message: Message,
    channel_service: ChannelService,
    link_service: LinkService,
    profile_service: ProfileService,
    admin_id: int
) -> None:
    """Handle messages from foreign channels with spam checking."""
    try:
        # Check for bot links in message
        bot_links = await link_service.check_message_for_bot_links(message)
        if bot_links:
            # Handle bot link detection
            await link_service.handle_bot_link_detection(message, bot_links)

            # Mark channel as suspicious
            await channel_service.mark_channel_as_suspicious(
                channel_id=message.sender_chat.id,
                reason="Bot links detected in foreign channel",
                admin_id=admin_id
            )
            return

        # Check for rate limiting
        is_rate_limited = await channel_service.check_channel_rate_limit(
            channel_id=message.sender_chat.id
        )
        if is_rate_limited:
            # Block channel for too frequent messages
            await channel_service.block_channel(
                channel_id=message.sender_chat.id,
                reason="Rate limit exceeded",
                admin_id=admin_id
            )
            return

        # If passed all checks, handle as normal channel
        await channel_service.handle_channel_message(message, admin_id)

    except Exception as e:
        logger.error(safe_format_message("Error handling foreign channel message: {error}", error=sanitize_for_logging(e)))


@channel_router.my_chat_member()
async def handle_channel_member_update(update) -> None:
    """Handle channel member updates."""
    try:
        # This can be used to track when channels are added/removed
        # For now, just log the event
        logger.info(safe_format_message("Channel member update: {update}", update=sanitize_for_logging(update)))

    except Exception as e:
        logger.error(safe_format_message("Error handling channel member update: {error}", error=sanitize_for_logging(e)))
