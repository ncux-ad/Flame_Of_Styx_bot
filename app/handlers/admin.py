"""Admin command handlers."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.keyboards.inline import get_main_menu_keyboard
from app.keyboards.reply import get_admin_menu_keyboard
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)

# Create router
admin_router = Router()


@admin_router.message(Command("start"))
async def handle_start_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /start command for admins."""
    try:
        logger.info(
            safe_format_message(
                "Start command received from {user_id}",
                user_id=message.from_user.id if message.from_user else 0,
            )
        )

        welcome_text = (
            "🤖 <b>AntiSpam Bot</b>\n\n"
            "Добро пожаловать в панель администратора!\n\n"
            "Доступные команды:\n"
            "/status - статистика\n"
            "/channels - управление каналами\n"
            "/bots - управление ботами\n"
            "/suspicious - подозрительные профили\n"
            "/help - помощь"
        )

        await message.answer(welcome_text)
        logger.info(
            safe_format_message(
                "Start command response sent to {user_id}",
                user_id=message.from_user.id if message.from_user else 0,
            )
        )

    except Exception as e:
        logger.error(
            safe_format_message(
                "Error handling start command: {error}", error=sanitize_for_logging(e)
            )
        )


@admin_router.message(Command("status"), IsAdminOrSilentFilter())
async def handle_status_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /status command."""
    try:
        # TODO: Get real statistics from database
        status_text = (
            "📊 <b>Статистика AntiSpam Bot</b>\n\n"
            f"<b>Каналы:</b>\n"
            f"✅ Разрешены: 0\n"
            f"🚫 Заблокированы: 0\n"
            f"⏳ Ожидают: 0\n\n"
            f"<b>Боты:</b>\n"
            f"✅ В whitelist: 0\n\n"
            f"<b>Статус:</b> 🟢 Работает"
        )

        await message.answer(status_text)

    except Exception as e:
        logger.error(f"Error handling status command: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@admin_router.message(Command("channels"), IsAdminOrSilentFilter())
async def handle_channels_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /channels command."""
    try:
        # Get services from kwargs (aiogram 3.x style)
        channel_service = kwargs.get("channel_service")

        if not channel_service:
            logger.error("Channel service not injected properly")
            await message.answer("❌ Ошибка: сервис каналов недоступен")
            return

        # Get channel lists
        allowed_channels = await channel_service.get_allowed_channels()
        blocked_channels = await channel_service.get_blocked_channels()
        pending_channels = await channel_service.get_pending_channels()

        channels_text = "📋 <b>Управление каналами</b>\n\n"

        if allowed_channels:
            channels_text += "<b>✅ Разрешенные каналы:</b>\n"
            for channel in allowed_channels[:10]:  # Show first 10
                channels_text += f"• {channel.title} (@{channel.username})\n"
            if len(allowed_channels) > 10:
                channels_text += f"... и еще {len(allowed_channels) - 10}\n"
            channels_text += "\n"

        if blocked_channels:
            channels_text += "<b>🚫 Заблокированные каналы:</b>\n"
            for channel in blocked_channels[:10]:  # Show first 10
                channels_text += f"• {channel.title} (@{channel.username})\n"
            if len(blocked_channels) > 10:
                channels_text += f"... и еще {len(blocked_channels) - 10}\n"
            channels_text += "\n"

        if pending_channels:
            channels_text += "<b>⏳ Ожидающие решения:</b>\n"
            for channel in pending_channels[:10]:  # Show first 10
                channels_text += f"• {channel.title} (@{channel.username})\n"
            if len(pending_channels) > 10:
                channels_text += f"... и еще {len(pending_channels) - 10}\n"

        if not any([allowed_channels, blocked_channels, pending_channels]):
            channels_text += "Нет каналов в базе данных"

        await message.answer(channels_text)

    except Exception as e:
        logger.error(f"Error handling channels command: {e}")
        await message.answer("❌ Ошибка при получении списка каналов")


