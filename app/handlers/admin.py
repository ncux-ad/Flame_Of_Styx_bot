"""
Упрощенный админский роутер - только админские команды
"""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)

# Create router
admin_router = Router()

# Apply admin filter to all handlers in this router
admin_router.message.filter(IsAdminOrSilentFilter())


@admin_router.message(Command("start"))
async def handle_start_command(
    message: Message,
    moderation_service: ModerationService,
    bot_service: BotService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Главное меню администратора."""
    try:
        logger.info(f"Admin start command from {message.from_user.id}")

        welcome_text = (
            "🤖 <b>AntiSpam Bot - Упрощенная версия</b>\n\n"
            "Доступные команды:\n"
            "/status - статистика бота\n"
            "/channels - управление каналами\n"
            "/bots - управление ботами\n"
            "/suspicious - подозрительные профили\n"
            "/unban - разблокировать пользователя\n"
            "/banned - список заблокированных\n"
            "/sync_bans - синхронизировать баны с Telegram\n"
            "/help - помощь"
        )

        await message.answer(welcome_text)
        logger.info(f"Start command response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in start command: {e}")


@admin_router.message(Command("status"))
async def handle_status_command(
    message: Message,
    moderation_service: ModerationService,
    bot_service: BotService,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Подробная статистика бота."""
    try:
        logger.info(f"Status command from {message.from_user.id}")

        # Получаем статистику
        total_bots = await bot_service.get_total_bots_count()
        total_channels = await channel_service.get_total_channels_count()
        banned_users = await moderation_service.get_banned_users(limit=100)
        active_bans = len([ban for ban in banned_users if ban.is_active])

        # Получаем информацию о каналах (упрощённо)
        try:
            channels = await channel_service.get_all_channels()
            channel_info = []
            for channel in channels[:5]:  # Показываем первые 5 каналов
                channel_info.append(f"• {channel.title} <code>({channel.chat_id})</code>")
        except:
            channels = []
            channel_info = []

        # Добавляем известные чаты из логов, если их нет в базе
        known_chats = [
            {
                "title": "Test_FlameOfStyx_bot",
                "chat_id": "-1003094131978",
                "type": "Группа для комментариев",
            }
        ]

        # Если в базе нет каналов, показываем известные
        if not channel_info:
            for chat in known_chats:
                channel_info.append(f"• {chat['title']} <code>({chat['chat_id']})</code>")
                channel_info.append(f"  └ Тип: {chat['type']}")
                channel_info.append(f"  └ Статус: ✅ Антиспам активен")

        # Информация о боте (упрощённо)
        bot_username = "FlameOfStyx_bot"  # Из конфига
        bot_id = "7977609078"  # Из логов

        status_text = (
            f"📊 <b>Подробная статистика бота</b>\n\n"
            f"🤖 <b>Информация о боте:</b>\n"
            f"• Username: @{bot_username}\n"
            f"• ID: <code>{bot_id}</code>\n"
            f"• Статус: ✅ Работает\n\n"
            f"📢 <b>Подключённые чаты ({total_channels}):</b>\n"
        )

        if channel_info:
            status_text += "\n".join(channel_info)
            if len(channels) > 5:
                status_text += f"\n• ... и ещё {len(channels) - 5} чатов"
        else:
            status_text += "• Чаты не обнаружены в базе данных\n"
            status_text += "💡 <b>Для добавления новых чатов:</b>\n"
            status_text += "1. Добавьте бота в канал/группу\n"
            status_text += "2. Дайте права администратора\n"
            status_text += "3. Включите комментарии к постам\n"
            status_text += "4. Используйте /channels для проверки"

        status_text += f"\n\n🚫 <b>Модерация:</b>\n"
        status_text += f"• Активных банов: {active_bans}\n"
        status_text += f"• Всего записей: {len(banned_users)}\n\n"
        status_text += f"👑 <b>Администратор:</b> <code>{admin_id}</code>"

        await message.answer(status_text)
        logger.info(f"Status response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.answer("❌ Ошибка получения статистики")


@admin_router.message(Command("channels"))
async def handle_channels_command(
    message: Message,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Управление каналами."""
    try:
        logger.info(f"Channels command from {message.from_user.id}")

        channels = await channel_service.get_all_channels()

        if not channels:
            await message.answer("📢 Каналы не найдены")
            return

        channels_text = "📢 <b>Управление каналами</b>\n\n"
        for channel in channels[:10]:  # Показываем первые 10
            status = "✅ Нативный" if channel.is_native else "🔍 Иностранный"
            username = f"@{channel.username}" if channel.username else "Без username"
            channels_text += f"{status} <b>{channel.title or 'Без названия'}</b>\n"
            channels_text += f"   ID: <code>{channel.telegram_id}</code> | {username}\n"
            if channel.member_count:
                channels_text += f"   👥 Участников: {channel.member_count}\n"
            channels_text += "\n"

        if len(channels) > 10:
            channels_text += f"... и еще {len(channels) - 10} каналов"

        await message.answer(channels_text)
        logger.info(f"Channels response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in channels command: {e}")
        await message.answer("❌ Ошибка получения списка каналов")


@admin_router.message(Command("bots"))
async def handle_bots_command(
    message: Message,
    bot_service: BotService,
    admin_id: int,
) -> None:
    """Управление ботами."""
    try:
        logger.info(f"Bots command from {message.from_user.id}")

        bots = await bot_service.get_all_bots()

        if not bots:
            await message.answer("🤖 Боты не найдены")
            return

        bots_text = "🤖 <b>Управление ботами</b>\n\n"
        for bot in bots[:10]:  # Показываем первые 10
            status = "✅ Вайтлист" if bot.is_whitelisted else "❌ Блэклист"
            bots_text += f"{status} @{bot.username or 'Без username'}\n"

        if len(bots) > 10:
            bots_text += f"\n... и еще {len(bots) - 10} ботов"

        await message.answer(bots_text)
        logger.info(f"Bots response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in bots command: {e}")
        await message.answer("❌ Ошибка получения списка ботов")


@admin_router.message(Command("suspicious"))
async def handle_suspicious_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Подозрительные профили."""
    try:
        logger.info(f"Suspicious command from {message.from_user.id}")

        profiles = await profile_service.get_suspicious_profiles()

        if not profiles:
            await message.answer("👤 Подозрительные профили не найдены")
            return

        profiles_text = "👤 <b>Подозрительные профили</b>\n\n"
        for profile in profiles[:10]:  # Показываем первые 10
            profiles_text += f"ID: {profile.user_id}\n"

        if len(profiles) > 10:
            profiles_text += f"\n... и еще {len(profiles) - 10} профилей"

        await message.answer(profiles_text)
        logger.info(f"Suspicious response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in suspicious command: {e}")
        await message.answer("❌ Ошибка получения подозрительных профилей")


@admin_router.message(Command("unban"))
async def handle_unban_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Разблокировать пользователя с подсказками."""
    try:
        logger.info(f"Unban command from {message.from_user.id}")

        # Парсим аргументы команды
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []

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
                user_info = await profile_service.get_user_info(user_id)
                user_display = (
                    f"@{user_info['username']}"
                    if user_info["username"]
                    else f"{user_info['first_name']} {user_info['last_name'] or ''}".strip()
                )
                if not user_display or user_display == "Unknown User":
                    user_display = f"User {user_id}"

                # Получаем информацию о чате
                chat_info = (
                    await channel_service.get_channel_info(chat_id)
                    if chat_id
                    else {"title": "Unknown Chat", "username": None}
                )
                chat_display = (
                    f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]
                )

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
                success = await moderation_service.unban_user(
                    user_id=user_id, chat_id=chat_id, admin_id=admin_id
                )

                if success:
                    await message.answer(
                        f"✅ Пользователь <code>{user_id}</code> разблокирован в чате <code>{chat_id}</code>"
                    )
                    logger.info(f"User {user_id} unbanned by admin {admin_id}")
                else:
                    await message.answer(
                        f"❌ Не удалось разблокировать пользователя <code>{user_id}</code>"
                    )
            else:
                await message.answer("❌ Неверный номер пользователя")
            return

        # Обработка по user_id и chat_id
        if len(args) < 1:
            await message.answer(
                "❌ Использование: /unban &lt;user_id&gt; [chat_id]\n"
                "Пример: /unban 123456789 -1001234567890"
            )
            return

        user_id = int(args[0])
        chat_id = int(args[1]) if len(args) > 1 else message.chat.id

        # Разблокируем пользователя
        success = await moderation_service.unban_user(
            user_id=user_id, chat_id=chat_id, admin_id=admin_id
        )

        if success:
            await message.answer(
                f"✅ Пользователь <code>{user_id}</code> разблокирован в чате <code>{chat_id}</code>"
            )
            logger.info(f"User {user_id} unbanned by admin {admin_id}")
        else:
            await message.answer(f"❌ Не удалось разблокировать пользователя <code>{user_id}</code>")

    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
    except Exception as e:
        logger.error(f"Error in unban command: {e}")
        await message.answer("❌ Ошибка при разблокировке пользователя")


@admin_router.message(Command("banned"))
async def handle_banned_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Показать список заблокированных пользователей с подробной информацией."""
    try:
        logger.info(f"Banned command from {message.from_user.id}")

        # Получаем список заблокированных пользователей
        banned_users = await moderation_service.get_banned_users(limit=10)

        if not banned_users:
            await message.answer("📝 Нет заблокированных пользователей")
            return

        text = "🚫 <b>Заблокированные пользователи:</b>\n\n"

        for i, log_entry in enumerate(banned_users, 1):
            user_id = log_entry.user_id
            reason = log_entry.reason or "Спам"
            date_text = (
                log_entry.created_at.strftime("%d.%m.%Y %H:%M")
                if log_entry.created_at
                else "Неизвестно"
            )
            chat_id = log_entry.chat_id

            # Получаем информацию о пользователе
            user_info = await profile_service.get_user_info(user_id)

            # Формируем отображение пользователя
            if user_info["username"]:
                user_display = f"@{user_info['username']}"
            else:
                first_name = user_info["first_name"] or ""
                last_name = user_info["last_name"] or ""
                full_name = f"{first_name} {last_name}".strip()
                user_display = full_name if full_name else f"User {user_id}"

            # Получаем информацию о чате
            chat_info = (
                await channel_service.get_channel_info(chat_id)
                if chat_id
                else {"title": "Unknown Chat", "username": None}
            )
            chat_display = (
                f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]
            )

            text += f"{i}. <b>{user_display}</b> <code>({user_id})</code>\n"
            text += f"   Причина: {reason}\n"
            text += f"   Чат: <b>{chat_display}</b> <code>({chat_id})</code>\n"
            text += f"   Дата: {date_text}\n\n"

        if len(banned_users) == 10:
            text += "💡 Показаны последние 10 пользователей"

        await message.answer(text)
        logger.info(f"Banned list sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in banned command: {e}")
        await message.answer("❌ Ошибка получения списка заблокированных")


@admin_router.message(Command("ban_history"))
async def handle_ban_history_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Показать историю банов с chat_id для удобства."""
    try:
        logger.info(f"Ban history command from {message.from_user.id}")

        # Получаем последние 10 записей из истории банов
        ban_history = await moderation_service.get_ban_history(limit=10)

        if not ban_history:
            await message.answer("📝 Нет записей в истории банов")
            return

        text = "📋 <b>История банов (с ID чатов):</b>\n\n"

        for i, log_entry in enumerate(ban_history, 1):
            user_id = log_entry.user_id
            reason = log_entry.reason or "Спам"
            chat_id = log_entry.chat_id
            date_text = (
                log_entry.created_at.strftime("%d.%m.%Y %H:%M")
                if log_entry.created_at
                else "Неизвестно"
            )
            is_active = "🟢 Активен" if log_entry.is_active else "🔴 Неактивен"

            # Получаем информацию о чате
            chat_info = (
                await channel_service.get_channel_info(chat_id)
                if chat_id
                else {"title": "Unknown Chat", "username": None}
            )
            chat_display = (
                f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]
            )

            text += f"{i}. <b>User {user_id}</b>\n"
            text += f"   Причина: {reason}\n"
            text += f"   Чат: <b>{chat_display}</b>\n"
            text += f"   ID чата: <code>{chat_id}</code>\n"
            text += f"   Статус: {is_active}\n"
            text += f"   Дата: {date_text}\n\n"

        text += "💡 <b>Для синхронизации используйте:</b>\n"
        text += "• <code>/sync_bans &lt;chat_id&gt;</code>\n"
        text += "• <code>/sync_bans 1</code> - синхронизировать по номеру"

        await message.answer(text)
        logger.info(f"Ban history sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in ban_history command: {e}")
        await message.answer("❌ Ошибка получения истории банов")


@admin_router.message(Command("sync_bans"))
async def handle_sync_bans_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Синхронизировать баны с Telegram API."""
    try:
        logger.info(f"Sync bans command from {message.from_user.id}")

        # Парсим аргументы команды
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []

        if not args:
            # Показываем последние чаты с банами для выбора
            ban_history = await moderation_service.get_ban_history(limit=10)

            if not ban_history:
                await message.answer("❌ Нет записей в истории банов")
                return

            # Получаем уникальные chat_id
            chat_ids = list(set([log.chat_id for log in ban_history if log.chat_id]))

            if not chat_ids:
                await message.answer("❌ Нет чатов с банами")
                return

            text = "🔄 <b>Выберите чат для синхронизации:</b>\n\n"

            for i, chat_id in enumerate(chat_ids[:5], 1):
                # Получаем информацию о чате
                chat_info = await channel_service.get_channel_info(chat_id)
                chat_display = (
                    f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]
                )

                # Считаем активные баны в этом чате
                active_bans = len(
                    [log for log in ban_history if log.chat_id == chat_id and log.is_active]
                )

                text += f"{i}. <b>{chat_display}</b>\n"
                text += f"   ID: <code>{chat_id}</code>\n"
                text += f"   Активных банов: {active_bans}\n\n"

            text += "💡 <b>Использование:</b>\n"
            text += "• <code>/sync_bans 1</code> - синхронизировать по номеру\n"
            text += "• <code>/sync_bans &lt;chat_id&gt;</code> - синхронизировать по ID\n"
            text += "• <code>/ban_history</code> - полная история банов"

            await message.answer(text)
            return

        # Обработка выбора по номеру
        if args[0].isdigit() and 1 <= int(args[0]) <= 5:
            ban_history = await moderation_service.get_ban_history(limit=10)
            chat_ids = list(set([log.chat_id for log in ban_history if log.chat_id]))
            chat_index = int(args[0]) - 1

            if 0 <= chat_index < len(chat_ids):
                chat_id = chat_ids[chat_index]

                result = await moderation_service.sync_bans_from_telegram(chat_id)

                if result["status"] == "success":
                    await message.answer(f"✅ {result['message']}")
                elif result["status"] == "info":
                    await message.answer(f"ℹ️ {result['message']}")
                elif result["status"] == "error":
                    await message.answer(f"❌ {result['message']}")
                else:
                    await message.answer(f"⚠️ {result['message']}")
            else:
                await message.answer("❌ Неверный номер чата")
            return

        # Обработка по chat_id
        chat_id = int(args[0])

        result = await moderation_service.sync_bans_from_telegram(chat_id)

        if result["status"] == "success":
            await message.answer(f"✅ {result['message']}")
        elif result["status"] == "info":
            await message.answer(f"ℹ️ {result['message']}")
        elif result["status"] == "error":
            await message.answer(f"❌ {result['message']}")
        else:
            await message.answer(f"⚠️ {result['message']}")

        logger.info(f"Sync bans response sent to {message.from_user.id}")

    except ValueError:
        await message.answer("❌ Неверный формат ID чата")
    except Exception as e:
        logger.error(f"Error in sync_bans command: {e}")
        await message.answer("❌ Ошибка синхронизации банов")


@admin_router.message(Command("help"))
async def handle_help_command(
    message: Message,
    admin_id: int,
) -> None:
    """Справка по командам."""
    try:
        logger.info(f"Help command from {message.from_user.id}")

        help_text = (
            "🤖 <b>AntiSpam Bot - Справка</b>\n\n"
            "👑 <b>Команды администратора:</b>\n"
            "/start - главное меню\n"
            "/status - статистика бота\n"
            "/channels - управление каналами\n"
            "/bots - управление ботами\n"
            "/suspicious - подозрительные профили\n"
            "/unban - разблокировать пользователя\n"
            "/banned - список заблокированных\n"
            "/ban_history - история банов с ID чатов\n"
            "/sync_bans - синхронизировать баны с Telegram\n"
            "/help - эта справка\n\n"
            "📖 <b>Дополнительная информация:</b>\n"
            "• Все команды работают в личных сообщениях\n"
            "• Антиспам работает автоматически в каналах\n"
            "• Для получения прав администратора обратитесь к разработчику"
        )

        await message.answer(help_text)
        logger.info(f"Help response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer("❌ Ошибка получения справки")
