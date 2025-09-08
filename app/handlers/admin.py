"""Admin command handlers."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.services.channels import ChannelService
from app.services.bots import BotService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.keyboards.inline import get_main_menu_keyboard
from app.keyboards.reply import get_admin_menu_keyboard
from app.filters.is_admin import IsAdminFilter

logger = logging.getLogger(__name__)

# Create router
admin_router = Router()

# Apply admin filter to all handlers
admin_router.message.filter(IsAdminFilter())
admin_router.callback_query.filter(IsAdminFilter())


@admin_router.message(Command("start"))
async def handle_start_command(message: Message) -> None:
    """Handle /start command for admins."""
    try:
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
        
        await message.answer(
            welcome_text,
            reply_markup=get_admin_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error handling start command: {e}")


@admin_router.message(Command("status"))
async def handle_status_command(message: Message) -> None:
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


@admin_router.message(Command("channels"))
async def handle_channels_command(
    message: Message,
    channel_service: ChannelService
) -> None:
    """Handle /channels command."""
    try:
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


@admin_router.message(Command("bots"))
async def handle_bots_command(
    message: Message,
    bot_service: BotService
) -> None:
    """Handle /bots command."""
    try:
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


@admin_router.message(Command("suspicious"))
async def handle_suspicious_command(
    message: Message,
    profile_service: ProfileService
) -> None:
    """Handle /suspicious command."""
    try:
        # This would need to be implemented in ProfileService
        suspicious_text = (
            "⚠️ <b>Подозрительные профили</b>\n\n"
            "Функция в разработке..."
        )
        
        await message.answer(suspicious_text)
        
    except Exception as e:
        logger.error(f"Error handling suspicious command: {e}")
        await message.answer("❌ Ошибка при получении подозрительных профилей")


@admin_router.message(Command("help"))
async def handle_help_command(message: Message) -> None:
    """Handle /help command."""
    try:
        help_text = (
            "❓ <b>Справка по командам</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - главное меню\n"
            "/status - статистика бота\n"
            "/channels - управление каналами\n"
            "/bots - управление ботами\n"
            "/suspicious - подозрительные профили\n"
            "/help - эта справка\n\n"
            "<b>Управление каналами:</b>\n"
            "При получении сообщения от канала вы получите уведомление с кнопками:\n"
            "✅ Разрешить - добавить канал в whitelist\n"
            "🚫 Заблокировать - добавить канал в blacklist\n"
            "🗑 Удалить сообщение - удалить сообщение\n\n"
            "<b>Управление ботами:</b>\n"
            "Боты автоматически банится, если не находятся в whitelist\n"
            "Используйте команды для управления whitelist"
        )
        
        await message.answer(help_text)
        
    except Exception as e:
        logger.error(f"Error handling help command: {e}")


@admin_router.callback_query(F.data == "admin_stats")
async def handle_admin_stats_callback(
    callback: CallbackQuery,
    channel_service: ChannelService,
    bot_service: BotService
) -> None:
    """Handle admin stats callback."""
    try:
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
