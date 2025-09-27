"""
Упрощенный админский роутер - только админские команды
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.moderation import ModerationService
from app.models.moderation_log import ModerationAction
from app.services.profiles import ProfileService
from app.utils.error_handling import ValidationError, handle_errors
from app.utils.security import sanitize_for_logging, safe_format_message

logger = logging.getLogger(__name__)

# Create router
admin_router = Router()

# Apply admin filter to all handlers in this router
admin_router.message.filter(IsAdminOrSilentFilter())


@admin_router.message(Command("start"))
@handle_errors(user_message="❌ Ошибка выполнения команды /start")
async def handle_start_command(
    message: Message,
    moderation_service: ModerationService,
    bot_service: BotService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Главное меню администратора."""
    if not message.from_user:
        raise ValidationError("Отсутствует информация о пользователе")

    logger.info(f"Admin start command from {sanitize_for_logging(str(message.from_user.id))}")

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
        "/force_unban - принудительный разбан по ID/username\n"
        "/help - помощь"
    )

    await message.answer(welcome_text)
    logger.info(f"Start command response sent to {sanitize_for_logging(str(message.from_user.id))}")


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
        logger.info(f"Status command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем статистику
        # total_bots = await bot_service.get_total_bots_count()
        # total_channels = await channel_service.get_total_channels_count()  # Не используется
        banned_users = await moderation_service.get_banned_users(limit=100)
        active_bans = len([ban for ban in banned_users if ban.is_active])

        # Получаем статистику спама
        spam_stats = await moderation_service.get_spam_statistics()
        deleted_messages = spam_stats["deleted_messages"]
        total_actions = spam_stats["total_actions"]

        # Получаем информацию о каналах из базы данных
        try:
            all_channels = await channel_service.get_all_channels()
        except Exception:
            all_channels = []

        # Фильтруем только каналы, где бот является администратором
        connected_channels = []
        for channel in all_channels:
            try:
                telegram_id = int(channel.telegram_id) if channel.telegram_id is not None else 0 if channel.telegram_id is not None else 0
                is_native = await channel_service.is_native_channel(telegram_id)
                if is_native:
                    connected_channels.append(channel)
            except Exception:
                continue

        # Получаем группы комментариев из базы данных
        comment_groups = []
        for channel in all_channels:
            if hasattr(channel, "is_comment_group") and bool(channel.is_comment_group):
                comment_groups.append(
                    {
                        "title": channel.title or f"Группа {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "type": "Группа для комментариев",
                    }
                )

        # Формируем информацию о чатах
        channel_info = []

        # Добавляем только подключенные каналы (где бот админ)
        for channel in connected_channels[:5]:  # Показываем первые 5 подключенных каналов
            channel_info.append(f"• {channel.title} <code>({channel.telegram_id})</code>")
            channel_info.append("  └ Тип: Канал")
            channel_info.append("  └ Статус: ✅ Антиспам активен")

        # Добавляем группы комментариев
        for chat in comment_groups:
            channel_info.append(f"• {chat['title']} <code>({chat['chat_id']})</code>")
            channel_info.append(f"  └ Тип: {chat['type']}")
            channel_info.append("  └ Статус: ✅ Антиспам активен")

        # Информация о боте (упрощённо)
        # bot_username = "FlameOfStyx_bot"  # Из конфига - не используется
        bot_id = "7977609078"  # Из логов

        # Подсчитываем общее количество чатов
        total_connected_chats = len(connected_channels) + len(comment_groups)

        status_text = (
            "📊 <b>Подробная статистика бота</b>\n\n"
            "🤖 <b>Информация о боте:</b>\n"
            "• Username: @FlameOfStyx_bot\n"
            f"• ID: <code>{bot_id}</code>\n"
            "• Статус: ✅ Работает\n\n"
            f"📢 <b>Подключённые чаты ({total_connected_chats}):</b>\n"
        )

        if channel_info:
            status_text += "\n".join(channel_info)
            if len(connected_channels) > 5:
                status_text += f"\n• ... и ещё {len(connected_channels) - 5} подключенных каналов"
        else:
            status_text += "• Подключенные чаты не обнаружены\n"
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
        logger.info(f"Status response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in status command: {sanitize_for_logging(str(e))}")
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
        logger.info(f"Channels command from {sanitize_for_logging(str(message.from_user.id))}")

        channels = await channel_service.get_all_channels()

        if not channels:
            await message.answer("📢 Каналы не найдены")
            return

        # Разделяем каналы на нативные и иностранные
        native_channels = []
        foreign_channels = []

        for channel in channels:
            # Проверяем, является ли канал нативным (где бот админ)
            telegram_id = int(channel.telegram_id) if channel.telegram_id is not None else 0
            is_native = await channel_service.is_native_channel(telegram_id)
            if is_native:
                native_channels.append(channel)
            else:
                foreign_channels.append(channel)

        channels_text = "📢 <b>Управление каналами</b>\n\n"

        # Показываем нативные каналы (где бот админ)
        if native_channels:
            channels_text += f"✅ <b>Нативные каналы ({len(native_channels)})</b>\n"
            channels_text += "<i>Каналы где бот является администратором</i>\n\n"

            for channel in native_channels[:5]:  # Показываем первые 5 нативных
                username = f"@{channel.username}" if channel.username else "Без username"
                channels_text += f"<b>{channel.title or 'Без названия'}</b>\n"
                channels_text += f"   ID: <code>{channel.telegram_id}</code> | {username}\n"
                if channel.member_count:
                    channels_text += f"   👥 Участников: {channel.member_count}\n"
                channels_text += "\n"

            if len(native_channels) > 5:
                channels_text += f"... и еще {len(native_channels) - 5} нативных каналов\n\n"
            else:
                channels_text += "\n"

        # Показываем иностранные каналы (откуда приходят сообщения)
        if foreign_channels:
            channels_text += f"🔍 <b>Иностранные каналы ({len(foreign_channels)})</b>\n"
            channels_text += "<i>Каналы откуда приходят сообщения (бот не админ)</i>\n\n"

            for channel in foreign_channels[:5]:  # Показываем первые 5 иностранных
                username = f"@{channel.username}" if channel.username else "Без username"
                channels_text += f"<b>{channel.title or 'Без названия'}</b>\n"
                channels_text += f"   ID: <code>{channel.telegram_id}</code> | {username}\n"
                if channel.member_count:
                    channels_text += f"   👥 Участников: {channel.member_count}\n"
                channels_text += "\n"

            if len(foreign_channels) > 5:
                channels_text += f"... и еще {len(foreign_channels) - 5} иностранных каналов\n\n"

        # Получаем группы комментариев из базы данных
        comment_groups = []
        for channel in channels:
            if hasattr(channel, "is_comment_group") and bool(channel.is_comment_group):
                comment_groups.append(
                    {
                        "title": channel.title or f"Группа {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "type": "Группа для комментариев",
                    }
                )

        if comment_groups:
            channels_text += f"\n💬 <b>Группы комментариев ({len(comment_groups)})</b>\n"
            channels_text += "<i>Группы для модерации комментариев к постам</i>\n\n"

            for group in comment_groups:
                channels_text += f"<b>{group['title']}</b>\n"
                channels_text += f"   ID: <code>{group['chat_id']}</code>\n"
                channels_text += f"   Тип: {group['type']}\n"
                channels_text += "   Статус: ✅ Антиспам активен\n\n"

        # Общая статистика
        channels_text += "📊 <b>Общая статистика:</b>\n"
        channels_text += f"• Нативных каналов: {len(native_channels)}\n"
        channels_text += f"• Иностранных каналов: {len(foreign_channels)}\n"
        channels_text += f"• Групп комментариев: {len(comment_groups)}\n"
        channels_text += f"• Всего чатов: {len(channels) + len(comment_groups)}"

        await message.answer(channels_text)
        logger.info(f"Channels response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in channels command: {sanitize_for_logging(str(e))}")
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
        logger.info(f"Bots command from {sanitize_for_logging(str(message.from_user.id))}")

        bots = await bot_service.get_all_bots()

        if not bots:
            await message.answer("🤖 Боты не найдены")
            return

        bots_text = "🤖 <b>Управление ботами</b>\n\n"
        for bot in bots[:10]:  # Показываем первые 10
            is_whitelisted = bool(bot.is_whitelisted)
            status = "✅ Вайтлист" if is_whitelisted else "❌ Блэклист"
            username_value = bot.username
            username = str(username_value) if username_value is not None else "Без username"
            bots_text += f"{status} @{username}\n"

        if len(bots) > 10:
            bots_text += f"\n... и еще {len(bots) - 10} ботов"

        await message.answer(bots_text)
        logger.info(f"Bots response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in bots command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка ботов")




@admin_router.message(Command("settings"))
async def handle_settings_command(message: Message) -> None:
    """Настройки бота."""
    try:
        if not message.from_user:
            return
        logger.info(f"Settings command from {sanitize_for_logging(str(message.from_user.id))}")

        # Load current configuration
        from app.config import load_config

        config = load_config()

        settings_text = (
            "⚙️ <b>Настройки бота</b>\n\n"
            "🔧 <b>Текущие настройки:</b>\n"
            f"• Система подозрительных профилей: ✅ Включена\n"
            f"• Порог подозрительности: {config.suspicion_threshold}\n"
            f"• Автоматическая модерация: ✅ Включена\n"
            f"• Логирование: ✅ Включено\n\n"
            "🛡️ <b>Настройки антиспама:</b>\n"
            f"• Проверка медиа без подписи: {'✅' if config.check_media_without_caption else '❌'}\n"
            f"• Разрешать GIF без подписи: {'✅' if config.allow_videos_without_caption else '❌'}\n"
            f"• Разрешать фото без подписи: {'✅' if config.allow_photos_without_caption else '❌'}\n"
            f"• Разрешать видео без подписи: {'✅' if config.allow_videos_without_caption else '❌'}\n"
            f"• Макс. размер документа для подозрения: {config.max_document_size_suspicious} байт\n\n"
            "📊 <b>Статистика:</b>\n"
            "• Middleware активен\n"
            "• DI сервисы загружены\n"
            "• База данных подключена\n\n"
            "ℹ️ Для изменения настроек используйте команды:\n"
            "• /setlimit threshold &lt;значение&gt; - порог подозрительности\n"
            "• /setlimit media_check &lt;0|1&gt; - проверка медиа без подписи\n"
            "• /setlimit allow_gifs &lt;0|1&gt; - разрешить GIF без подписи\n"
            "• /setlimit allow_photos &lt;0|1&gt; - разрешить фото без подписи\n"
            "• /setlimit allow_videos &lt;0|1&gt; - разрешить видео без подписи\n"
            "• /setlimit doc_size &lt;байты&gt; - размер документа для подозрения"
        )

        await message.answer(settings_text)
        if message.from_user:
            logger.info(f"Settings response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in settings command: {sanitize_for_logging(str(e))}")


@admin_router.message(Command("setlimits"))
async def handle_setlimits_command(message: Message, limits_service: LimitsService) -> None:
    """Просмотр лимитов системы."""
    try:
        if not message.from_user:
            return
        logger.info(f"Setlimits command from {sanitize_for_logging(str(message.from_user.id))}")

        limits_text = (
            "🔒 <b>Управление лимитами</b>\n\n" "👑 <b>Доступно администраторам</b>\n\n"
        ) + limits_service.get_limits_display()

        await message.answer(limits_text)
        if message.from_user:
            logger.info(f"Setlimits response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in setlimits command: {sanitize_for_logging(str(e))}")


@admin_router.message(Command("setlimit"))
async def handle_setlimit_command(message: Message, limits_service: LimitsService) -> None:
    """Изменение конкретного лимита."""
    try:
        if not message.from_user:
            return
        logger.info(f"Setlimit command from {sanitize_for_logging(str(message.from_user.id))}")

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
                "• threshold - порог подозрительности\n"
                "• media_check - проверка медиа без подписи (0/1)\n"
                "• allow_gifs - разрешить GIF без подписи (0/1)\n"
                "• allow_photos - разрешить фото без подписи (0/1)\n"
                "• allow_videos - разрешить видео без подписи (0/1)\n"
                "• doc_size - размер документа для подозрения (байты)\n\n"
                "💡 <b>Примеры:</b>\n"
                "• /setlimit messages 15\n"
                "• /setlimit threshold 0.3\n"
                "• /setlimit allow_gifs 1\n"
                "• /setlimit doc_size 100000"
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
            "media_check": "check_media_without_caption",
            "allow_gifs": "allow_videos_without_caption",
            "allow_photos": "allow_photos_without_caption",
            "allow_videos": "allow_videos_without_caption",
            "doc_size": "max_document_size_suspicious",
        }

        if limit_type not in limit_mapping:
            await message.answer(
                "❌ <b>Неверный тип лимита</b>\n\n"
                "📋 <b>Доступные типы:</b>\n"
                "• messages - максимум сообщений в минуту\n"
                "• links - максимум ссылок в сообщении\n"
                "• ban - время блокировки в часах\n"
                "• threshold - порог подозрительности\n"
                "• media_check - проверка медиа без подписи (0/1)\n"
                "• allow_gifs - разрешить GIF без подписи (0/1)\n"
                "• allow_photos - разрешить фото без подписи (0/1)\n"
                "• allow_videos - разрешить видео без подписи (0/1)\n"
                "• doc_size - размер документа для подозрения (байты)"
            )
            return

        # Обновляем лимит
        success = limits_service.update_limit(limit_mapping[limit_type], value)

        if success:
            await message.answer(
                f"✅ <b>Лимит обновлен!</b>\n\n"
                f"📊 <b>{limit_type}</b> изменен на <b>{value}</b>\n\n"
                "🔄 Изменения применены немедленно благодаря hot-reload!"
            )
        else:
            await message.answer("❌ Ошибка при обновлении лимита!")

        if message.from_user:
            logger.info(f"Setlimit response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in setlimit command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка при обработке команды!")


