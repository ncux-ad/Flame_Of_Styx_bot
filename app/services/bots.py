"""Bot management service."""

import logging
from typing import List, Optional

from aiogram import Bot as AiogramBot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.auth.authorization import require_admin, safe_user_operation
from app.models.bot import Bot
from app.models.moderation_log import ModerationAction, ModerationLog

# from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)


class BotService:
    """Service for managing bot whitelist."""

    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session

    async def add_bot_to_whitelist(
        self, username: str, admin_id: int, telegram_id: Optional[int] = None
    ) -> bool:
        """Add bot to whitelist."""
        try:
            # Check if bot already exists
            result = await self.db.execute(select(Bot).where(Bot.username == username))
            existing_bot = result.scalar_one_or_none()

            if existing_bot:
                # Update existing bot
                existing_bot.is_whitelisted = True
                if telegram_id:
                    existing_bot.telegram_id = telegram_id
            else:
                # Create new bot entry
                new_bot = Bot(username=username, telegram_id=telegram_id or 0, is_whitelisted=True)
                self.db.add(new_bot)

            await self.db.commit()

            # Log moderation action
            await self._log_bot_action(
                action=ModerationAction.ALLOW_BOT, bot_username=username, admin_id=admin_id
            )

            logger.info(f"Bot {username} added to whitelist by admin {admin_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding bot {username} to whitelist: {e}")
            return False

    async def remove_bot_from_whitelist(self, username: str, admin_id: int) -> bool:
        """Remove bot from whitelist."""
        try:
            result = await self.db.execute(select(Bot).where(Bot.username == username))
            bot = result.scalar_one_or_none()

            if bot:
                bot.is_whitelisted = False
                await self.db.commit()

                # Log moderation action
                await self._log_bot_action(
                    action=ModerationAction.BLOCK_BOT, bot_username=username, admin_id=admin_id
                )

                logger.info(f"Bot {username} removed from whitelist by admin {admin_id}")
                return True
            else:
                logger.warning(f"Bot {username} not found in whitelist")
                return False

        except Exception as e:
            logger.error(f"Error removing bot {username} from whitelist: {e}")
            return False

    async def is_bot_whitelisted(self, username: str) -> bool:
        """Check if bot is whitelisted."""
        result = await self.db.execute(select(Bot.is_whitelisted).where(Bot.username == username))
        is_whitelisted = result.scalar_one_or_none()
        return is_whitelisted is True

    async def get_whitelisted_bots(self) -> List[Bot]:
        """Get list of whitelisted bots."""
        result = await self.db.execute(select(Bot).where(Bot.is_whitelisted))
        return result.scalars().all()

    async def get_all_bots(self) -> List[Bot]:
        """Get list of all bots."""
        result = await self.db.execute(select(Bot))
        return result.scalars().all()

    async def get_bot_by_username(self, username: str) -> Optional[Bot]:
        """Get bot by username."""
        result = await self.db.execute(select(Bot).where(Bot.username == username))
        return result.scalar_one_or_none()

    async def update_bot_info(
        self,
        username: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Update bot information."""
        try:
            result = await self.db.execute(select(Bot).where(Bot.username == username))
            bot = result.scalar_one_or_none()

            if bot:
                if first_name is not None:
                    bot.first_name = first_name
                if last_name is not None:
                    bot.last_name = last_name
                if description is not None:
                    bot.description = description

                await self.db.commit()
                logger.info(f"Bot {username} info updated")
                return True
            else:
                logger.warning(f"Bot {username} not found")
                return False

        except Exception as e:
            logger.error(f"Error updating bot {username} info: {e}")
            return False

    async def get_total_bots_count(self) -> int:
        """Get total number of bots."""
        try:
            result = await self.db.execute(select(Bot))
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting bots count: {e}")
            return 0

    async def _log_bot_action(
        self, action: ModerationAction, bot_username: str, admin_id: int
    ) -> None:
        """Log bot action to database."""
        log_entry = ModerationLog(
            action=action, admin_telegram_id=admin_id, details=f"Bot: {bot_username}"
        )

        self.db.add(log_entry)
        await self.db.commit()
