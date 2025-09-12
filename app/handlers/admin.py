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
    """Статистика бота."""
    try:
        logger.info(f"Status command from {message.from_user.id}")

        # Получаем статистику
        total_bots = await bot_service.get_total_bots_count()
        total_channels = await channel_service.get_total_channels_count()

        status_text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"🤖 Всего ботов: {total_bots}\n"
            f"📢 Всего каналов: {total_channels}\n"
            f"👑 Админ ID: {admin_id}\n"
            f"✅ Статус: Работает"
        )

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
    admin_id: int,
) -> None:
    """Разблокировать пользователя."""
    try:
        logger.info(f"Unban command from {message.from_user.id}")

        # Парсим аргументы команды
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []

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