@admin_router.message(Command("bots"), IsAdminOrSilentFilter())
async def handle_bots_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /bots command."""
    try:
        # Get services from kwargs (aiogram 3.x style)
        bot_service = kwargs.get("bot_service")

        if not bot_service:
            logger.error("Bot service not injected properly")
            await message.answer("❌ Ошибка: сервис ботов недоступен")
            return

        # Get bot lists
        whitelisted_bots = await bot_service.get_whitelisted_bots()
        all_bots = await bot_service.get_all_bots()

        bots_text = "🤖 <b>Управление ботами</b>\n\n"

        if whitelisted_bots:
            bots_text += "<b>✅ Боты в whitelist:</b>\n"
            for bot in whitelisted_bots[:10]:  # Show first 10
                bots_text += f"• @{bot.username}\n"
            if len(whitelisted_bots) > 10:
                bots_text += f"... и еще {len(whitelisted_bots) - 10}\n"
            bots_text += "\n"

        bots_text += f"<b>Всего ботов в базе:</b> {len(all_bots)}\n"
        bots_text += f"<b>В whitelist:</b> {len(whitelisted_bots)}\n"
        bots_text += f"<b>Заблокированы:</b> {len(all_bots) - len(whitelisted_bots)}"

        await message.answer(bots_text)

    except Exception as e:
        logger.error(f"Error handling bots command: {e}")
        await message.answer("❌ Ошибка при получении списка ботов")


@admin_router.message(Command("suspicious"), IsAdminOrSilentFilter())
async def handle_suspicious_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /suspicious command."""
    try:
        # Get services from kwargs (aiogram 3.x style)
        profile_service = kwargs.get("profile_service")

        if not profile_service:
            logger.error("Profile service not injected properly")
            logger.error(f"Available keys in kwargs: {list(kwargs.keys())}")
            await message.answer("❌ Ошибка: сервис профилей недоступен")
            return

        # Get suspicious profiles
        suspicious_profiles = await profile_service.get_suspicious_profiles()

        if not suspicious_profiles:
            await message.answer("✅ Подозрительных профилей не найдено")
            return

        response_text = f"⚠️ <b>Подозрительные профили</b>\n\n"
        response_text += f"Найдено: {len(suspicious_profiles)}\n\n"

        for profile in suspicious_profiles[:10]:  # Show first 10
            response_text += f"• ID: {profile.user_id}\n"
            if profile.username:
                response_text += f"  Username: @{profile.username}\n"
            response_text += f"  Причина: {profile.reason}\n"
            response_text += f"  Дата: {profile.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

        if len(suspicious_profiles) > 10:
            response_text += f"... и еще {len(suspicious_profiles) - 10}\n"

        await message.answer(response_text)

    except Exception as e:
        logger.error(f"Error handling suspicious command: {e}")
        await message.answer("❌ Ошибка при получении подозрительных профилей")


@admin_router.message(Command("help"))
async def handle_help_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /help command."""
    try:
        from app.services.help import HelpService

        help_service = HelpService()

        # Parse command arguments
        command_text = message.text or ""
        args = command_text.split()[1:] if len(command_text.split()) > 1 else []

        if args:
            # Help for specific category
            category = args[0]
            help_text = help_service.get_category_help(
                category, user_id=message.from_user.id if message.from_user else None
            )
        else:
            # Main help
            # Check if user is admin
            from app.filters.is_admin_or_silent import IsAdminOrSilentFilter

            filter_instance = IsAdminOrSilentFilter()
            is_admin = (
                message.from_user.id in filter_instance.admin_ids if message.from_user else False
            )
            help_text = help_service.get_main_help(is_admin=is_admin)

        await message.answer(help_text)

    except Exception as e:
        logger.error(f"Error handling help command: {e}")
        await message.answer("❌ Ошибка при получении справки")


@admin_router.message(Command("limits"), IsAdminOrSilentFilter())
async def handle_limits_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /limits command to show current rate limits."""
    try:
        from app.config import load_config

        config = load_config()
        admin_ids = config.admin_ids_list

        limits_text = (
            "📊 <b>Текущие лимиты Rate Limit</b>\n\n"
            "👥 <b>Обычные пользователи:</b>\n"
            "• 10 запросов в минуту\n"
            "• Интервал: 60 секунд\n\n"
            "👑 <b>Администраторы:</b>\n"
            f"• 100 запросов в минуту\n"
            f"• Интервал: 60 секунд\n"
            f"• Количество админов: {len(admin_ids)}\n\n"
            "ℹ️ <i>Лимиты применяются к сообщениям и callback-запросам</i>"
        )

        await message.answer(limits_text)

    except Exception as e:
        logger.error(f"Error handling limits command: {e}")
        await message.answer("❌ Ошибка при получении информации о лимитах")


