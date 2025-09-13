"""Channel message handlers."""

import logging

from aiogram import Router

# from aiogram.filters import KICKED, LEFT, MEMBER, ChatMemberUpdatedFilter
from aiogram.types import Message

from app.services.channels import ChannelService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import safe_format_message, sanitize_for_logging

# DI will inject services automatically

logger = logging.getLogger(__name__)

# Create router
channel_router = Router()


@channel_router.message()
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
        logger.info(
            f"Channel handler: sender_chat={message.sender_chat}, chat_type={message.chat.type}"
        )
        logger.info(
            f"handle_channel_message called: from_user={message.from_user}, is_bot={message.from_user.is_bot if message.from_user else None}"
        )

        # Handle messages from channels (sender_chat) or channel comment groups (supergroup)
        # Skip private messages and regular groups
        if message.chat.type not in ["channel", "supergroup"]:
            return

        # Skip if message is from bot (but allow channel messages)
        if message.from_user and message.from_user.is_bot and not message.sender_chat:
            return

        # Determine channel ID for checking
        channel_id = message.sender_chat.id if message.sender_chat else message.chat.id

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
        logger.error(
            safe_format_message(
                "Error handling channel message: {error}", error=sanitize_for_logging(e)
            )
        )


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
        logger.info(f"Native channel message: {message.text}")

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
        logger.error(
            safe_format_message(
                "Error handling native channel message: {error}", error=sanitize_for_logging(e)
            )
        )


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
            link
            for link in bot_links
            if link[0] in ["suspicious_media", "forwarded_media", "media_without_caption"]
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
            await channel_service.block_channel(
                channel_id=channel_id, reason="Rate limit exceeded", admin_id=admin_id
            )
            return

        # If passed all checks, handle as normal channel
        await channel_service.handle_channel_message(message, admin_id)

    except Exception as e:
        logger.error(
            safe_format_message(
                "Error handling foreign channel message: {error}", error=sanitize_for_logging(e)
            )
        )


@channel_router.my_chat_member()
async def handle_channel_member_update(update, channel_service: ChannelService) -> None:
    """Handle channel member updates."""
    try:
        # Log the event
        logger.info(
            safe_format_message(
                "Channel member update: {update}", update=sanitize_for_logging(update)
            )
        )

        # Save channel information to database
        if hasattr(update, "chat") and update.chat:
            await channel_service.save_channel_info(update.chat, None)

    except Exception as e:
        logger.error(
            safe_format_message(
                "Error handling channel member update: {error}", error=sanitize_for_logging(e)
            )
        )