@admin_router.message(Command("reload_limits"))
async def handle_reload_limits_command(message: Message, limits_service: LimitsService) -> None:
    """Принудительная перезагрузка лимитов из файла."""
    try:
        if not message.from_user:
            return
        logger.info(f"Reload limits command from {sanitize_for_logging(str(message.from_user.id))}")

        # Перезагружаем лимиты
        success = limits_service.reload_limits()

        if success:
            limits = limits_service.get_current_limits()
            await message.answer(
                "🔄 <b>Лимиты перезагружены!</b>\n\n"
                f"📊 <b>Текущие лимиты:</b>\n"
                f"• Сообщений в минуту: {limits['max_messages_per_minute']}\n"
                f"• Ссылок в сообщении: {limits['max_links_per_message']}\n"
                f"• Время блокировки: {limits['ban_duration_hours']} часов\n"
                f"• Порог подозрительности: {limits['suspicion_threshold']}\n\n"
                "✅ Изменения применены немедленно!"
            )
        else:
            await message.answer("❌ Ошибка при перезагрузке лимитов!")

        if message.from_user:
            logger.info(f"Reload limits response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in reload_limits command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка при перезагрузке лимитов!")


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
                    await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
                )
                chat_display = f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]

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

        # Обработка по user_id и chat_id
        if len(args) < 1:
            await message.answer(
                "❌ Использование: /unban &lt;user_id_or_username&gt; [chat_id]\n" 
                "Примеры:\n"
                "• /unban 123456789 -1001234567890\n"
                "• /unban @username -1001234567890"
            )
            return

        user_identifier = args[0]
        if len(args) > 1:
            chat_id = int(args[1])
        else:
            await message.answer("❌ Необходимо указать ID чата: /unban <user_id> <chat_id>")
            return
        
        # Если ID положительный и длинный, добавляем минус для групп/каналов
        if chat_id > 0 and len(str(chat_id)) >= 10:
            chat_id = -chat_id

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

        # Разблокируем пользователя
        success = await moderation_service.unban_user(user_id=user_id, chat_id=chat_id, admin_id=admin_id)

        if success:
            await message.answer(f"✅ Пользователь <code>{user_id}</code> разблокирован в чате <code>{chat_id}</code>")
            logger.info(f"User {sanitize_for_logging(str(user_id))} unbanned by admin {sanitize_for_logging(str(admin_id))}")
        else:
            await message.answer(f"❌ Не удалось разблокировать пользователя <code>{user_id}</code>")

    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
    except Exception as e:
        logger.error(f"Error in unban command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка при разблокировке пользователя")


