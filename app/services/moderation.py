"""Moderation service for user management."""

import logging
from typing import Optional

from aiogram import Bot
from aiogram.types import ChatMemberUpdated, User
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.authorization import require_admin, safe_user_operation
from app.models.moderation_log import ModerationAction, ModerationLog
from app.models.user import User as UserModel
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)


class ModerationService:
    """Service for user moderation operations."""

    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session

    @require_admin
    async def ban_user(
        self, user_id: int, chat_id: int, admin_id: int, reason: Optional[str] = None
    ) -> bool:
        """Ban user from chat."""
        try:
            # Ban user in Telegram
            await self.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

            # Update user status in database
            await self._update_user_status(user_id, is_banned=True, ban_reason=reason)

            # Log moderation action
            await self._log_moderation_action(
                action=ModerationAction.BAN,
                user_id=user_id,
                admin_id=admin_id,
                reason=reason,
                chat_id=chat_id,
            )

            logger.info(
                safe_format_message(
                    "User {user_id} banned by admin {admin_id}",
                    user_id=sanitize_for_logging(user_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error banning user {user_id}: {error}",
                    user_id=sanitize_for_logging(user_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    @require_admin
    async def unban_user(self, user_id: int, chat_id: int, admin_id: int) -> bool:
        """Unban user from chat."""
        try:
            # Unban user in Telegram
            await self.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

            # Update user status in database
            await self._update_user_status(user_id, is_banned=False, ban_reason=None)

            # Log moderation action
            await self._log_moderation_action(
                action=ModerationAction.UNBAN, user_id=user_id, admin_id=admin_id, chat_id=chat_id
            )

            logger.info(
                safe_format_message(
                    "User {user_id} unbanned by admin {admin_id}",
                    user_id=sanitize_for_logging(user_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error unbanning user {user_id}: {error}",
                    user_id=sanitize_for_logging(user_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    @require_admin
    async def mute_user(
        self, user_id: int, chat_id: int, admin_id: int, reason: Optional[str] = None
    ) -> bool:
        """Mute user in chat."""
        try:
            # Mute user in Telegram (restrict permissions)
            await self.bot.restrict_chat_member(
                chat_id=chat_id, user_id=user_id, permissions=None  # No permissions = muted
            )

            # Update user status in database
            await self._update_user_status(user_id, is_muted=True)

            # Log moderation action
            await self._log_moderation_action(
                action=ModerationAction.MUTE,
                user_id=user_id,
                admin_id=admin_id,
                reason=reason,
                chat_id=chat_id,
            )

            logger.info(
                safe_format_message(
                    "User {user_id} muted by admin {admin_id}",
                    user_id=sanitize_for_logging(user_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error muting user {user_id}: {error}",
                    user_id=sanitize_for_logging(user_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    @require_admin
    async def unmute_user(self, user_id: int, chat_id: int, admin_id: int) -> bool:
        """Unmute user in chat."""
        try:
            # Unmute user in Telegram (restore permissions)
            from aiogram.types import ChatPermissions

            await self.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_change_info=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                ),
            )

            # Update user status in database
            await self._update_user_status(user_id, is_muted=False)

            # Log moderation action
            await self._log_moderation_action(
                action=ModerationAction.UNMUTE, user_id=user_id, admin_id=admin_id, chat_id=chat_id
            )

            logger.info(
                safe_format_message(
                    "User {user_id} unmuted by admin {admin_id}",
                    user_id=sanitize_for_logging(user_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error unmuting user {user_id}: {error}",
                    user_id=sanitize_for_logging(user_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    @require_admin
    async def delete_message(self, chat_id: int, message_id: int, admin_id: int) -> bool:
        """Delete message."""
        try:
            # Delete message in Telegram
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)

            # Log moderation action
            await self._log_moderation_action(
                action=ModerationAction.DELETE_MESSAGE,
                admin_id=admin_id,
                message_id=message_id,
                chat_id=chat_id,
            )

            logger.info(
                safe_format_message(
                    "Message {message_id} deleted by admin {admin_id}",
                    message_id=sanitize_for_logging(message_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error deleting message {message_id}: {error}",
                    message_id=sanitize_for_logging(message_id),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    @require_admin
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        result = await self.db.execute(
            select(UserModel.is_banned).where(UserModel.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user is True if user is not None else False

    @require_admin
    async def is_user_muted(self, user_id: int) -> bool:
        """Check if user is muted."""
        result = await self.db.execute(
            select(UserModel.is_muted).where(UserModel.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user is True if user is not None else False

    @require_admin
    async def _update_user_status(
        self,
        user_id: int,
        is_banned: Optional[bool] = None,
        is_muted: Optional[bool] = None,
        ban_reason: Optional[str] = None,
    ) -> None:
        """Update user status in database."""
        update_data = {}

        if is_banned is not None:
            update_data["is_banned"] = is_banned
        if is_muted is not None:
            update_data["is_muted"] = is_muted
        if ban_reason is not None:
            update_data["ban_reason"] = ban_reason

        if update_data:
            await self.db.execute(
                update(UserModel).where(UserModel.telegram_id == user_id).values(**update_data)
            )
            await self.db.commit()

    @require_admin
    async def _log_moderation_action(
        self,
        action: ModerationAction,
        user_id: Optional[int] = None,
        admin_id: int = 0,
        reason: Optional[str] = None,
        message_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> None:
        """Log moderation action to database."""
        log_entry = ModerationLog(
            action=action,
            user_id=user_id,
            admin_telegram_id=admin_id,
            reason=reason,
            message_id=message_id,
            chat_id=chat_id,
        )

        self.db.add(log_entry)
        await self.db.commit()
