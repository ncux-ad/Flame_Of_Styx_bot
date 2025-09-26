"""Channel management service."""

import logging
from typing import List, Optional

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.auth.authorization import require_admin, safe_user_operation
from app.models.channel import Channel as ChannelModel
from app.models.channel import ChannelStatus
from app.models.moderation_log import ModerationAction, ModerationLog
from app.services.moderation import ModerationService
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing channel whitelist/blacklist."""

    def __init__(self, bot: Bot, db_session: AsyncSession, native_channel_ids: List[int] = None):
        self.bot = bot
        self.db = db_session
        self.moderation_service = ModerationService(bot, db_session)
        self.native_channel_ids = native_channel_ids or []

    async def handle_channel_message(self, message: Message, admin_id: int) -> bool:
        """Handle message from channel (sender_chat)."""
        if not message.sender_chat:
            return False

        channel_id = message.sender_chat.id
        channel_username = message.sender_chat.username
        channel_title = message.sender_chat.title or "Unknown Channel"

        # Check if channel is already in database
        channel = await self._get_channel_by_id(channel_id)

        if not channel:
            # New channel - create entry and notify admin
            channel = await self._create_channel(
                channel_id=channel_id,
                username=channel_username,
                title=channel_title,
                status=ChannelStatus.PENDING,
            )

            # Notify admin about new channel
            await self._notify_admin_about_channel(
                admin_id=admin_id, channel=channel, message=message
            )

            return True

        # Check channel status
        if channel.status.value == ChannelStatus.BLOCKED.value:
            # Channel is blocked - delete message and ban channel
            await self.moderation_service.delete_message(
                chat_id=message.chat.id, message_id=message.message_id, admin_id=0  # System action
            )

            logger.info(
                safe_format_message(
                    "Deleted message from blocked channel {channel_id}",
                    channel_id=sanitize_for_logging(channel_id),
                )
            )
            return True

        elif channel.status.value == ChannelStatus.ALLOWED.value:
            # Channel is allowed - let message pass
            return False

        else:  # PENDING
            # Channel is pending - notify admin again
            await self._notify_admin_about_channel(
                admin_id=admin_id, channel=channel, message=message
            )
            return True

    async def allow_channel(self, channel_id: int, admin_id: int) -> bool:
        """Allow channel to post messages."""
        try:
            channel = await self._get_channel_by_id(channel_id)
            if not channel:
                logger.warning(
                    safe_format_message(
                        "Channel {channel_id} not found",
                        channel_id=sanitize_for_logging(channel_id),
                    )
                )
                return False

            # Update channel status
            setattr(channel, "status", ChannelStatus.ALLOWED)
            await self.db.commit()

            # Log moderation action
            await self._log_channel_action(
                action=ModerationAction.ALLOW_CHANNEL, channel_id=channel_id, admin_id=admin_id
            )

            logger.info(
                safe_format_message(
                    "Channel {channel_id} allowed by admin {admin_id}",
                    channel_id=sanitize_for_logging(channel_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error allowing channel {channel_id}: {error}",
                    channel_id=sanitize_for_logging(channel_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    async def block_channel(self, channel_id: int, reason: str, admin_id: int) -> bool:
        """Block channel from posting messages."""
        try:
            channel = await self._get_channel_by_id(channel_id)
            if not channel:
                logger.warning(
                    safe_format_message(
                        "Channel {channel_id} not found",
                        channel_id=sanitize_for_logging(channel_id),
                    )
                )
                return False

            # Update channel status
            setattr(channel, "status", ChannelStatus.BLOCKED)
            # Add notes field if it exists in the model
            if hasattr(channel, "notes"):
                channel.notes = reason
            await self.db.commit()

            # Log moderation action
            await self._log_channel_action(
                action=ModerationAction.BLOCK_CHANNEL, channel_id=channel_id, admin_id=admin_id
            )

            logger.info(
                safe_format_message(
                    "Channel {channel_id} blocked by admin {admin_id}: {reason}",
                    channel_id=sanitize_for_logging(channel_id),
                    admin_id=sanitize_for_logging(admin_id),
                    reason=sanitize_for_logging(reason),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error blocking channel {channel_id}: {error}",
                    channel_id=sanitize_for_logging(channel_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    async def get_channel_status(self, channel_id: int) -> Optional[ChannelStatus]:
        """Get channel status."""
        channel = await self._get_channel_by_id(channel_id)
        if channel and channel.status is not None:
            return ChannelStatus(channel.status)
        return None

    async def get_allowed_channels(self) -> List[ChannelModel]:
        """Get list of allowed channels."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.status == ChannelStatus.ALLOWED)
        )
        return list(result.scalars().all())

    async def get_blocked_channels(self) -> List[ChannelModel]:
        """Get list of blocked channels."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.status == ChannelStatus.BLOCKED)
        )
        return list(result.scalars().all())

    async def get_pending_channels(self) -> List[ChannelModel]:
        """Get list of pending channels."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.status == ChannelStatus.PENDING)
        )
        return list(result.scalars().all())

    async def _get_channel_by_id(self, channel_id: int) -> Optional[ChannelModel]:
        """Get channel by ID."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.telegram_id == channel_id)
        )
        return result.scalar_one_or_none()

    async def _create_channel(
        self, channel_id: int, username: Optional[str], title: str, status: ChannelStatus
    ) -> ChannelModel:
        """Create new channel entry."""
        channel = ChannelModel(
            telegram_id=channel_id, username=username, title=title, status=status
        )

        self.db.add(channel)
        await self.db.commit()
        await self.db.refresh(channel)

        return channel

    async def _notify_admin_about_channel(
        self, admin_id: int, channel: ChannelModel, message: Message
    ) -> None:
        """Notify admin about new channel message."""
        try:
            channel_info = "📢 <b>Новое сообщение от канала</b>\n\n"
            channel_info += f"<b>Канал:</b> {channel.title}\n"
            if channel.username is not None and channel.username.strip():
                channel_info += f"<b>Username:</b> @{channel.username}\n"
            channel_info += f"<b>ID:</b> {channel.telegram_id}\n"
            channel_info += f"<b>Статус:</b> {channel.status.value}\n\n"
            message_text = message.text or ""
            channel_info += f"<b>Сообщение:</b> {message_text[:200]}..."

            await self.bot.send_message(
                chat_id=admin_id, text=channel_info, reply_markup=None  # Will be set by handler
            )

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error notifying admin about channel: {error}", error=sanitize_for_logging(e)
                )
            )

    async def _log_channel_action(
        self, action: ModerationAction, channel_id: int, admin_id: int
    ) -> None:
        """Log channel action to database."""
        log_entry = ModerationLog(action=action, channel_id=channel_id, admin_telegram_id=admin_id)

        self.db.add(log_entry)
        await self.db.commit()

    async def is_native_channel(self, channel_id: int) -> bool:
        """Check if channel is native (where bot has admin rights)."""
        try:
            logger.info(f"Checking if channel {channel_id} is native...")
            logger.info(f"Configured native channels: {self.native_channel_ids}")
            
            # First check if channel is in the configured native channels list
            if channel_id in self.native_channel_ids:
                logger.info(f"Channel {channel_id} is in native list: True")
                return True
            
            # If not in list, check if bot has admin rights in this channel
            try:
                # Get bot's member status in the channel
                bot_member = await self.bot.get_chat_member(chat_id=channel_id, user_id=self.bot.id)
                
                # Check if bot is admin or creator
                is_admin = bot_member.status in ['administrator', 'creator']
                logger.info(f"Channel {channel_id} bot admin status: {is_admin} (status: {bot_member.status})")
                
                return is_admin
                
            except Exception as e:
                # If we can't get member status, assume it's not native
                logger.warning(f"Could not check admin status for channel {channel_id}: {e}")
                return False
                
        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error checking if channel is native: {error}", error=sanitize_for_logging(e)
                )
            )
            return False

    async def mark_channel_as_suspicious(self, channel_id: int, reason: str, admin_id: int) -> None:
        """Mark channel as suspicious."""
        try:
            # Update channel status to suspicious
            result = await self.db.execute(
                select(ChannelModel).where(ChannelModel.telegram_id == channel_id)
            )
            channel = result.scalar_one_or_none()

            if channel:
                setattr(channel, "status", ChannelStatus.SUSPICIOUS)
                # Add notes field if it exists in the model
                if hasattr(channel, "notes"):
                    channel.notes = reason
                await self.db.commit()

                # Log the action
                await self._log_channel_action(
                    ModerationAction.MARK_SUSPICIOUS, channel_id, admin_id
                )

                logger.info(
                    safe_format_message(
                        "Channel {channel_id} marked as suspicious: {reason}",
                        channel_id=sanitize_for_logging(channel_id),
                        reason=sanitize_for_logging(reason),
                    )
                )

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error marking channel as suspicious: {error}", error=sanitize_for_logging(e)
                )
            )

    async def check_channel_rate_limit(self, channel_id: int) -> bool:
        """Check if channel exceeded rate limit."""
        try:
            # Simple rate limiting: 10 messages per minute
            # In production, this should use Redis or similar
            import time

            now = time.time()
            if not hasattr(self, "_channel_messages"):
                self._channel_messages = {}

            if channel_id not in self._channel_messages:
                self._channel_messages[channel_id] = []

            # Clean old messages
            self._channel_messages[channel_id] = [
                msg_time
                for msg_time in self._channel_messages[channel_id]
                if now - msg_time < 60  # 1 minute
            ]

            # Add current message
            self._channel_messages[channel_id].append(now)

            # Check if exceeded limit
            return len(self._channel_messages[channel_id]) > 10

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error checking channel rate limit: {error}", error=sanitize_for_logging(e)
                )
            )
            return False

    async def get_all_channels(self) -> List[ChannelModel]:
        """Get all channels from database."""
        try:
            result = await self.db.execute(select(ChannelModel))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all channels: {e}")
            return []

    async def get_total_channels_count(self) -> int:
        """Get total number of channels."""
        try:
            result = await self.db.execute(select(ChannelModel))
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting channels count: {e}")
            return 0

    async def get_channel_info(self, chat_id: int) -> dict:
        """Get channel information from Telegram API."""
        try:
            chat = await self.bot.get_chat(chat_id)
            return {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type,
                "description": getattr(chat, "description", None),
                "member_count": getattr(chat, "member_count", None),
            }
        except Exception as e:
            logger.error(f"Error getting channel info for {chat_id}: {e}")
            return {
                "id": chat_id,
                "title": f"Unknown Channel ({chat_id})",
                "username": None,
                "type": "unknown",
                "description": None,
                "member_count": None,
            }

    async def save_channel_info(self, chat, sender_chat=None) -> None:
        """Save channel information to database."""
        try:
            logger.info(f"save_channel_info called: chat={chat}, sender_chat={sender_chat}")

            # Only save main channels, not comment groups
            # If sender_chat exists, it's a message from a channel - save the channel
            # If sender_chat is None, it's a message in comment group - don't save
            if not sender_chat:
                logger.info("Message in comment group, not saving to database")
                return

            target_chat = sender_chat

            if not target_chat:
                logger.info("No target_chat, returning")
                return

            # Determine if this is a comment group (not needed for now)
            # is_comment_group = chat.type == "supergroup" and sender_chat is not None
            # linked_chat_id = sender_chat.id if is_comment_group else None

            # Check if channel already exists
            result = await self.db.execute(
                select(ChannelModel).where(ChannelModel.telegram_id == target_chat.id)
            )
            existing_channel = result.scalar_one_or_none()

            if existing_channel:
                # Update existing channel
                existing_channel.title = target_chat.title
                existing_channel.username = target_chat.username
                # existing_channel.is_comment_group = is_comment_group
                logger.info(f"Updated channel info: {target_chat.title} ({target_chat.id})")
            else:
                # Create new channel
                new_channel = ChannelModel(
                    telegram_id=target_chat.id,
                    title=target_chat.title,
                    username=target_chat.username,
                    status=ChannelStatus.ALLOWED,  # Use ALLOWED instead of ACTIVE
                    is_native=False,  # Will be determined later
                    # is_comment_group=is_comment_group
                )
                self.db.add(new_channel)
                logger.info(f"Saved new channel: {target_chat.title} ({target_chat.id})")

            await self.db.commit()

        except Exception as e:
            logger.error(f"Error saving channel info: {e}")
            await self.db.rollback()