@admin_router.message(Command("force_unban"))
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

        if len(args) < 2:
            await message.answer(
                "❌ Использование: /force_unban <user_id_or_username> <chat_id>\n"
                "Примеры:\n"
                "• /force_unban 123456789 -1001234567890\n"
                "• /force_unban @username -1001234567890"
            )
            return

        user_identifier = args[0]
        chat_id = int(args[1])
        
        # Если ID положительный и длинный, добавляем минус для групп/каналов
        if chat_id > 0 and len(str(chat_id)) >= 10:
            chat_id = -chat_id

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
        try:
            chat = await moderation_service.bot.get_chat(chat_id)
            logger.info(f"Chat found: {sanitize_for_logging(chat.title or 'Unknown')} (ID: {sanitize_for_logging(str(chat_id))})")
            
            # Проверяем, является ли бот администратором
            try:
                bot_member = await moderation_service.bot.get_chat_member(chat_id, moderation_service.bot.id)
                if bot_member.status not in ["administrator", "creator"]:
                    await message.answer(
                        f"❌ <b>Бот не является администратором в чате:</b>\n\n"
                        f"📝 Название: {chat.title}\n"
                        f"🆔 ID: <code>{chat_id}</code>\n"
                        f"🤖 Статус бота: {bot_member.status}\n\n"
                        f"💡 <b>Для разбана необходимо:</b>\n"
                        f"• Добавить бота как администратора в чат\n"
                        f"• Или использовать чат где бот уже админ\n\n"
                        f"🔍 <b>Используйте команду:</b> <code>/my_chats</code>"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking bot status: {sanitize_for_logging(str(e))}")
                await message.answer(
                    f"❌ <b>Не удалось проверить статус бота в чате:</b>\n\n"
                    f"📝 Название: {chat.title}\n"
                    f"🆔 ID: <code>{chat_id}</code>\n"
                    f"❌ Ошибка: {e}\n\n"
                    f"💡 <b>Возможно бот не является администратором</b>\n"
                    f"🔍 <b>Используйте команду:</b> <code>/my_chats</code>"
                )
                return
                
        except Exception as e:
            logger.error(f"Chat not found: {sanitize_for_logging(str(e))}")
            await message.answer(f"❌ Чат не найден: {sanitize_for_logging(str(e))}")
            return

        # Принудительно разблокируем пользователя
        logger.info(f"Force unbanning user {sanitize_for_logging(str(user_id))} in chat {sanitize_for_logging(str(chat_id))}")
        
        try:
            # Принудительно разблокируем в Telegram
            await moderation_service.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            logger.info(f"Successfully force unbanned user {sanitize_for_logging(str(user_id))} in Telegram chat {sanitize_for_logging(str(chat_id))}")
        except Exception as telegram_error:
            logger.error(f"Telegram API error during force unban: {sanitize_for_logging(str(telegram_error))}")
            await message.answer(f"⚠️ Ошибка Telegram API: {sanitize_for_logging(str(telegram_error))}")
            return

        # Обновляем статус в базе данных
        await moderation_service._update_user_status(user_id, is_banned=False, ban_reason=None)
        
        # Деактивируем все активные баны
        await moderation_service._deactivate_all_user_bans(user_id)
        
        # Логируем действие
        await moderation_service._log_moderation_action(
            action=ModerationAction.UNBAN, 
            user_id=user_id, 
            admin_id=admin_id, 
            chat_id=chat_id
        )

        # Проверяем статус пользователя после разбана
        try:
            member = await moderation_service.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            status_info = f"Статус после разбана: {member.status}"
        except Exception as status_error:
            status_info = f"Не удалось проверить статус: {status_error}"

        await message.answer(
            f"✅ <b>Принудительный разбан выполнен</b>\n\n"
            f"👤 Пользователь: <code>{user_id}</code>\n"
            f"💬 Чат: <code>{chat_id}</code>\n"
            f"📊 {status_info}\n\n"
            f"🔄 Пользователь должен попробовать присоединиться к каналу снова"
        )
        
        logger.info(f"Force unban completed for user {sanitize_for_logging(str(user_id))} in chat {sanitize_for_logging(str(chat_id))}")

    except ValueError as e:
        await message.answer(f"❌ Неверный формат ID чата: {sanitize_for_logging(str(e))}")
    except Exception as e:
        logger.error(f"Error in force_unban command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка при принудительном разбане")


@admin_router.message(Command("suspicious"))
async def handle_suspicious_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Показать подозрительные профили."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем подозрительные профили
        profiles = await profile_service.get_suspicious_profiles(limit=10)
        
        if not profiles:
            await message.answer("✅ Подозрительных профилей не найдено")
            return

        text = "🔍 <b>Подозрительные профили:</b>\n\n"
        
        for i, profile in enumerate(profiles, 1):
            # Получаем информацию о пользователе
            user_info = await profile_service.get_user_info(int(profile.user_id))
            username = f"@{user_info['username']}" if user_info['username'] else "Нет username"
            name = f"{user_info['first_name']} {user_info['last_name'] or ''}".strip()
            
            text += f"{i}. <b>{name}</b>\n"
            text += f"   ID: <code>{profile.user_id}</code>\n"
            text += f"   Username: {username}\n"
            text += f"   Счет подозрительности: {profile.suspicion_score:.2f}\n"
            text += f"   Паттерны: {profile.detected_patterns}\n"
            if profile.linked_chat_title and str(profile.linked_chat_title).strip():
                text += f"   Связанный чат: {profile.linked_chat_title}\n"
            text += f"   Дата: {profile.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

        text += "💡 <b>Команды управления:</b>\n"
        text += "• /suspicious_reset - сбросить все подозрительные профили\n"
        text += "• /suspicious_analyze <user_id> - проанализировать пользователя\n"
        text += "• /suspicious_remove <user_id> - удалить из подозрительных"
        
        await message.answer(text)
        logger.info(f"Suspicious profiles response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in suspicious command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения подозрительных профилей")


@admin_router.message(Command("suspicious_reset"))
async def handle_suspicious_reset_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Сбросить все подозрительные профили."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious reset command from {sanitize_for_logging(str(message.from_user.id))}")

        # Сбрасываем все подозрительные профили
        deleted_count = await profile_service.reset_suspicious_profiles()
        
        await message.answer(
            f"✅ <b>Подозрительные профили сброшены</b>\n\n"
            f"🗑️ Удалено записей: {deleted_count}\n"
            f"📊 Система анализа сброшена"
        )
        logger.info(f"Reset {sanitize_for_logging(str(deleted_count))} suspicious profiles for {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in suspicious_reset command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка сброса подозрительных профилей")


