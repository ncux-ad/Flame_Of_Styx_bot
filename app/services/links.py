"""Link checking service for bot detection."""

import re
import logging
from typing import List, Optional, Tuple
from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bot import Bot as BotModel
from app.services.moderation import ModerationService

logger = logging.getLogger(__name__)


class LinkService:
    """Service for checking links and detecting bots."""
    
    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session
        self.moderation_service = ModerationService(bot, db_session)
    
    async def check_message_for_bot_links(self, message: Message) -> List[Tuple[str, bool]]:
        """Check message for bot links and return list of (username, is_bot) tuples."""
        if not message.text:
            return []
        
        # Find all t.me/username patterns
        t_me_pattern = r't\.me/([a-zA-Z0-9_]+)'
        matches = re.findall(t_me_pattern, message.text, re.IGNORECASE)
        
        results = []
        for username in matches:
            is_bot = await self._check_if_username_is_bot(username)
            results.append((username, is_bot))
        
        return results
    
    async def _check_if_username_is_bot(self, username: str) -> bool:
        """Check if username belongs to a bot."""
        try:
            # First check if it's in our whitelist
            if await self._is_bot_whitelisted(username):
                return False  # Whitelisted bots are allowed
            
            # Try to get chat member info
            try:
                chat_member = await self.bot.get_chat_member(
                    chat_id=f"@{username}",
                    user_id=self.bot.id
                )
                
                # If we can get chat member info, it's likely a bot
                return True
                
            except Exception:
                # If we can't get chat member info, it might not be a bot
                # or it might be a private channel
                return False
                
        except Exception as e:
            logger.error(f"Error checking if {username} is bot: {e}")
            return False
    
    async def _is_bot_whitelisted(self, username: str) -> bool:
        """Check if bot is in whitelist."""
        result = await self.db.execute(
            select(BotModel.is_whitelisted)
            .where(BotModel.username == username)
        )
        is_whitelisted = result.scalar_one_or_none()
        return is_whitelisted is True
    
    async def handle_bot_link_detection(
        self, 
        message: Message, 
        bot_links: List[Tuple[str, bool]]
    ) -> bool:
        """Handle detection of bot links in message."""
        if not bot_links:
            return False
        
        # Check if any of the links are to non-whitelisted bots
        non_whitelisted_bots = [username for username, is_bot in bot_links if is_bot]
        
        if non_whitelisted_bots:
            # Delete message and ban user
            await self.moderation_service.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id,
                admin_id=0  # System action
            )
            
            if message.from_user:
                await self.moderation_service.ban_user(
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    admin_id=0,  # System action
                    reason=f"Posted bot links: {', '.join(non_whitelisted_bots)}"
                )
            
            logger.info(f"Deleted message with bot links: {non_whitelisted_bots}")
            return True
        
        return False
    
    async def add_bot_to_whitelist(
        self, 
        username: str, 
        admin_id: int,
        telegram_id: Optional[int] = None
    ) -> bool:
        """Add bot to whitelist."""
        try:
            # Check if bot already exists
            result = await self.db.execute(
                select(BotModel).where(BotModel.username == username)
            )
            existing_bot = result.scalar_one_or_none()
            
            if existing_bot:
                # Update existing bot
                existing_bot.is_whitelisted = True
                existing_bot.telegram_id = telegram_id or existing_bot.telegram_id
            else:
                # Create new bot entry
                new_bot = BotModel(
                    username=username,
                    telegram_id=telegram_id or 0,
                    is_whitelisted=True
                )
                self.db.add(new_bot)
            
            await self.db.commit()
            logger.info(f"Bot {username} added to whitelist by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding bot {username} to whitelist: {e}")
            return False
    
    async def remove_bot_from_whitelist(
        self, 
        username: str, 
        admin_id: int
    ) -> bool:
        """Remove bot from whitelist."""
        try:
            result = await self.db.execute(
                select(BotModel).where(BotModel.username == username)
            )
            bot = result.scalar_one_or_none()
            
            if bot:
                bot.is_whitelisted = False
                await self.db.commit()
                logger.info(f"Bot {username} removed from whitelist by admin {admin_id}")
                return True
            else:
                logger.warning(f"Bot {username} not found in whitelist")
                return False
                
        except Exception as e:
            logger.error(f"Error removing bot {username} from whitelist: {e}")
            return False
    
    async def get_whitelisted_bots(self) -> List[BotModel]:
        """Get list of whitelisted bots."""
        result = await self.db.execute(
            select(BotModel).where(BotModel.is_whitelisted == True)
        )
        return result.scalars().all()
