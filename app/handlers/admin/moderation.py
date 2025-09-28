"""
Команды модерации (unban, banned, ban_history, sync_bans)
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.moderation import ModerationService
from app.services.channels import ChannelService
from app.services.profiles import ProfileService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)

# Создаем роутер для команд модерации
moderation_router = Router()


@moderation_router.message(Command("unban"))
async def handle_unban_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Разблокировать пользователя с подсказками."""
    try:
        if not message.from_user:
            return
        logger.info(f"Unban command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            # Показываем последних заблокированных для выбора
            banned_users = await moderation_service.get_banned_users(limit=5)

            if not banned_users:
                await message.answer("❌ Нет заблокированных пользователей")
                return

            text = "🚫 <b>Выберите пользователя для разблокировки:</b>\n\n"

            for i, log_entry in enumerate(banned_users, 1):
                user_id = log_entry.user_id
                reason = log_entry.reason or "Спам"
                chat_id = log_entry.chat_id

                # Получаем информацию о пользователе
                user_info = await profile_service.get_user_info(int(str(user_id)))
                user_display = (
                    f"@{user_info.get('username')}"
                    if user_info.get("username")
                    else f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                )
                if not user_display or user_display == "Unknown User":
                    user_display = f"User {user_id}"

                # Получаем информацию о чате
                chat_info = (
                    await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
                )
                chat_display = f"@{chat_info.get('username')}" if chat_info.get("username") else chat_info.get("title", "Unknown Chat")

                text += f"{i}. <b>{user_display}</b> <code>({user_id})</code>\n"
                text += f"   Причина: {reason}\n"
                text += f"   Чат: <b>{chat_display}</b> <code>({chat_id})</code>\n\n"

            text += "💡 <b>Использование:</b>\n"
            text += "• <code>/unban 1</code> - разблокировать по номеру\n"
            text += "• <code>/unban &lt;user_id&gt; [chat_id]</code> - разблокировать по ID"

            await message.answer(text)
            return

        # Обработка выбора по номеру
        if args[0].isdigit() and 1 <= int(args[0]) <= 5:
            banned_users = await moderation_service.get_banned_users(limit=5)
            user_index = int(args[0]) - 1

            if 0 <= user_index < len(banned_users):
                log_entry = banned_users[user_index]
                user_id = log_entry.user_id
                chat_id = log_entry.chat_id

                # Разблокируем пользователя
                success = await moderation_service.unban_user(user_id=user_id, chat_id=chat_id, admin_id=admin_id)

                if success:
                    await message.answer(f"✅ Пользователь <code>{sanitize_for_logging(str(user_id))}</code> разблокирован в чате <code>{sanitize_for_logging(str(chat_id))}</code>")
                    logger.info(f"User {sanitize_for_logging(str(user_id))} unbanned by admin {sanitize_for_logging(str(admin_id))}")
                else:
                    await message.answer(f"❌ Не удалось разблокировать пользователя <code>{sanitize_for_logging(str(user_id))}</code>")
            else:
                await message.answer("❌ Неверный номер пользователя")
            return

        # Обработка по user_id
        try:
            user_id = int(args[0])
            chat_id = int(args[1]) if len(args) > 1 else None

            # Разблокируем пользователя
            success = await moderation_service.unban_user(user_id=user_id, chat_id=chat_id, admin_id=admin_id)

            if success:
                chat_info = f" в чате <code>{sanitize_for_logging(str(chat_id))}</code>" if chat_id else ""
                await message.answer(f"✅ Пользователь <code>{sanitize_for_logging(str(user_id))}</code> разблокирован{chat_info}")
                logger.info(f"User {sanitize_for_logging(str(user_id))} unbanned by admin {sanitize_for_logging(str(admin_id))}")
            else:
                await message.answer(f"❌ Не удалось разблокировать пользователя <code>{sanitize_for_logging(str(user_id))}</code>")

        except ValueError:
            await message.answer("❌ Неверный формат ID пользователя или чата")

    except Exception as e:
        logger.error(f"Error in unban command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка разблокировки пользователя")


@moderation_router.message(Command("force_unban"))
async def handle_force_unban_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Принудительный разбан пользователя по ID или username."""
    try:
        if not message.from_user:
            return
        logger.info(f"Force unban command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            await message.answer(
                "❌ <b>Использование:</b> /force_unban &lt;user_id&gt; [chat_id] или /force_unban @username [chat_id]\n\n"
                "💡 <b>Примеры:</b>\n"
                "• /force_unban 123456789\n"
                "• /force_unban @username\n"
                "• /force_unban 123456789 -1001234567890"
            )
            return

        user_identifier = args[0]
        chat_id = int(args[1]) if len(args) > 1 else None

        # Определяем user_id
        user_id = None
        if user_identifier.startswith("@"):
            # Это username, нужно найти user_id
            username = user_identifier[1:]  # Убираем @
            try:
                # Пытаемся получить информацию о пользователе через Telegram API
                user_info = await moderation_service.bot.get_chat_member(chat_id=chat_id, user_id=int(username))
                user_id = user_info.user.id
                logger.info(f"Found user_id {sanitize_for_logging(str(user_id))} for username @{sanitize_for_logging(username)}")
            except Exception as e:
                await message.answer(f"❌ Не удалось найти пользователя @{sanitize_for_logging(username)}: {sanitize_for_logging(str(e))}")
                return
        else:
            # Это user_id
            try:
                user_id = int(user_identifier)
            except ValueError:
                await message.answer(f"❌ Неверный формат ID пользователя: {sanitize_for_logging(str(user_identifier))}")
                return

        # Проверяем, что чат существует и бот может в нем работать
        if chat_id:
            try:
                chat_info = await moderation_service.bot.get_chat(chat_id)
                logger.info(f"Chat info: {chat_info.title} ({chat_id})")
            except Exception as e:
                await message.answer(f"❌ Не удалось получить информацию о чате {chat_id}: {sanitize_for_logging(str(e))}")
                return

        # Принудительно разблокируем пользователя
        success = await moderation_service.unban_user(user_id=user_id, chat_id=chat_id, admin_id=admin_id)

        if success:
            chat_info = f" в чате <code>{sanitize_for_logging(str(chat_id))}</code>" if chat_id else " во всех чатах"
            await message.answer(
                f"✅ <b>Принудительный разбан выполнен</b>\n\n"
                f"👤 <b>Пользователь:</b> <code>{sanitize_for_logging(str(user_id))}</code>\n"
                f"📍 <b>Область:</b> {chat_info}\n"
                f"🔓 <b>Статус:</b> Разблокирован"
            )
            logger.info(f"Force unban completed for user {sanitize_for_logging(str(user_id))} by admin {sanitize_for_logging(str(admin_id))}")
        else:
            await message.answer(f"❌ Не удалось выполнить принудительный разбан пользователя <code>{sanitize_for_logging(str(user_id))}</code>")

    except Exception as e:
        logger.error(f"Error in force_unban command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка принудительного разбана")


@moderation_router.message(Command("banned"))
async def handle_banned_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Показать список заблокированных пользователей."""
    try:
        if not message.from_user:
            return
        logger.info(f"Banned command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем заблокированных пользователей
        banned_users = await moderation_service.get_banned_users(limit=20)

        if not banned_users:
            await message.answer("✅ Нет заблокированных пользователей")
            return

        text = "🚫 <b>Заблокированные пользователи</b>\n\n"

        for i, log_entry in enumerate(banned_users, 1):
            user_id = log_entry.user_id
            reason = log_entry.reason or "Спам"
            chat_id = log_entry.chat_id
            date_text = log_entry.created_at.strftime("%d.%m.%Y %H:%M") if log_entry.created_at else "Неизвестно"

            # Получаем информацию о пользователе
            user_info = await profile_service.get_user_info(int(str(user_id)))
            user_display = (
                f"@{user_info.get('username')}"
                if user_info.get("username")
                else f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            )
            if not user_display or user_display == "Unknown User":
                user_display = f"User {user_id}"

            # Получаем информацию о чате
            chat_info = (
                await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
            )
            chat_display = f"@{chat_info.get('username')}" if chat_info.get("username") else chat_info.get("title", "Unknown Chat")

            text += f"{i}. <b>{user_display}</b> <code>({user_id})</code>\n"
            text += f"   Причина: {reason}\n"
            text += f"   Чат: <b>{chat_display}</b> <code>({chat_id})</code>\n"
            text += f"   Дата: {date_text}\n\n"

        text += "💡 <b>Для разблокировки используйте:</b> /unban"

        await message.answer(text)
        logger.info(f"Banned users list sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in banned command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка заблокированных")


@moderation_router.message(Command("ban_history"))
async def handle_ban_history_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Показать историю банов."""
    try:
        if not message.from_user:
            return
        logger.info(f"Ban history command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем историю банов
        ban_logs = await moderation_service.get_ban_history(limit=50)

        if not ban_logs:
            await message.answer("📋 История банов пуста")
            return

        # Группируем по чатам
        bans_by_chat = {}
        for log_entry in ban_logs:
            chat_id = log_entry.chat_id
            if chat_id not in bans_by_chat:
                bans_by_chat[chat_id] = []
            bans_by_chat[chat_id].append(log_entry)

        text = "📋 <b>История банов</b>\n\n"

        entry_number = 1
        for chat_id, chat_bans in bans_by_chat.items():
            # Получаем информацию о чате
            chat_info = (
                await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
            )
            chat_display = f"@{chat_info.get('username')}" if chat_info.get("username") else chat_info.get("title", "Unknown Chat")
            
            text += f"<b>💬 {chat_display}</b> <code>({chat_id})</code>\n"
            
            for log_entry in chat_bans:
                user_id = log_entry.user_id
                reason = log_entry.reason or "Спам"
                date_text = log_entry.created_at.strftime("%d.%m.%Y %H:%M") if log_entry.created_at else "Неизвестно"
                is_active = "🟢 Активен" if log_entry.is_active else "🔴 Неактивен"

                # Получаем информацию о пользователе
                user_info = await profile_service.get_user_info(int(str(user_id)))
                
                # Формируем отображение пользователя
                if user_info.get("username"):
                    user_display = f"@{user_info.get('username')}"
                else:
                    first_name = user_info.get("first_name", "")
                    last_name = user_info.get("last_name", "")
                    full_name = f"{first_name} {last_name}".strip()
                    user_display = full_name if full_name else f"User {user_id}"

                text += f"  {entry_number}. <b>{user_display}</b> <code>({user_id})</code>\n"
                text += f"     Причина: {reason}\n"
                text += f"     Статус: {is_active}\n"
                text += f"     Дата: {date_text}\n\n"
                
                entry_number += 1
            
            text += "\n"

        text += "💡 <b>Для синхронизации используйте:</b>\n"
        text += "• <code>/sync_bans &lt;chat_id&gt;</code>\n"
        text += "• <code>/sync_bans 1</code> - синхронизировать по номеру"

        await message.answer(text)
        logger.info(f"Ban history sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in ban_history command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения истории банов")


@moderation_router.message(Command("sync_bans"))
async def handle_sync_bans_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Синхронизация банов с Telegram."""
    try:
        if not message.from_user:
            return
        logger.info(f"Sync bans command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            # Показываем последние чаты для синхронизации
            recent_chats = await moderation_service.get_recent_chats(limit=5)

            if not recent_chats:
                await message.answer("❌ Нет чатов для синхронизации")
                return

            text = "🔄 <b>Выберите чат для синхронизации банов:</b>\n\n"

            for i, chat_id in enumerate(recent_chats, 1):
                # Получаем информацию о чате
                chat_info = (
                    await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
                )
                chat_display = f"@{chat_info.get('username')}" if chat_info.get("username") else chat_info.get("title", "Unknown Chat")
                
                text += f"{i}. <b>{chat_display}</b> <code>({chat_id})</code>\n"

            text += "\n💡 <b>Использование:</b>\n"
            text += "• <code>/sync_bans 1</code> - синхронизировать по номеру\n"
            text += "• <code>/sync_bans &lt;chat_id&gt;</code> - синхронизировать по ID\n"
            text += "• <code>/sync_bans &lt;user_id&gt; &lt;chat_id&gt;</code> - синхронизировать конкретного пользователя"

            await message.answer(text)
            return

        if len(args) == 1:
            # Синхронизация по номеру или chat_id
            if args[0].isdigit() and 1 <= int(args[0]) <= 5:
                # По номеру
                recent_chats = await moderation_service.get_recent_chats(limit=5)
                chat_index = int(args[0]) - 1
                
                if 0 <= chat_index < len(recent_chats):
                    chat_id = recent_chats[chat_index]
                    result = await moderation_service.sync_bans_with_telegram(chat_id)
                    
                    if result['success']:
                        await message.answer(f"✅ Синхронизация завершена для чата {chat_id}\n\n{result['message']}")
                    else:
                        await message.answer(f"⚠️ {result['message']}")
                else:
                    await message.answer("❌ Неверный номер чата")
            else:
                # По chat_id
                try:
                    chat_id = int(args[0])
                    result = await moderation_service.sync_bans_with_telegram(chat_id)
                    
                    if result['success']:
                        await message.answer(f"✅ Синхронизация завершена для чата {chat_id}\n\n{result['message']}")
                    else:
                        await message.answer(f"⚠️ {result['message']}")
                except ValueError:
                    await message.answer("❌ Неверный формат ID чата")
        else:
            # user_id и chat_id - синхронизируем конкретного пользователя
            try:
                user_id = int(args[0])
                chat_id = int(args[1])
                # Если ID положительный и длинный, добавляем минус для групп/каналов
                if chat_id > 0 and len(str(chat_id)) >= 10:
                    chat_id = -chat_id
            except ValueError:
                await message.answer("❌ Неверный формат ID пользователя или чата")
                return
            
            try:
                # Проверяем статус пользователя в Telegram
                member = await moderation_service.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                telegram_status = member.status
                
                # Проверяем статус в базе данных
                is_banned_db = await moderation_service.is_user_banned(user_id)
                
                # Синхронизируем статус
                if telegram_status in ["kicked", "left"] and not is_banned_db:
                    # Пользователь заблокирован в Telegram, но не в БД - добавляем в БД
                    await moderation_service.ban_user(user_id, chat_id, "Синхронизация с Telegram", admin_id)
                    await message.answer(f"✅ Пользователь {user_id} добавлен в базу банов")
                elif telegram_status not in ["kicked", "left"] and is_banned_db:
                    # Пользователь не заблокирован в Telegram, но в БД - разблокируем
                    await moderation_service.unban_user(user_id, chat_id, admin_id)
                    await message.answer(f"✅ Пользователь {user_id} разблокирован")
                else:
                    await message.answer(f"ℹ️ Статус пользователя {user_id} уже синхронизирован")
                    
            except Exception as e:
                await message.answer(f"❌ Ошибка синхронизации: {sanitize_for_logging(str(e))}")

    except Exception as e:
        logger.error(f"Error in sync_bans command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка синхронизации банов")
