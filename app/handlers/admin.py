"""
Упрощенный админский роутер - только админские команды
"""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService

# from app.utils.security import safe_format_message, sanitize_for_logging

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
        if not message.from_user:
            return
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
        if not message.from_user:
            return
        logger.info(f"Status command from {message.from_user.id}")

        # Получаем статистику
        # total_bots = await bot_service.get_total_bots_count()
        total_channels = await channel_service.get_total_channels_count()
        banned_users = await moderation_service.get_banned_users(limit=100)
        active_bans = len([ban for ban in banned_users if ban.is_active])

        # Получаем статистику спама
        spam_stats = await moderation_service.get_spam_statistics()
        deleted_messages = spam_stats["deleted_messages"]
        total_actions = spam_stats["total_actions"]

        # Получаем информацию о каналах из базы данных
        try:
            channels = await channel_service.get_all_channels()
        except Exception:
            channels = []

        # Добавляем известные чаты, где бот активен
        known_chats = [
            {
                "title": "Test_FlameOfStyx_bot",
                "chat_id": "-1003094131978",
                "type": "Группа для комментариев",
            }
        ]

        # Формируем информацию о чатах
        channel_info = []

        # Добавляем каналы из базы данных
        for channel in channels[:5]:  # Показываем первые 5 каналов
            channel_info.append(f"• {channel.title} <code>({channel.telegram_id})</code>")
            channel_info.append("  └ Тип: Канал")
            channel_info.append("  └ Статус: ✅ Антиспам активен")

        # Добавляем известные чаты (группы комментариев)
        for chat in known_chats:
            channel_info.append(f"• {chat['title']} <code>({chat['chat_id']})</code>")
            channel_info.append(f"  └ Тип: {chat['type']}")
            channel_info.append("  └ Статус: ✅ Антиспам активен")

        # Информация о боте (упрощённо)
        bot_username = "FlameOfStyx_bot"  # Из конфига
        bot_id = "7977609078"  # Из логов

        # Подсчитываем общее количество чатов
        total_connected_chats = len(channels) + len(known_chats)

        status_text = (
            "📊 <b>Подробная статистика бота</b>\n\n"
            "🤖 <b>Информация о боте:</b>\n"
            f"• Username: @{bot_username}\n"
            f"• ID: <code>{bot_id}</code>\n"
            "• Статус: ✅ Работает\n\n"
            f"📢 <b>Подключённые чаты ({total_connected_chats}):</b>\n"
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

        status_text += "\n\n🚫 <b>Модерация:</b>\n"
        status_text += f"• Активных банов: {active_bans}\n"
        status_text += f"• Всего записей: {len(banned_users)}\n"
        status_text += f"• Удалено спам-сообщений: {deleted_messages}\n"
        status_text += f"• Всего действий модерации: {total_actions}\n\n"
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
        if not message.from_user:
            return
        logger.info(f"Channels command from {message.from_user.id}")

        channels = await channel_service.get_all_channels()

        if not channels:
            await message.answer("📢 Каналы не найдены")
            return

        channels_text = "📢 <b>Управление каналами</b>\n\n"
        for channel in channels[:10]:  # Показываем первые 10
            status = "✅ Нативный" if channel.is_native else "🔍 Иностранный"
            username = f"@{channel.username}" if channel.username else "Без username"
            channels_text += f"<b>{channel.title or 'Без названия'}</b>\n"
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
        if not message.from_user:
            return
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
        if not message.from_user:
            return
        logger.info(f"Suspicious command from {message.from_user.id}")

        profiles = await profile_service.get_suspicious_profiles()

        if not profiles:
            await message.answer("👤 Подозрительные профили не найдены")
            return

        profiles_text = "👤 <b>Подозрительные профили</b>\n\n"

        for i, profile in enumerate(profiles[:10], 1):  # Показываем первые 10
            # Получаем информацию о пользователе
            user_info = await profile_service.get_user_info(profile.user_id)

            profiles_text += f"<b>{i}. Пользователь {profile.user_id}</b>\n"
            profiles_text += f"• <b>Имя:</b> {user_info.get('first_name', 'Неизвестно')}\n"
            if user_info.get("username"):
                profiles_text += f"• <b>Username:</b> @{user_info['username']}\n"
            profiles_text += f"• <b>Счет подозрительности:</b> {profile.suspicion_score:.2f}\n"

            if profile.linked_chat_title and profile.linked_chat_title.strip():
                profiles_text += f"• <b>Связанный канал:</b> {profile.linked_chat_title}\n"
                if profile.linked_chat_username and profile.linked_chat_username.strip():
                    profiles_text += f"• <b>Username канала:</b> @{profile.linked_chat_username}\n"

            if profile.detected_patterns and profile.detected_patterns.strip():
                patterns = profile.detected_patterns.split(",") if profile.detected_patterns else []
                pattern_names = {
                    "short_first_name": "Короткое имя",
                    "short_last_name": "Короткая фамилия",
                    "no_identifying_info": "Нет идентификаторов",
                    "bot_like_username": "Bot-подобный username",
                    "no_username": "Нет username",
                    "no_last_name": "Нет фамилии",
                    "bot_like_first_name": "Bot-подобное имя",
                }
                pattern_text = ", ".join([pattern_names.get(p, p) for p in patterns if p])
                profiles_text += f"• <b>Паттерны:</b> {pattern_text}\n"

            if profile.is_reviewed:
                status = (
                    "✅ Подтвержден"
                    if profile.is_confirmed_suspicious
                    else "❌ Ложное срабатывание"
                )
                profiles_text += f"• <b>Статус:</b> {status}\n"
            else:
                profiles_text += f"• <b>Статус:</b> ⏳ Ожидает проверки\n"

            profiles_text += f"• <b>Дата:</b> {profile.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

        if len(profiles) > 10:
            profiles_text += f"<i>... и еще {len(profiles) - 10} профилей</i>"

        await message.answer(profiles_text)
        logger.info(f"Suspicious response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in suspicious command: {e}")
        await message.answer("❌ Ошибка получения подозрительных профилей")


@admin_router.message(Command("reset_suspicious"))
async def handle_reset_suspicious_command(message: Message, profile_service: ProfileService):
    """Reset suspicious profile status for testing."""
    try:
        # Reset all suspicious profiles to unreviewed status
        result = await profile_service.reset_suspicious_profiles()

        if result > 0:
            await message.answer(f"✅ Сброшено статусов подозрительных профилей: {result}")
        else:
            await message.answer("ℹ️ Нет подозрительных профилей для сброса")

    except Exception as e:
        logger.error(f"Error resetting suspicious profiles: {e}")
        await message.answer(f"❌ Ошибка при сбросе статусов: {e}")


@admin_router.message(Command("recalculate_suspicious"))
async def handle_recalculate_suspicious_command(message: Message, profile_service: ProfileService):
    """Recalculate suspicious profiles with new weights."""
    try:
        # Get all suspicious profiles
        profiles = await profile_service.get_suspicious_profiles(limit=100)

        if not profiles:
            await message.answer("ℹ️ Нет подозрительных профилей для пересчета")
            return

        updated_count = 0
        for profile in profiles:
            # Get user info and recalculate
            user_info = await profile_service.get_user_info(profile.user_id)
            if user_info:
                # Create a mock User object for recalculation
                from aiogram.types import User

                mock_user = User(
                    id=profile.user_id,
                    is_bot=False,
                    first_name=user_info.get("first_name", ""),
                    last_name=user_info.get("last_name"),
                    username=user_info.get("username"),
                    language_code="ru",
                )

                # Recalculate analysis
                analysis_result = await profile_service._perform_profile_analysis(mock_user)

                # Update profile with new score
                if analysis_result["suspicion_score"] != profile.suspicion_score:
                    profile.suspicion_score = analysis_result["suspicion_score"]
                    profile.detected_patterns = ",".join(analysis_result["patterns"])
                    profile.is_suspicious = analysis_result["is_suspicious"]
                    updated_count += 1

        if updated_count > 0:
            await profile_service.db.commit()
            await message.answer(f"✅ Пересчитано профилей: {updated_count}")
        else:
            await message.answer("ℹ️ Нет изменений в профилях")

    except Exception as e:
        logger.error(f"Error recalculating suspicious profiles: {e}")
        await message.answer(f"❌ Ошибка при пересчете: {e}")


@admin_router.message(Command("cleanup_duplicates"))
async def handle_cleanup_duplicates_command(message: Message, profile_service: ProfileService):
    """Clean up duplicate suspicious profiles."""
    try:
        from sqlalchemy import delete, func, select

        from app.models.suspicious_profile import SuspiciousProfile

        # Find users with multiple profiles
        result = await profile_service.db.execute(
            select(SuspiciousProfile.user_id, func.count(SuspiciousProfile.id).label("count"))
            .group_by(SuspiciousProfile.user_id)
            .having(func.count(SuspiciousProfile.id) > 1)
        )

        duplicates = result.fetchall()

        if not duplicates:
            await message.answer("ℹ️ Дублирующих профилей не найдено")
            return

        cleaned_count = 0
        for user_id, count in duplicates:
            # Keep the most recent profile, delete others
            profiles = await profile_service.db.execute(
                select(SuspiciousProfile)
                .where(SuspiciousProfile.user_id == user_id)
                .order_by(SuspiciousProfile.created_at.desc())
            )
            profiles_list = profiles.scalars().all()

            # Delete all except the first (most recent)
            for profile in profiles_list[1:]:
                await profile_service.db.delete(profile)
                cleaned_count += 1

        await profile_service.db.commit()
        await message.answer(f"✅ Удалено дублирующих профилей: {cleaned_count}")

    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {e}")
        await message.answer(f"❌ Ошибка при очистке: {e}")


@admin_router.message(Command("settings"))
async def handle_settings_command(message: Message) -> None:
    """Настройки бота."""
    try:
        if not message.from_user:
            return
        logger.info(f"Settings command from {message.from_user.id}")

        settings_text = (
            "⚙️ <b>Настройки бота</b>\n\n"
            "🔧 <b>Текущие настройки:</b>\n"
            "• Система подозрительных профилей: ✅ Включена\n"
            "• Порог подозрительности: 0.2\n"
            "• Автоматическая модерация: ✅ Включена\n"
            "• Логирование: ✅ Включено\n\n"
            "📊 <b>Статистика:</b>\n"
            "• Middleware активен\n"
            "• DI сервисы загружены\n"
            "• База данных подключена\n\n"
            "ℹ️ Для изменения настроек обратитесь к разработчику"
        )

        await message.answer(settings_text)
        if message.from_user:
            logger.info(f"Settings response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in settings command: {e}")


@admin_router.message(Command("setlimits"))
async def handle_setlimits_command(message: Message, limits_service: LimitsService) -> None:
    """Просмотр лимитов системы."""
    try:
        if not message.from_user:
            return
        logger.info(f"Setlimits command from {message.from_user.id}")

        limits_text = (
            "🔒 <b>Управление лимитами</b>\n\n" "👑 <b>Доступно администраторам</b>\n\n"
        ) + limits_service.get_limits_display()

        await message.answer(limits_text)
        if message.from_user:
            logger.info(f"Setlimits response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in setlimits command: {e}")


@admin_router.message(Command("setlimit"))
async def handle_setlimit_command(message: Message, limits_service: LimitsService) -> None:
    """Изменение конкретного лимита."""
    try:
        if not message.from_user:
            return
        logger.info(f"Setlimit command from {message.from_user.id}")

        # Парсим команду: /setlimit <тип> <значение>
        text = message.text or ""
        parts = text.split()

        if len(parts) < 3:
            await message.answer(
                "❌ <b>Неверный формат команды</b>\n\n"
                "Используйте: /setlimit &lt;тип&gt; &lt;значение&gt;\n\n"
                "📋 <b>Доступные типы:</b>\n"
                "• messages - максимум сообщений в минуту\n"
                "• links - максимум ссылок в сообщении\n"
                "• ban - время блокировки в часах\n"
                "• threshold - порог подозрительности\n\n"
                "💡 <b>Примеры:</b>\n"
                "• /setlimit messages 15\n"
                "• /setlimit links 5\n"
                "• /setlimit ban 48\n"
                "• /setlimit threshold 0.3"
            )
            return

        limit_type = parts[1].lower()
        try:
            value = float(parts[2]) if limit_type == "threshold" else int(parts[2])
        except ValueError:
            await message.answer("❌ Значение должно быть числом!")
            return

        # Маппинг типов лимитов
        limit_mapping = {
            "messages": "max_messages_per_minute",
            "links": "max_links_per_message",
            "ban": "ban_duration_hours",
            "threshold": "suspicion_threshold",
        }

        if limit_type not in limit_mapping:
            await message.answer(
                "❌ <b>Неверный тип лимита</b>\n\n"
                "📋 <b>Доступные типы:</b>\n"
                "• messages - максимум сообщений в минуту\n"
                "• links - максимум ссылок в сообщении\n"
                "• ban - время блокировки в часах\n"
                "• threshold - порог подозрительности"
            )
            return

        # Обновляем лимит
        success = limits_service.update_limit(limit_mapping[limit_type], value)

        if success:
            await message.answer(
                f"✅ <b>Лимит обновлен!</b>\n\n"
                f"📊 <b>{limit_type}</b> изменен на <b>{value}</b>\n\n"
                "🔄 Изменения вступят в силу после перезапуска бота"
            )
        else:
            await message.answer("❌ Ошибка при обновлении лимита!")

        if message.from_user:
            logger.info(f"Setlimit response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in setlimit command: {e}")
        await message.answer("❌ Ошибка при обработке команды!")


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
        if not message.from_user:
            return
        logger.info(f"Unban command from {message.from_user.id}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
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
            await message.answer(
                f"❌ Не удалось разблокировать пользователя <code>{user_id}</code>"
            )

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
        if not message.from_user:
            return
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
        if not message.from_user:
            return
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
        if not message.from_user:
            return
        logger.info(f"Sync bans command from {message.from_user.id}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
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
    help_service: HelpService,
) -> None:
    """Справка по командам."""
    try:
        if not message.from_user:
            return
        logger.info(f"Help command from {message.from_user.id}")

        # Используем HelpService для получения актуальной справки
        help_text = help_service.get_main_help(is_admin=True)

        await message.answer(help_text)
        if message.from_user:
            logger.info(f"Help response sent to {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer("❌ Ошибка получения справки")


# Обработчики callback для подозрительных профилей
@admin_router.callback_query(lambda c: c.data and c.data.startswith("ban_suspicious:"))
async def handle_ban_suspicious_callback(
    callback_query: CallbackQuery,
    moderation_service: ModerationService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Забанить подозрительного пользователя."""
    try:
        if not callback_query.from_user:
            return

        user_id = int(callback_query.data.split(":")[1]) if callback_query.data else 0

        # Получаем информацию о пользователе
        user_info = await profile_service.get_user_info(user_id)

        # Получаем профиль для получения счета подозрительности
        profile = await profile_service._get_suspicious_profile(user_id)
        suspicion_score = profile.suspicion_score if profile else 0.0

        # Баним пользователя
        success = await moderation_service.ban_user(
            user_id=user_id,
            chat_id=callback_query.message.chat.id if callback_query.message else 0,
            reason=f"Подозрительный профиль (счет: {suspicion_score:.2f})",
            admin_id=admin_id,
        )

        if success:
            # Отмечаем профиль как проверенный и подтвержденный
            await profile_service.mark_profile_as_reviewed(
                user_id=user_id,
                admin_id=admin_id,
                is_confirmed=True,
                notes="Забанен за подозрительный профиль",
            )

            await callback_query.answer("✅ Пользователь забанен")
            if callback_query.message:
                await callback_query.message.edit_text(
                    f"🚫 <b>Пользователь забанен</b>\n\n"
                    f"ID: {user_id}\n"
                    f"Имя: {user_info.get('first_name', 'Неизвестно')}\n"
                    f"Причина: Подозрительный профиль"
                )
        else:
            await callback_query.answer("❌ Ошибка при бане пользователя")

    except Exception as e:
        logger.error(f"Error in ban_suspicious callback: {e}")
        await callback_query.answer("❌ Ошибка обработки")


@admin_router.callback_query(lambda c: c.data and c.data.startswith("watch_suspicious:"))
async def handle_watch_suspicious_callback(
    callback_query: CallbackQuery,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Пометить подозрительного пользователя для наблюдения."""
    try:
        if not callback_query.from_user:
            return

        user_id = int(callback_query.data.split(":")[1]) if callback_query.data else 0

        # Отмечаем профиль как проверенный, но не подтвержденный
        await profile_service.mark_profile_as_reviewed(
            user_id=user_id, admin_id=admin_id, is_confirmed=False, notes="Помечен для наблюдения"
        )

        await callback_query.answer("👀 Пользователь добавлен в список наблюдения")
        if callback_query.message:
            await callback_query.message.edit_text(
                f"👀 <b>Пользователь добавлен в наблюдение</b>\n\n"
                f"ID: {user_id}\n"
                f"Статус: Наблюдение"
            )

    except Exception as e:
        logger.error(f"Error in watch_suspicious callback: {e}")
        await callback_query.answer("❌ Ошибка обработки")


@admin_router.callback_query(lambda c: c.data and c.data.startswith("allow_suspicious:"))
async def handle_allow_suspicious_callback(
    callback_query: CallbackQuery,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Разрешить подозрительному пользователю (ложное срабатывание)."""
    try:
        if not callback_query.from_user:
            return

        user_id = int(callback_query.data.split(":")[1]) if callback_query.data else 0

        # Отмечаем профиль как проверенный и ложное срабатывание
        await profile_service.mark_profile_as_reviewed(
            user_id=user_id,
            admin_id=admin_id,
            is_confirmed=False,
            notes="Ложное срабатывание - разрешен",
        )

        await callback_query.answer("✅ Пользователь разрешен")
        if callback_query.message:
            await callback_query.message.edit_text(
                f"✅ <b>Пользователь разрешен</b>\n\n"
                f"ID: {user_id}\n"
                f"Статус: Ложное срабатывание"
            )

    except Exception as e:
        logger.error(f"Error in allow_suspicious callback: {e}")
        await callback_query.answer("❌ Ошибка обработки")