@admin_router.message(Command("suspicious_analyze"))
async def handle_suspicious_analyze_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Проанализировать конкретного пользователя."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious analyze command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if len(args) < 1:
            await message.answer(
                "❌ Использование: /suspicious_analyze <user_id>\n"
                "Пример: /suspicious_analyze 123456789"
            )
            return

        try:
            user_id = int(args[0])
        except ValueError:
            await message.answer("❌ Неверный формат ID пользователя")
            return

        # Получаем информацию о пользователе
        user_info = await profile_service.get_user_info(user_id)
        
        # Создаем объект User для анализа
        from aiogram.types import User
        user = User(
            id=user_info['id'],
            is_bot=user_info['is_bot'],
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            username=user_info['username']
        )
        
        # Анализируем профиль
        profile = await profile_service.analyze_user_profile(user, admin_id)
        
        # Формируем ответ
        text = f"🔍 <b>Анализ профиля пользователя</b>\n\n"
        text += f"<b>Пользователь:</b> {user_info['first_name']} {user_info['last_name'] or ''}\n"
        text += f"<b>ID:</b> <code>{user_id}</code>\n"
        text += f"<b>Username:</b> @{user_info['username'] or 'Нет'}\n"
        
        if profile:
            # Пользователь подозрительный
            text += f"<b>Счет подозрительности:</b> {profile.suspicion_score:.2f}\n"
            
            # Парсим паттерны из строки
            patterns = str(profile.detected_patterns).split(',') if profile.detected_patterns else []
            text += f"<b>Обнаружено паттернов:</b> {len(patterns)}\n\n"
            
            if patterns:
                text += "<b>🔍 Обнаруженные паттерны:</b>\n"
                for pattern in patterns:
                    if pattern.strip():  # Пропускаем пустые строки
                        text += f"• {pattern.strip()}\n"
                text += "\n"
            
            if profile.linked_chat_title and str(profile.linked_chat_title).strip():
                text += f"<b>📱 Связанный чат:</b> {profile.linked_chat_title}\n"
                text += f"<b>📊 Постов:</b> {profile.post_count}\n\n"
            
            # Определяем статус
            if float(profile.suspicion_score) >= 0.7:
                status = "🔴 Высокий риск"
            elif float(profile.suspicion_score) >= 0.4:
                status = "🟡 Средний риск"
            else:
                status = "🟢 Низкий риск"
                
            text += f"<b>Статус:</b> {status}\n"
            text += f"<b>Дата анализа:</b> {profile.created_at.strftime('%d.%m.%Y %H:%M') if profile.created_at else 'Неизвестно'}"
        else:
            # Пользователь не подозрительный
            text += f"<b>Счет подозрительности:</b> 0.00\n"
            text += f"<b>Обнаружено паттернов:</b> 0\n\n"
            text += f"<b>Статус:</b> 🟢 Низкий риск\n"
            text += f"<b>Результат:</b> Пользователь не является подозрительным"
        
        await message.answer(text)
        logger.info(f"Profile analysis completed for user {sanitize_for_logging(str(user_id))}")

    except Exception as e:
        logger.error(f"Error in suspicious_analyze command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка анализа профиля")


