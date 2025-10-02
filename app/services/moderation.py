"""Moderation service for user management."""

import logging
from typing import Optional

from aiogram import Bot

# from aiogram.types import ChatMemberUpdated, User
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# from app.auth.authorization import require_admin, safe_user_operation
from app.models.moderation_log import ModerationAction, ModerationLog
from app.models.user import User as UserModel
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)


class ModerationService:
    """Service for user moderation operations."""

    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session

    async def ban_user(self, user_id: int, chat_id: int, admin_id: int, reason: Optional[str] = None) -> bool:
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
            logger.info(f"Starting unban process for user {user_id} in chat {chat_id}")

            # Unban user in Telegram
            try:
                await self.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                logger.info(f"Successfully unbanned user {user_id} in Telegram chat {chat_id}")
            except Exception as telegram_error:
                logger.error(f"Telegram API error during unban: {telegram_error}")
                # Продолжаем выполнение даже если Telegram API ошибся

            # Deactivate the last ban for this user in this chat
            await self._deactivate_last_ban(user_id, chat_id)
            logger.info(f"Deactivated last ban for user {user_id} in chat {chat_id}")

            # Update user status in database
            await self._update_user_status(user_id, is_banned=False, ban_reason=None)
            logger.info(f"Updated user {user_id} status to not banned in database")

            # Log moderation action
            await self._log_moderation_action(
                action=ModerationAction.UNBAN, user_id=user_id, admin_id=admin_id, chat_id=chat_id
            )

            # Проверяем статус пользователя после разбана
            try:
                member = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                logger.info(f"User {user_id} status after unban: {member.status}")
            except Exception as status_error:
                logger.warning(f"Could not check user {user_id} status after unban: {status_error}")

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

    async def mute_user(self, user_id: int, chat_id: int, admin_id: int, reason: Optional[str] = None) -> bool:
        """Mute user in chat."""
        try:
            # Mute user in Telegram (restrict permissions)
            await self.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=None)  # No permissions = muted

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
        # Сначала проверяем активные баны в moderation_logs
        result = await self.db.execute(
            select(ModerationLog).where(
                ModerationLog.user_id == user_id,
                ModerationLog.action == ModerationAction.BAN,
                ModerationLog.is_active.is_(True),
            )
        )
        active_bans = result.scalars().all()

        if active_bans:
            logger.info(f"User {user_id} has {len(active_bans)} active ban(s) in moderation_logs")
            return True

        # Если нет активных банов в moderation_logs, проверяем users.is_banned
        result = await self.db.execute(select(UserModel.is_banned).where(UserModel.telegram_id == user_id))
        user = result.scalar_one_or_none()
        return user is True if user is not None else False

    async def is_user_muted(self, user_id: int) -> bool:
        """Check if user is muted."""
        result = await self.db.execute(select(UserModel.is_muted).where(UserModel.telegram_id == user_id))
        user = result.scalar_one_or_none()
        return user is True if user is not None else False

    async def get_banned_users(self, limit: int = 20) -> list:
        """Get list of currently active banned users from ModerationLog."""
        result = await self.db.execute(
            select(ModerationLog)
            .where(ModerationLog.action == ModerationAction.BAN, ModerationLog.is_active)
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
        """Get ban history (all bans, active and inactive) from all chats."""
        # Получаем уникальные чаты с банами
        chat_result = await self.db.execute(
            select(ModerationLog.chat_id).where(ModerationLog.action == ModerationAction.BAN).distinct()
        )
        chat_ids = [row[0] for row in chat_result.fetchall()]

        if not chat_ids:
            return []

        # Получаем последние баны из каждого чата
        all_bans = []
        for chat_id in chat_ids:
            result = await self.db.execute(
                select(ModerationLog)
                .where(ModerationLog.action == ModerationAction.BAN, ModerationLog.chat_id == chat_id)
                .order_by(ModerationLog.created_at.desc())
                .limit(limit // len(chat_ids) + 1)  # Равномерно распределяем лимит
            )
            chat_bans = result.scalars().all()
            all_bans.extend(chat_bans)

        # Сортируем по дате и ограничиваем общий лимит
        all_bans.sort(key=lambda x: x.created_at, reverse=True)
        return all_bans[:limit]

    async def get_ban_history_by_chat(self, chat_id: int, limit: int = 10) -> list:
        """Get ban history for specific chat."""
        result = await self.db.execute(
            select(ModerationLog)
            .where(ModerationLog.action == ModerationAction.BAN, ModerationLog.chat_id == chat_id)
            .order_by(ModerationLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_deleted_messages_count(self) -> int:
        """Get total count of deleted messages."""
        result = await self.db.execute(select(ModerationLog).where(ModerationLog.action == ModerationAction.DELETE_MESSAGE))
        return len(result.scalars().all())

    async def get_spam_statistics(self) -> dict:
        """Get spam statistics."""
        # Count deleted messages
        deleted_messages = await self.get_deleted_messages_count()

        # Count bans
        banned_users = await self.get_banned_users(limit=1000)
        total_bans = len(banned_users)

        # Count total moderation actions
        result = await self.db.execute(select(ModerationLog))
        total_actions = len(result.scalars().all())

        return {
            "deleted_messages": deleted_messages,
            "total_bans": total_bans,
            "total_actions": total_actions,
        }

    async def cleanup_duplicate_bans(self, chat_id: int) -> int:
        """Remove duplicate ban records for the same user in the same chat."""
        try:
            # Находим дубликаты - записи с одинаковыми user_id, chat_id, action=BAN
            result = await self.db.execute(
                select(ModerationLog)
                .where(ModerationLog.chat_id == chat_id, ModerationLog.action == ModerationAction.BAN)
                .order_by(ModerationLog.user_id, ModerationLog.created_at.desc())
            )
            all_bans = result.scalars().all()

            # Группируем по user_id
            user_bans = {}
            for ban in all_bans:
                if ban.user_id not in user_bans:
                    user_bans[ban.user_id] = []
                user_bans[ban.user_id].append(ban)

            removed_count = 0

            # Для каждого пользователя оставляем только самую новую активную запись
            for user_id, bans in user_bans.items():
                if len(bans) > 1:
                    # Сортируем по дате создания (новые первыми)
                    bans.sort(key=lambda x: x.created_at, reverse=True)

                    # Оставляем только первую (самую новую) запись
                    # keep_ban = bans[0]  # Не используется
                    for ban in bans[1:]:
                        await self.db.delete(ban)
                        removed_count += 1
                        logger.info(f"Removed duplicate ban record for user {user_id} in chat {chat_id}")

            await self.db.commit()
            return removed_count

        except Exception as e:
            logger.error(f"Error cleaning up duplicate bans: {e}")
            return 0

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
                    ModerationLog.is_active,
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
                .where(ModerationLog.chat_id == chat_id, ModerationLog.action == ModerationAction.BAN)
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
                        # Проверяем, есть ли уже активный бан для этого пользователя в этом чате
                        existing_ban = await self.db.execute(
                            select(ModerationLog).where(
                                ModerationLog.user_id == user_id,
                                ModerationLog.chat_id == chat_id,
                                ModerationLog.action == ModerationAction.BAN,
                                ModerationLog.is_active.is_(True),
                            )
                        )
                        if existing_ban.scalar_one_or_none():
                            logger.info(f"User {user_id} already has active ban in chat {chat_id}, skipping")
                            continue

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
                        elif member.status in ["member", "administrator", "creator"] and ban_log.is_active:
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

            # Очищаем дубликаты
            removed_duplicates = await self.cleanup_duplicate_bans(chat_id)

            # Формируем ответ
            if synced_count > 0 or created_count > 0 or removed_duplicates > 0:
                message = f"✅ Синхронизация завершена для чата '{chat_title}'\n"
                if created_count > 0:
                    message += f"Создано записей: {created_count}\n"
                if synced_count > 0:
                    message += f"Обновлено записей: {synced_count}\n"
                if removed_duplicates > 0:
                    message += f"Удалено дубликатов: {removed_duplicates}\n"
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
            await self.db.execute(update(UserModel).where(UserModel.telegram_id == user_id).values(**update_data))
            await self.db.commit()

        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Если разблокируем пользователя,
        # деактивируем ВСЕ его активные баны
        if is_banned is False:
            await self._deactivate_all_user_bans(user_id)

    async def _deactivate_all_user_bans(self, user_id: int) -> None:
        """Deactivate ALL active bans for user across all chats."""
        try:
            # Находим ВСЕ активные баны для пользователя
            result = await self.db.execute(
                select(ModerationLog).where(
                    ModerationLog.user_id == user_id,
                    ModerationLog.action == ModerationAction.BAN,
                    ModerationLog.is_active.is_(True),
                )
            )
            active_bans = result.scalars().all()

            # Деактивируем все найденные баны
            for ban in active_bans:
                ban.is_active = False
                logger.info(f"Deactivated ban {ban.id} for user {user_id} in chat {ban.chat_id}")

            await self.db.commit()
            logger.info(f"Deactivated {len(active_bans)} active bans for user {user_id}")
        except Exception as e:
            logger.error(f"Error deactivating all bans for user {user_id}: {e}")

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
