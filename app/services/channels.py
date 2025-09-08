"""Channel management service."""

import logging
from typing import Optional, List
from aiogram import Bot
from aiogram.types import Message, Chat
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.channel import Channel as ChannelModel, ChannelStatus
from app.models.moderation_log import ModerationLog, ModerationAction
from app.services.moderation import ModerationService

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing channel whitelist/blacklist."""
    
    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session
        self.moderation_service = ModerationService(bot, db_session)
    
    async def handle_channel_message(
        self, 
        message: Message, 
        admin_id: int
    ) -> bool:
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
                status=ChannelStatus.PENDING
            )
            
            # Notify admin about new channel
            await self._notify_admin_about_channel(
                admin_id=admin_id,
                channel=channel,
                message=message
            )
            
            return True
        
        # Check channel status
        if channel.status == ChannelStatus.BLOCKED:
            # Channel is blocked - delete message and ban channel
            await self.moderation_service.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id,
                admin_id=0  # System action
            )
            
            logger.info(f"Deleted message from blocked channel {channel_id}")
            return True
        
        elif channel.status == ChannelStatus.ALLOWED:
            # Channel is allowed - let message pass
            return False
        
        else:  # PENDING
            # Channel is pending - notify admin again
            await self._notify_admin_about_channel(
                admin_id=admin_id,
                channel=channel,
                message=message
            )
            return True
    
    async def allow_channel(
        self, 
        channel_id: int, 
        admin_id: int
    ) -> bool:
        """Allow channel to post messages."""
        try:
            channel = await self._get_channel_by_id(channel_id)
            if not channel:
                logger.warning(f"Channel {channel_id} not found")
                return False
            
            # Update channel status
            channel.status = ChannelStatus.ALLOWED
            await self.db.commit()
            
            # Log moderation action
            await self._log_channel_action(
                action=ModerationAction.ALLOW_CHANNEL,
                channel_id=channel_id,
                admin_id=admin_id
            )
            
            logger.info(f"Channel {channel_id} allowed by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error allowing channel {channel_id}: {e}")
            return False
    
    async def block_channel(
        self, 
        channel_id: int, 
        admin_id: int
    ) -> bool:
        """Block channel from posting messages."""
        try:
            channel = await self._get_channel_by_id(channel_id)
            if not channel:
                logger.warning(f"Channel {channel_id} not found")
                return False
            
            # Update channel status
            channel.status = ChannelStatus.BLOCKED
            await self.db.commit()
            
            # Log moderation action
            await self._log_channel_action(
                action=ModerationAction.BLOCK_CHANNEL,
                channel_id=channel_id,
                admin_id=admin_id
            )
            
            logger.info(f"Channel {channel_id} blocked by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error blocking channel {channel_id}: {e}")
            return False
    
    async def get_channel_status(self, channel_id: int) -> Optional[ChannelStatus]:
        """Get channel status."""
        channel = await self._get_channel_by_id(channel_id)
        return channel.status if channel else None
    
    async def get_allowed_channels(self) -> List[ChannelModel]:
        """Get list of allowed channels."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.status == ChannelStatus.ALLOWED)
        )
        return result.scalars().all()
    
    async def get_blocked_channels(self) -> List[ChannelModel]:
        """Get list of blocked channels."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.status == ChannelStatus.BLOCKED)
        )
        return result.scalars().all()
    
    async def get_pending_channels(self) -> List[ChannelModel]:
        """Get list of pending channels."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.status == ChannelStatus.PENDING)
        )
        return result.scalars().all()
    
    async def _get_channel_by_id(self, channel_id: int) -> Optional[ChannelModel]:
        """Get channel by ID."""
        result = await self.db.execute(
            select(ChannelModel).where(ChannelModel.telegram_id == channel_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_channel(
        self, 
        channel_id: int, 
        username: Optional[str], 
        title: str,
        status: ChannelStatus
    ) -> ChannelModel:
        """Create new channel entry."""
        channel = ChannelModel(
            telegram_id=channel_id,
            username=username,
            title=title,
            status=status
        )
        
        self.db.add(channel)
        await self.db.commit()
        await self.db.refresh(channel)
        
        return channel
    
    async def _notify_admin_about_channel(
        self, 
        admin_id: int, 
        channel: ChannelModel, 
        message: Message
    ) -> None:
        """Notify admin about new channel message."""
        try:
            channel_info = f"📢 <b>Новое сообщение от канала</b>\n\n"
            channel_info += f"<b>Канал:</b> {channel.title}\n"
            if channel.username:
                channel_info += f"<b>Username:</b> @{channel.username}\n"
            channel_info += f"<b>ID:</b> {channel.telegram_id}\n"
            channel_info += f"<b>Статус:</b> {channel.status.value}\n\n"
            channel_info += f"<b>Сообщение:</b> {message.text[:200]}..."
            
            await self.bot.send_message(
                chat_id=admin_id,
                text=channel_info,
                reply_markup=None  # Will be set by handler
            )
            
        except Exception as e:
            logger.error(f"Error notifying admin about channel: {e}")
    
    async def _log_channel_action(
        self,
        action: ModerationAction,
        channel_id: int,
        admin_id: int
    ) -> None:
        """Log channel action to database."""
        log_entry = ModerationLog(
            action=action,
            channel_id=channel_id,
            admin_telegram_id=admin_id
        )
        
        self.db.add(log_entry)
        await self.db.commit()