@admin_router.message(Command("suspicious_remove"))
async def handle_suspicious_remove_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Удалить пользователя из подозрительных."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious remove command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if len(args) < 1:
            await message.answer(
                "❌ Использование: /suspicious_remove <user_id>\n"
                "Пример: /suspicious_remove 123456789"
            )
            return

        try:
            user_id = int(args[0])
        except ValueError:
            await message.answer("❌ Неверный формат ID пользователя")
            return

        # Удаляем из подозрительных профилей
        profile = await profile_service._get_suspicious_profile(user_id)
        if not profile:
            await message.answer("❌ Пользователь не найден в подозрительных профилях")
            return
            
        await profile_service.db.delete(profile)
        await profile_service.db.commit()
        
        await message.answer(
            f"✅ <b>Пользователь удален из подозрительных</b>\n\n"
            f"👤 ID: <code>{user_id}</code>\n"
            f"🗑️ Запись удалена из базы данных"
        )
        logger.info(f"Removed user {sanitize_for_logging(str(user_id))} from suspicious profiles")

    except Exception as e:
        logger.error(f"Error in suspicious_remove command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка удаления из подозрительных")


@admin_router.message(Command("find_chat"))
async def handle_find_chat_command(
    message: Message,
    moderation_service: ModerationService,
    admin_id: int,
) -> None:
    """Найти ID чата по invite ссылке или username."""
    try:
        if not message.from_user:
            return
        logger.info(f"Find chat command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if len(args) < 1:
            await message.answer(
                "❌ Использование: /find_chat <invite_link_or_username>\n"
                "Примеры:\n"
                "• /find_chat https://t.me/+xlbTj-RSikM0NjA6\n"
                "• /find_chat @channel_username"
            )
            return

        chat_identifier = args[0]
        
        try:
            # Пытаемся получить информацию о чате
            chat = await moderation_service.bot.get_chat(chat_identifier)
            
            # Проверяем, является ли бот администратором
            try:
                bot_member = await moderation_service.bot.get_chat_member(chat.id, moderation_service.bot.id)
                admin_status = "✅ Админ" if bot_member.status in ["administrator", "creator"] else "❌ Не админ"
            except Exception:
                admin_status = "❓ Неизвестно"
            
            await message.answer(
                f"✅ <b>Информация о чате:</b>\n\n"
                f"📝 Название: {chat.title}\n"
                f"🆔 ID: <code>{chat.id}</code>\n"
                f"👤 Username: @{chat.username if chat.username else 'Нет'}\n"
                f"📊 Тип: {chat.type}\n"
                f"👥 Участников: {getattr(chat, 'member_count', 'Неизвестно')}\n"
                f"🤖 Статус бота: {admin_status}\n\n"
                f"💡 Используйте ID для команд: <code>{chat.id}</code>"
            )
            
        except Exception as e:
            await message.answer(
                f"❌ <b>Не удалось найти чат:</b>\n\n"
                f"🔍 Идентификатор: <code>{chat_identifier}</code>\n"
                f"❌ Ошибка: {e}\n\n"
                f"💡 <b>Возможные причины:</b>\n"
                f"• Бот не является администратором канала\n"
                f"• Неправильная invite ссылка\n"
                f"• Канал не существует или удален\n"
                f"• У бота нет доступа к каналу\n\n"
                f"🔧 <b>Попробуйте:</b>\n"
                f"• Добавить бота как администратора в канал\n"
                f"• Использовать username канала: @channel_name\n"
                f"• Проверить правильность invite ссылки"
            )

    except Exception as e:
        logger.error(f"Error in find_chat command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка при поиске чата")


@admin_router.message(Command("my_chats"))
async def handle_my_chats_command(
    message: Message,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Показать все каналы, где бот является администратором."""
    try:
        if not message.from_user:
            return
        logger.info(f"My chats command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем все каналы из базы данных
        channels = await channel_service.get_all_channels()
        
        if not channels:
            await message.answer("❌ Нет каналов в базе данных")
            return

        text = "📢 <b>Каналы в базе данных:</b>\n\n"
        
        for i, channel in enumerate(channels, 1):
            # Проверяем статус бота в канале
            try:
                bot_member = await channel_service.bot.get_chat_member(int(channel.telegram_id), channel_service.bot.id)
                admin_status = "✅ Админ" if bot_member.status in ["administrator", "creator"] else "❌ Не админ"
            except Exception:
                admin_status = "❓ Неизвестно"
            
            text += f"{i}. <b>{channel.title}</b>\n"
            text += f"   ID: <code>{channel.telegram_id}</code>\n"
            text += f"   Username: @{channel.username if channel.username and str(channel.username).strip() else 'Нет'}\n"
            text += f"   Статус бота: {admin_status}\n"
            text += f"   Тип: {'Канал' if not bool(channel.is_comment_group) else 'Группа комментариев'}\n\n"

        text += "💡 <b>Используйте ID канала для команд разбана</b>"
        
        await message.answer(text)
        logger.info(f"My chats response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in my_chats command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка каналов")


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
        logger.info(f"Banned command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем список заблокированных пользователей
        banned_users = await moderation_service.get_banned_users(limit=10)

        if not banned_users:
            await message.answer("📝 Нет заблокированных пользователей")
            return

        text = "🚫 <b>Заблокированные пользователи:</b>\n\n"

        for i, log_entry in enumerate(banned_users, 1):
            user_id = log_entry.user_id
            reason = log_entry.reason or "Спам"
            date_text = log_entry.created_at.strftime("%d.%m.%Y %H:%M") if log_entry.created_at else "Неизвестно"
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
                await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
            )
            chat_display = f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]

            text += f"{i}. <b>{user_display}</b> <code>({user_id})</code>\n"
            text += f"   Причина: {reason}\n"
            text += f"   Чат: <b>{chat_display}</b> <code>({chat_id})</code>\n"
            text += f"   Дата: {date_text}\n\n"

        if len(banned_users) == 10:
            text += "💡 Показаны последние 10 пользователей"

        await message.answer(text)
        logger.info(f"Banned list sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in banned command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка заблокированных")


@admin_router.message(Command("ban_history"))
async def handle_ban_history_command(
    message: Message,
    moderation_service: ModerationService,
    channel_service: ChannelService,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Показать историю банов с chat_id для удобства."""
    try:
        if not message.from_user:
            return
        logger.info(f"Ban history command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем последние 10 записей из истории банов
        ban_history = await moderation_service.get_ban_history(limit=10)

        if not ban_history:
            await message.answer("📝 Нет записей в истории банов")
            return

        # Группируем баны по чатам
        bans_by_chat = {}
        for log_entry in ban_history:
            chat_id = log_entry.chat_id
            if chat_id not in bans_by_chat:
                bans_by_chat[chat_id] = []
            bans_by_chat[chat_id].append(log_entry)

        text = "📋 <b>История банов (по чатам):</b>\n\n"

        entry_number = 1
        for chat_id, chat_bans in bans_by_chat.items():
            # Получаем информацию о чате
            chat_info = (
                await channel_service.get_channel_info(chat_id) if chat_id else {"title": "Unknown Chat", "username": None}
            )
            chat_display = f"@{chat_info['username']}" if chat_info["username"] else chat_info["title"]
            
            text += f"<b>💬 {chat_display}</b> <code>({chat_id})</code>\n"
            
            for log_entry in chat_bans:
                user_id = log_entry.user_id
                reason = log_entry.reason or "Спам"
                date_text = log_entry.created_at.strftime("%d.%m.%Y %H:%M") if log_entry.created_at else "Неизвестно"
                is_active = "🟢 Активен" if log_entry.is_active else "🔴 Неактивен"

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
        logger.info(f"Sync bans command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        if not message.text:
            await message.answer("❌ Ошибка: пустое сообщение")
            return
        args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []

        if not args:
            # Показываем все каналы где бот может работать
            channels = await channel_service.get_all_channels()
            
            if not channels:
                await message.answer("❌ Нет каналов в базе данных")
                return

            # Фильтруем только каналы где бот является администратором
            native_channels = []
            for channel in channels:
                try:
                    bot_member = await channel_service.bot.get_chat_member(int(channel.telegram_id), channel_service.bot.id)
                    if bot_member.status in ["administrator", "creator"]:
                        native_channels.append(channel)
                except Exception:
                    # Если не можем проверить статус, пропускаем
                    continue

            if not native_channels:
                await message.answer("❌ Бот не является администратором ни в одном канале")
                return

            # Получаем историю банов для подсчета активных банов
            ban_history = await moderation_service.get_ban_history(limit=50)
            
            text = "🔄 <b>Выберите чат для синхронизации:</b>\n\n"

            for i, channel in enumerate(native_channels[:5], 1):
                # Считаем активные баны в этом чате
                active_bans = len([log for log in ban_history if log.chat_id == channel.telegram_id and log.is_active])
                
                chat_display = f"@{channel.username}" if channel.username else channel.title

                text += f"{i}. <b>{chat_display}</b>\n"
                text += f"   ID: <code>{channel.telegram_id}</code>\n"
                text += f"   Активных банов: {active_bans}\n\n"

            text += "💡 <b>Использование:</b>\n"
            text += "• <code>/sync_bans 1</code> - синхронизировать по номеру\n"
            text += "• <code>/sync_bans &lt;chat_id&gt;</code> - синхронизировать по ID\n"
            text += "• <code>/ban_history</code> - полная история банов"

            await message.answer(text)
            return

        # Обработка выбора по номеру
        if args[0].isdigit() and 1 <= int(args[0]) <= 5:
            # Получаем все каналы где бот админ
            channels = await channel_service.get_all_channels()
            native_channels = []
            for channel in channels:
                try:
                    bot_member = await channel_service.bot.get_chat_member(int(channel.telegram_id), channel_service.bot.id)
                    if bot_member.status in ["administrator", "creator"]:
                        native_channels.append(channel)
                except Exception:
                    continue
            
            chat_index = int(args[0]) - 1

            if 0 <= chat_index < len(native_channels):
                chat_id = native_channels[chat_index].telegram_id

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

        # Обработка по chat_id или user_id
        if len(args) == 1:
            # Только chat_id - синхронизируем все баны в чате
            try:
                chat_id = int(args[0])
                # Если ID положительный и длинный, добавляем минус для групп/каналов
                if chat_id > 0 and len(str(chat_id)) >= 10:
                    chat_id = -chat_id
            except ValueError:
                await message.answer("❌ Неверный формат ID чата")
                return
            
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
                if telegram_status == "kicked" and not is_banned_db:
                    # Пользователь забанен в Telegram, но не в БД - активируем бан
                    await moderation_service._update_user_status(user_id, is_banned=True)
                    await message.answer(f"✅ Пользователь {user_id} синхронизирован: активирован бан в БД")
                elif telegram_status in ["member", "administrator", "creator"] and is_banned_db:
                    # Пользователь НЕ забанен в Telegram, но забанен в БД - деактивируем бан
                    await moderation_service._update_user_status(user_id, is_banned=False)
                    await moderation_service._deactivate_all_user_bans(user_id)
                    await message.answer(f"✅ Пользователь {user_id} синхронизирован: деактивирован бан в БД")
                else:
                    await message.answer(f"ℹ️ Пользователь {user_id} уже синхронизирован")
                    
            except Exception as e:
                await message.answer(f"❌ Ошибка проверки статуса пользователя: {e}")

        logger.info(f"Sync bans response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except ValueError:
        await message.answer("❌ Неверный формат ID чата")
    except Exception as e:
        logger.error(f"Error in sync_bans command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка синхронизации банов")


# УДАЛЕНО: /sync_user_status - дублирует функциональность /sync_bans


@admin_router.message(Command("help"))
async def handle_help_command(
    message: Message,
    help_service: HelpService,
) -> None:
    """Справка по командам."""
    try:
        if not message.from_user:
            return
        logger.info(f"Help command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        message_text = message.text or ""
        command_args = message_text.split()[1:] if len(message_text.split()) > 1 else []

        if command_args:
            # Если есть аргументы, показываем справку по категории
            category = command_args[0]
            user_id = message.from_user.id if message.from_user else None
            logger.info(f"Getting help for category: {sanitize_for_logging(category)}, user_id: {sanitize_for_logging(str(user_id))}")
            help_text = help_service.get_category_help(category, user_id=user_id)
        else:
            # Если аргументов нет, показываем основную справку
            help_text = help_service.get_main_help(is_admin=True)

        await message.answer(help_text)
        if message.from_user:
            logger.info(f"Help response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in help command: {sanitize_for_logging(str(e))}")
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

        callback_data = callback_query.data or ""
        user_id = int(callback_data.split(":")[1]) if callback_data and ":" in callback_data else 0

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
            try:
                if callback_query.message and hasattr(callback_query.message, "edit_text") and callable(getattr(callback_query.message, "edit_text", None)):
                    await callback_query.message.edit_text(
                        f"🚫 <b>Пользователь забанен</b>\n\n"
                        f"ID: {user_id}\n"
                        f"Имя: {user_info.get('first_name', 'Неизвестно')}\n"
                        f"Причина: Подозрительный профиль"
                    )
            except Exception as e:
                logger.warning(f"Could not edit message: {sanitize_for_logging(str(e))}")
        else:
            await callback_query.answer("❌ Ошибка при бане пользователя")

    except Exception as e:
        logger.error(f"Error in ban_suspicious callback: {sanitize_for_logging(str(e))}")
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

        callback_data = callback_query.data or ""
        user_id = int(callback_data.split(":")[1]) if callback_data and ":" in callback_data else 0

        # Отмечаем профиль как проверенный, но не подтвержденный
        await profile_service.mark_profile_as_reviewed(
            user_id=user_id, admin_id=admin_id, is_confirmed=False, notes="Помечен для наблюдения"
        )

        await callback_query.answer("👀 Пользователь добавлен в список наблюдения")
        try:
            if callback_query.message and hasattr(callback_query.message, "edit_text") and callable(getattr(callback_query.message, "edit_text", None)):
                await callback_query.message.edit_text(
                    f"👀 <b>Пользователь добавлен в наблюдение</b>\n\n" f"ID: {user_id}\n" f"Статус: Наблюдение"
                )
        except Exception as e:
            logger.warning(f"Could not edit message: {sanitize_for_logging(str(e))}")

    except Exception as e:
        logger.error(f"Error in watch_suspicious callback: {sanitize_for_logging(str(e))}")
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

        callback_data = callback_query.data or ""
        user_id = int(callback_data.split(":")[1]) if callback_data and ":" in callback_data else 0

        # Отмечаем профиль как проверенный и ложное срабатывание
        await profile_service.mark_profile_as_reviewed(
            user_id=user_id,
            admin_id=admin_id,
            is_confirmed=False,
            notes="Ложное срабатывание - разрешен",
        )

        await callback_query.answer("✅ Пользователь разрешен")
        try:
            if callback_query.message and hasattr(callback_query.message, "edit_text") and callable(getattr(callback_query.message, "edit_text", None)):
                await callback_query.message.edit_text(
                    f"✅ <b>Пользователь разрешен</b>\n\n" f"ID: {user_id}\n" f"Статус: Ложное срабатывание"
                )
        except Exception as e:
            logger.warning(f"Could not edit message: {sanitize_for_logging(str(e))}")

    except Exception as e:
        logger.error(f"Error in allow_suspicious callback: {sanitize_for_logging(str(e))}")
        await callback_query.answer("❌ Ошибка обработки")


@admin_router.message(Command("instructions"))
async def handle_instructions_command(
    message: Message,
    admin_id: int,
) -> None:
    """Отправить инструкцию по настройке бота для админов каналов."""
    try:
        if not message.from_user:
            return
        logger.info(f"Instructions command from {sanitize_for_logging(str(message.from_user.id))}")

        # Get bot username for instructions
        # bot_username = getattr(message.bot, "username", None) or "your_bot"  # Не используется

        instructions = (
            "📋 <b>ИНСТРУКЦИЯ ПО НАСТРОЙКЕ ПРАВ БОТА</b>\n\n"
            "🤖 <b>Что получают админы каналов при добавлении бота:</b>\n"
            "• Уведомление о готовности бота к работе\n"
            "• Подробную инструкцию по настройке прав\n"
            "• Контакты для связи с владельцем бота\n\n"
            "🔧 <b>ОБЯЗАТЕЛЬНЫЕ ПРАВА для работы бота:</b>\n\n"
            "1️⃣ <b>Удаление сообщений</b>\n"
            "• Настройки канала → Администраторы → @your_bot\n"
            '• Включить "Удалять сообщения"\n'
            "• Без этого бот не сможет удалять спам\n\n"
            "2️⃣ <b>Блокировка пользователей</b>\n"
            '• Включить "Добавлять участников" или "Исключать участников"\n'
            "• Без этого бот не сможет банить спамеров\n\n"
            "3️⃣ <b>Просмотр сообщений</b>\n"
            "• Убедиться, что бот может читать сообщения\n"
            "• Нужно для анализа контента\n\n"
            "✅ <b>ДОПОЛНИТЕЛЬНЫЕ ПРАВА (рекомендуется):</b>\n"
            "• Приглашение пользователей (для разбана)\n"
            "• Закрепление сообщений (для уведомлений)\n\n"
            "⚠️ <b>ВАЖНО для админов каналов:</b>\n"
            "• Без прав на удаление и бан бот работать НЕ БУДЕТ!\n"
            "• Настроить права нужно сразу после добавления\n"
            "• Бот начнет работать автоматически после настройки\n\n"
            "🔍 <b>Проверка работы:</b>\n"
            "• Отправить тестовое сообщение с бот-ссылкой\n"
            "• Бот должен удалить его (если права настроены)\n"
            "• Если не удаляет - проверить права\n\n"
            "⚙️ <b>Управление ботом (только для владельца):</b>\n"
            "• <code>/status</code> - статистика работы бота\n"
            "• <code>/settings</code> - настройки антиспама\n"
            "• <code>/suspicious</code> - просмотр подозрительных профилей\n"
            "• <code>/channels</code> - управление каналами\n"
            "• <code>/setlimits</code> - настройка лимитов\n\n"
            "📞 <b>Поддержка:</b>\n"
            "• Владелец бота: [@ncux-ad](https://github.com/ncux-ad)\n"
            "• GitHub: https://github.com/ncux-ad/Flame_Of_Styx_bot\n"
            "• При проблемах с настройкой - обращайтесь к владельцу\n\n"
            "💡 <b>Совет:</b> Админы каналов должны настроить права, а управление остается за владельцем бота!"
        )

        await message.answer(instructions)
        if message.from_user:
            logger.info(f"Instructions sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in instructions command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения инструкций")


@admin_router.message(Command("logs"))
async def handle_logs_command(
    message: Message,
    admin_id: int,
) -> None:
    """Просмотр логов системы."""
    try:
        if not message.from_user:
            return
        logger.info(f"Logs command from {sanitize_for_logging(str(message.from_user.id))}")

        # Парсим аргументы команды
        message_text = message.text or ""
        command_args = message_text.split()[1:] if len(message_text.split()) > 1 else []
        log_level = command_args[0] if command_args else "all"

        # Получаем логи из journalctl
        import os
        import subprocess

        # Пробуем разные пути к journalctl
        journalctl_paths = ["/usr/bin/journalctl", "/bin/journalctl", "journalctl"]

        journalctl_path = None
        for path in journalctl_paths:
            try:
                # Проверяем, существует ли файл
                if os.path.exists(path) or path == "journalctl":
                    journalctl_path = path
                    break
            except Exception:
                continue

        if not journalctl_path:
            # Если journalctl не найден, попробуем получить логи из файлов
            try:
                log_files = ["/var/log/antispam-bot.log", "logs/antispam-bot.log", "antispam-bot.log"]

                logs_text = ""
                for log_file in log_files:
                    if os.path.exists(log_file):
                        with open(log_file, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            if log_level == "error":
                                logs_text = "\n".join([line for line in lines if "ERROR" in line or "CRITICAL" in line])[
                                    -2000:
                                ]
                            elif log_level == "warning":
                                logs_text = "\n".join(
                                    [line for line in lines if "WARNING" in line or "ERROR" in line or "CRITICAL" in line]
                                )[-2000:]
                            else:
                                logs_text = "\n".join(lines[-50:])
                        break

                if logs_text:
                    if len(logs_text) > 3500:
                        logs_text = logs_text[:3500] + "\n... (логи обрезаны)"
                    response = f"📋 <b>Логи из файла ({log_level})</b>\n\n<code>{logs_text}</code>"
                else:
                    response = "❌ <b>Логи не найдены</b>\n\njournalctl недоступен и файлы логов не найдены"

                await message.answer(response)
                return

            except Exception as e:
                response = f"❌ <b>Ошибка чтения логов</b>\n\n{str(e)}"
                await message.answer(response)
                return

        try:

            if log_level == "error":
                # Только ошибки
                result = subprocess.run(
                    [
                        journalctl_path,
                        "-u",
                        "antispam-bot.service",
                        "--since",
                        "1 hour ago",
                        "--priority",
                        "err",
                        "--no-pager",
                        "-n",
                        "50",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                )
            elif log_level == "warning":
                # Предупреждения и ошибки - используем grep для фильтрации
                result = subprocess.run(
                    [journalctl_path, "-u", "antispam-bot.service", "--since", "1 hour ago", "--no-pager", "-n", "100"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                )
                if result.returncode == 0 and result.stdout:
                    # Фильтруем только WARNING и ERROR уровни
                    import re

                    warning_lines = []
                    for line in result.stdout.split("\n"):
                        if re.search(r"(WARNING|ERROR|CRITICAL)", line, re.IGNORECASE):
                            warning_lines.append(line)
                    result.stdout = "\n".join(warning_lines[-50:])  # Последние 50 строк
            else:
                # Все логи
                result = subprocess.run(
                    [journalctl_path, "-u", "antispam-bot.service", "--since", "1 hour ago", "--no-pager", "-n", "30"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                )

            if result.returncode == 0:
                logs_text = result.stdout.strip() if result.stdout else ""

                if logs_text:
                    # Ограничиваем размер сообщения (Telegram лимит 4096 символов)
                    if len(logs_text) > 3500:
                        logs_text = logs_text[:3500] + "\n... (логи обрезаны)"

                    response = f"📋 <b>Логи системы ({log_level})</b>\n\n<code>{logs_text}</code>"
                else:
                    # Нет логов указанного уровня
                    if log_level == "error":
                        response = "✅ <b>Ошибок не найдено</b>\n\nЗа последний час ошибок в логах не обнаружено."
                    elif log_level == "warning":
                        response = (
                            "✅ <b>Предупреждений не найдено</b>\n\nЗа последний час предупреждений в логах не обнаружено."
                        )
                    else:
                        response = "📋 <b>Логи системы (all)</b>\n\n<code>-- No entries --</code>"

            else:
                error_msg = result.stderr or "Неизвестная ошибка"
                response = f"❌ <b>Ошибка получения логов</b>\n\nКод возврата: {result.returncode}\nОшибка: {error_msg}\n\nПроверьте, что бот запущен как systemd сервис на Ubuntu сервере."

        except subprocess.TimeoutExpired:
            response = "⏰ <b>Таймаут получения логов</b>\n\nЛоги слишком большие, попробуйте позже"
        except Exception as e:
            response = f"❌ <b>Ошибка выполнения команды</b>\n\n{str(e)}"

        await message.answer(response)
        if message.from_user:
            logger.info(f"Logs response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in logs command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения логов")
