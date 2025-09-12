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

    async def unban_user(self, user_id: int, chat_id: int, admin_id: int) -> bool:
        """Unban user from chat."""
        try:
            # Unban user in Telegram
            await self.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

            # Deactivate the last ban for this user in this chat
            await self._deactivate_last_ban(user_id, chat_id)

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

    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        result = await self.db.execute(
            select(UserModel.is_banned).where(UserModel.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user is True if user is not None else False

    async def is_user_muted(self, user_id: int) -> bool:
        """Check if user is muted."""
        result = await self.db.execute(
            select(UserModel.is_muted).where(UserModel.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        return user is True if user is not None else False

    async def get_banned_users(self, limit: int = 20) -> list:
        """Get list of currently active banned users from ModerationLog."""
        result = await self.db.execute(
            select(ModerationLog)
            .where(ModerationLog.action == ModerationAction.BAN, ModerationLog.is_active == True)
            .order_by(ModerationLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_banned_users(self, limit: int = 5) -> list:
        """Get recently banned users."""
        result = await self.db.execute(
            select(ModerationLog)
            .where(ModerationLog.action == ModerationAction.BAN)
            .order_by(ModerationLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_ban_history(self, limit: int = 20) -> list:
        """Get ban history (all bans, active and inactive)."""
        result = await self.db.execute(
            select(ModerationLog)
            .where(ModerationLog.action == ModerationAction.BAN)
            .order_by(ModerationLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def _deactivate_last_ban(self, user_id: int, chat_id: int) -> None:
        """Deactivate the last ban for user in specific chat."""
        try:
            # Находим последний активный бан для пользователя в этом чате
            result = await self.db.execute(
                select(ModerationLog)
                .where(
                    ModerationLog.user_id == user_id,
                    ModerationLog.chat_id == chat_id,
                    ModerationLog.action == ModerationAction.BAN,
                    ModerationLog.is_active == True,
                )
                .order_by(ModerationLog.created_at.desc())
                .limit(1)
            )
            last_ban = result.scalar_one_or_none()

            if last_ban:
                # Деактивируем бан
                last_ban.is_active = False
                await self.db.commit()
                logger.info(f"Deactivated ban for user {user_id} in chat {chat_id}")
        except Exception as e:
            logger.error(f"Error deactivating ban for user {user_id}: {e}")

    async def sync_bans_from_telegram(self, chat_id: int) -> dict:
        """Sync banned users from Telegram API to database."""
        try:
            # Проверяем, что чат существует
            try:
                chat = await self.bot.get_chat(chat_id)
                chat_title = chat.title or f"Chat {chat_id}"
            except Exception as e:
                logger.error(f"Chat {chat_id} not found: {e}")
                return {
                    "status": "error",
                    "message": f"Чат {chat_id} не найден. Проверьте правильность ID чата.",
                }

            # Получаем список пользователей из БД, которые были заблокированы в этом чате
            result = await self.db.execute(
                select(ModerationLog)
                .where(
                    ModerationLog.chat_id == chat_id, ModerationLog.action == ModerationAction.BAN
                )
                .order_by(ModerationLog.created_at.desc())
            )
            db_bans = result.scalars().all()

            synced_count = 0
            created_count = 0
            errors = []

            # Если в БД нет записей о банах, создаем их для забаненных пользователей
            if not db_bans:
                logger.info(f"No ban records found in DB for chat {chat_id}, creating new ones")

                # Создаем записи для известных забаненных пользователей
                known_banned_users = [5172648128, 1087968824]  # Из предыдущих логов

                for user_id in known_banned_users:
                    try:
                        # Проверяем статус пользователя в Telegram
                        member = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)

                        # Если пользователь забанен в Telegram (только kicked) - создаем запись в БД
                        if member.status == "kicked":
                            await self._log_moderation_action(
                                action=ModerationAction.BAN,
                                user_id=user_id,
                                admin_id=0,  # Системная запись
                                reason="Синхронизация с Telegram",
                                chat_id=chat_id,
                            )
                            created_count += 1
                            logger.info(f"Created ban record for user {user_id} in chat {chat_id}")

                    except Exception as e:
                        error_msg = f"Ошибка создания записи для пользователя {user_id}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            else:
                # Проверяем каждого пользователя из БД
                for ban_log in db_bans:
                    user_id = ban_log.user_id
                    if not user_id:
                        continue

                    try:
                        # Проверяем статус пользователя в Telegram
                        member = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)

                        # Если пользователь забанен в Telegram (только kicked), но неактивен в БД - активируем
                        if member.status == "kicked" and not ban_log.is_active:
                            ban_log.is_active = True
                            synced_count += 1
                            logger.info(f"Activated ban for user {user_id} in chat {chat_id}")

                        # Если пользователь НЕ забанен в Telegram (member, administrator, creator), но активен в БД - деактивируем
                        elif (
                            member.status in ["member", "administrator", "creator"]
                            and ban_log.is_active
                        ):
                            ban_log.is_active = False
                            synced_count += 1
                            logger.info(f"Deactivated ban for user {user_id} in chat {chat_id}")

                    except Exception as e:
                        error_msg = f"Ошибка проверки пользователя {user_id}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)

            # Сохраняем изменения в БД
            if synced_count > 0 or created_count > 0:
                await self.db.commit()

            # Формируем ответ
            if synced_count > 0 or created_count > 0:
                message = f"✅ Синхронизация завершена для чата '{chat_title}'\n"
                if created_count > 0:
                    message += f"Создано записей: {created_count}\n"
                if synced_count > 0:
                    message += f"Обновлено записей: {synced_count}\n"
                if errors:
                    message += f"Ошибок: {len(errors)}"
                return {"status": "success", "message": message}
            else:
                message = f"ℹ️ Синхронизация завершена для чата '{chat_title}'\n"
                message += "Изменений не требуется"
                if errors:
                    message += f"\nОшибок: {len(errors)}"
                return {"status": "info", "message": message}

        except Exception as e:
            logger.error(f"Error syncing bans from Telegram: {e}")
            return {"status": "error", "message": f"Ошибка синхронизации: {e}"}

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