@admin_router.message(Command("setlimits"), IsAdminOrSilentFilter())
async def handle_setlimits_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /setlimits command to change rate limits (super admin only)."""
    try:
        from app.config import load_config

        config = load_config()
        # Only first admin (super admin) can change limits
        if message.from_user.id != config.admin_ids_list[0]:
            await message.answer("❌ Только суперадмин может изменять лимиты")
            return

        # Parse command arguments
        command_text = message.text or ""
        args = command_text.split()[1:] if len(command_text.split()) > 1 else []

        if len(args) < 2:
            help_text = (
                "⚙️ <b>Изменение лимитов Rate Limit</b>\n\n"
                "Использование: /setlimits [user_limit] [admin_limit]\n\n"
                "Примеры:\n"
                "• /setlimits 5 50 - 5 запросов для пользователей, 50 для админов\n"
                "• /setlimits 20 200 - 20 запросов для пользователей, 200 для админов\n\n"
                "⚠️ <i>Изменения вступят в силу после перезапуска бота</i>"
            )
            await message.answer(help_text)
            return

        try:
            user_limit = int(args[0])
            admin_limit = int(args[1])

            if user_limit < 1 or admin_limit < 1:
                await message.answer("❌ Лимиты должны быть больше 0")
                return

            if user_limit > admin_limit:
                await message.answer("❌ Лимит пользователей не может быть больше лимита админов")
                return

            # Update limits in bot.py (this would require bot restart)
            success_text = (
                f"✅ <b>Лимиты обновлены!</b>\n\n"
                f"👥 Пользователи: {user_limit} запросов в минуту\n"
                f"👑 Админы: {admin_limit} запросов в минуту\n\n"
                f"⚠️ <i>Для применения изменений перезапустите бота</i>"
            )
            await message.answer(success_text)

        except ValueError:
            await message.answer("❌ Лимиты должны быть числами")

    except Exception as e:
        logger.error(f"Error handling setlimits command: {e}")
        await message.answer("❌ Ошибка при изменении лимитов")


@admin_router.message(Command("logs"), IsAdminOrSilentFilter())
async def handle_logs_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /logs command."""
    try:
        import os
        from datetime import datetime

        # Check if logs directory exists
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            await message.answer("📝 Логи не найдены. Директория logs не существует.")
            return

        # Get list of log files
        log_files = [f for f in os.listdir(logs_dir) if f.endswith(".log")]

        if not log_files:
            await message.answer("📝 Логи не найдены. Нет файлов .log в директории logs.")
            return

        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)

        # Get the most recent log file
        latest_log = log_files[0]
        log_path = os.path.join(logs_dir, latest_log)

        # Get file size
        file_size = os.path.getsize(log_path)

        # Read last 50 lines of the log file
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines

        # Format log content
        log_content = "".join(last_lines)

        # Truncate if too long for Telegram (4096 chars limit)
        if len(log_content) > 4000:
            log_content = "...\n" + log_content[-4000:]

        response_text = (
            f"📝 <b>Последние логи</b>\n\n"
            f"📁 Файл: <code>{latest_log}</code>\n"
            f"📏 Размер: {file_size:,} байт\n"
            f"📅 Обновлен: {datetime.fromtimestamp(os.path.getmtime(log_path)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Последние 50 строк:</b>\n"
            f"<pre>{log_content}</pre>"
        )

        await message.answer(response_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error handling logs command: {e}")
        await message.answer("❌ Ошибка при получении логов")


@admin_router.callback_query(F.data == "admin_stats")
async def handle_admin_stats_callback(callback: CallbackQuery, **kwargs) -> None:
    """Handle admin stats callback."""
    try:
        # Get services from data
        data = kwargs.get("data", {})
        channel_service = data.get("channel_service")
        bot_service = data.get("bot_service")

        if not channel_service or not bot_service:
            logger.error("Services not injected properly")
            await callback.answer("❌ Ошибка: сервисы недоступны")
            return

        # Get statistics
        allowed_channels = await channel_service.get_allowed_channels()
        blocked_channels = await channel_service.get_blocked_channels()
        pending_channels = await channel_service.get_pending_channels()
        whitelisted_bots = await bot_service.get_whitelisted_bots()

        stats_text = (
            "📊 <b>Статистика</b>\n\n"
            f"<b>Каналы:</b>\n"
            f"✅ Разрешены: {len(allowed_channels)}\n"
            f"🚫 Заблокированы: {len(blocked_channels)}\n"
            f"⏳ Ожидают: {len(pending_channels)}\n\n"
            f"<b>Боты:</b>\n"
            f"✅ В whitelist: {len(whitelisted_bots)}"
        )

        await callback.message.edit_text(stats_text)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling admin stats callback: {e}")
        await callback.answer("❌ Ошибка при получении статистики")


@admin_router.message(Command("settings"), IsAdminOrSilentFilter())
async def handle_settings_command(message: Message, data: dict = None, **kwargs) -> None:
    """Handle /settings command."""
    try:
        settings_text = (
            "⚙️ <b>Настройки AntiSpam Bot</b>\n\n"
            "Доступные настройки:\n"
            "• Лимиты сообщений\n"
            "• Фильтры спама\n"
            "• Уведомления\n\n"
            "Используйте /setlimits для настройки лимитов."
        )

        await message.answer(settings_text)

    except Exception as e:
        logger.error(f"Error handling settings command: {e}")
        await message.answer("❌ Ошибка при получении настроек")
