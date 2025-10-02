"""
Админские хендлеры - модульная структура
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.keyboards.inline import get_spam_analysis_keyboard
from app.models.moderation_log import ModerationAction
from app.services.admin import AdminService
from app.services.bots import BotService
from app.services.bots_admin import BotsAdminService
from app.services.callbacks import CallbacksService
from app.services.channels import ChannelService
from app.services.channels_admin import ChannelsAdminService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.services.status import StatusService
from app.services.suspicious_admin import SuspiciousAdminService
from app.utils.error_handling import ValidationError, handle_errors
from app.utils.security import safe_format_message, sanitize_for_logging

# Импортируем все хендлеры
from .basic import basic_router
from .bots import bots_router
from .channels import channels_router
from .interactive import interactive_router
from .limits import limits_router
from .moderation import moderation_router

# from .spam_analysis import router as spam_analysis_router  # Перенесено в основной роутер
from .rate_limit import rate_limit_router
from .suspicious import suspicious_router

logger = logging.getLogger(__name__)

# Создаем основной роутер
admin_router = Router()

# Подключаем все подроутеры
admin_router.include_router(basic_router)
admin_router.include_router(channels_router)
admin_router.include_router(limits_router)
admin_router.include_router(moderation_router)
admin_router.include_router(suspicious_router)
admin_router.include_router(interactive_router)
# admin_router.include_router(spam_analysis_router)  # Перенесено в основной роутер из-за проблем Aiogram 3.x
admin_router.include_router(rate_limit_router)
admin_router.include_router(bots_router)

logger.info(f"Admin router configured with {len(admin_router.sub_routers)} sub-routers")
logger.info(f"Sub-routers: {[router.name for router in admin_router.sub_routers]}")

# Фильтр админа применяется к конкретным хендлерам, а не глобально
# admin_router.message.filter(IsAdminOrSilentFilter())
# admin_router.callback_query.filter(IsAdminOrSilentFilter())

logger.info("Admin filter will be applied to individual handlers")


# Простой тестовый хендлер с фильтром админа
@admin_router.message(Command("test_admin"), IsAdminOrSilentFilter())
async def test_admin_handler(message: Message) -> None:
    """Простой тестовый хендлер для проверки работы admin router."""
    logger.info("TEST ADMIN HANDLER CALLED!")
    await message.answer("✅ Admin router работает!")


# Тестовый хендлер для bots (перенесен из bots_router)
@admin_router.message(Command("test_bots"))
async def test_bots_handler(message: Message) -> None:
    """Тестовый хендлер для проверки работы bots функциональности."""
    logger.info("TEST BOTS HANDLER CALLED!")
    await message.answer("✅ Bots функциональность работает!")


from app.middlewares.silent_logging import send_silent_response

# Импортируем необходимые сервисы для bots команд
from app.services.bots_admin import BotsAdminService
from app.services.channels import ChannelService
from app.services.channels_admin import ChannelsAdminService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging


# Команда /bots (перенесена из bots_router)
@admin_router.message(Command("bots"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /bots")
async def handle_bots_command(
    message: Message,
    bots_admin_service: BotsAdminService,
    admin_id: int,
) -> None:
    """Показать список ботов и управление whitelist."""
    try:
        logger.info(f"BOTS COMMAND HANDLER CALLED: {message.text}")
        if not message.from_user:
            logger.warning("Bots command: no from_user")
            return

        logger.info(f"Bots command from {sanitize_for_logging(str(message.from_user.id))}")
        logger.info(f"Bots admin service: {bots_admin_service}")
        logger.info(f"Admin ID: {admin_id}")

        bots_text = await bots_admin_service.get_bots_list()
        logger.info(f"Bots text length: {len(bots_text)}")

        await send_silent_response(message, bots_text)
        logger.info(f"Bots list sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in bots command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения списка ботов")


# Команда /channels (перенесена из channels_router)
@admin_router.message(Command("channels"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /channels")
async def handle_channels_command(
    message: Message,
    channel_service: ChannelService,
    channels_admin_service: ChannelsAdminService,
    admin_id: int,
) -> None:
    """Показать список каналов."""
    try:
        if not message.from_user:
            return
        logger.info(f"Channels command from {sanitize_for_logging(str(message.from_user.id))}")

        channels_text = await channels_admin_service.get_channels_display()
        await message.answer(channels_text)
        logger.info(f"Channels list sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in channels command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения списка каналов")


# Команда /sync_channels (перенесена из channels_router)
@admin_router.message(Command("sync_channels"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /sync_channels")
async def handle_sync_channels_command(
    message: Message,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Синхронизация статуса каналов."""
    try:
        if not message.from_user:
            return
        logger.info(f"Sync channels command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем список каналов
        channels = await channel_service.get_all_channels()

        if not channels:
            await message.answer("📋 Каналы не найдены")
            return

        # Синхронизируем статус каждого канала
        synced_count = 0
        for channel in channels:
            try:
                await channel_service.sync_channel_status(channel.chat_id, admin_id)
                synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing channel {channel.chat_id}: {e}")
                continue

        await message.answer(f"✅ Синхронизировано {synced_count} каналов из {len(channels)}")
        logger.info(f"Sync channels completed: {synced_count}/{len(channels)}")

    except Exception as e:
        logger.error(f"Error in sync_channels command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка синхронизации каналов")


# Команда /find_chat (перенесена из channels_router)
@admin_router.message(Command("find_chat"), IsAdminOrSilentFilter())
@handle_errors(user_message="❌ Ошибка выполнения команды /find_chat")
async def handle_find_chat_command(
    message: Message,
    channel_service: ChannelService,
    admin_id: int,
) -> None:
    """Найти чат по ID или username."""
    try:
        if not message.from_user:
            return

        # Получаем аргументы команды
        args = message.text.split()[1:] if message.text else []
        if not args:
            await message.answer("❌ <b>Использование:</b> /find_chat <chat_id> или /find_chat @username")
            return

        chat_identifier = args[0]
        logger.info(f"Find chat command from {sanitize_for_logging(str(message.from_user.id))}: {chat_identifier}")

        # Ищем чат по ID или username
        chat_info = await channel_service.find_chat_by_identifier(chat_identifier)

        if chat_info:
            response = f"📋 <b>Найден чат:</b>\n"
            response += f"• ID: <code>{chat_info.get('id', 'N/A')}</code>\n"
            response += f"• Название: {chat_info.get('title', 'N/A')}\n"
            response += f"• Username: @{chat_info.get('username', 'N/A')}\n"
            response += f"• Тип: {chat_info.get('type', 'N/A')}\n"
            response += f"• Статус: {'✅ Антиспам активен' if chat_info.get('is_active', False) else '❌ Антиспам неактивен'}"

            await message.answer(response)
            logger.info(f"Chat found: {chat_info.get('id')}")
        else:
            await message.answer(f"❌ Чат не найден: {chat_identifier}")
            logger.info(f"Chat not found: {chat_identifier}")

    except Exception as e:
        logger.error(f"Error in find_chat command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка поиска чата")


# Команда spam_analysis перенесена из подроутера (проблема Aiogram 3.x с подроутерами)
@admin_router.message(Command("spam_analysis"), IsAdminOrSilentFilter())
async def handle_spam_analysis_command(message: Message) -> None:
    """Показать меню анализа спама."""
    logger.info("SPAM_ANALYSIS HANDLER CALLED!")
    try:
        user_id = message.from_user.id if message.from_user else 0
        logger.info(f"Spam analysis menu requested by user {user_id}")

        keyboard = get_spam_analysis_keyboard()

        await message.answer(
            "🔍 <b>Анализ данных спама</b>\n\n" "Выберите действие для анализа собранных данных:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        logger.info(f"Spam analysis menu sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error in spam_analysis_menu: {e}")
        await message.answer("❌ Ошибка при загрузке меню анализа спама")


# Callback handlers для spam_analysis (перенесены из подроутера)
@admin_router.callback_query(F.data == "spam_stats")
async def show_spam_stats(callback: CallbackQuery):
    """Показать статистику спама."""
    logger.info("SPAM_STATS CALLBACK CALLED!")

    # Проверяем, что пользователь админ
    if not callback.from_user or callback.from_user.id != 439304619:
        logger.warning(f"Non-admin user {callback.from_user.id if callback.from_user else 'None'} tried to use spam_stats")
        return

    try:
        from app.utils.pii_protection import secure_logger

        # Получаем данные за последние 30 дней
        spam_data = secure_logger.get_spam_analysis_data(days=30)

        if not spam_data:
            if callback.message:
                await callback.message.edit_text(
                    "📊 <b>Статистика спама</b>\n\n"
                    "❌ Данные за последние 30 дней не найдены.\n"
                    "Убедитесь, что включено полное логирование.",
                    parse_mode="HTML",
                )
            return

        # Простая статистика
        total_entries = len(spam_data)
        stats_text = (
            f"📊 <b>Статистика спама</b>\n\n" f"📅 Период: последние 30 дней\n" f"📊 Всего записей: {total_entries}\n\n"
        )

        if callback.message:
            await callback.message.edit_text(stats_text, reply_markup=get_spam_analysis_keyboard(), parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка получения статистики спама: {e}")
        if callback.message:
            await callback.message.edit_text(
                "❌ <b>Ошибка получения статистики</b>\n\n" f"Произошла ошибка: {str(e)}",
                reply_markup=get_spam_analysis_keyboard(),
                parse_mode="HTML",
            )


@admin_router.callback_query(F.data == "spam_back")
async def spam_back_to_menu(callback: CallbackQuery):
    """Вернуться к главному меню анализа спама."""
    logger.info("SPAM_BACK CALLBACK CALLED!")
    try:
        keyboard = get_spam_analysis_keyboard()

        if callback.message:
            await callback.message.edit_text(
                "🔍 <b>Анализ данных спама</b>\n\n" "Выберите действие для анализа собранных данных:",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error(f"Error in spam_back_to_menu: {e}")


# Временные заглушки для остальных кнопок
@admin_router.callback_query(F.data == "spam_patterns")
async def spam_patterns_stub(callback: CallbackQuery):
    """Заглушка для паттернов спама."""
    logger.info("SPAM_PATTERNS CALLBACK CALLED!")
    if callback.message:
        await callback.message.edit_text(
            "🔍 <b>Паттерны спама</b>\n\n" "Функция в разработке...",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="HTML",
        )


@admin_router.callback_query(F.data == "spam_export")
async def spam_export_stub(callback: CallbackQuery):
    """Заглушка для экспорта спама."""
    logger.info("SPAM_EXPORT CALLBACK CALLED!")
    if callback.message:
        await callback.message.edit_text(
            "📤 <b>Экспорт данных спама</b>\n\n" "Функция в разработке...",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="HTML",
        )


@admin_router.callback_query(F.data == "spam_cleanup")
async def spam_cleanup_stub(callback: CallbackQuery):
    """Заглушка для очистки спама."""
    logger.info("SPAM_CLEANUP CALLBACK CALLED!")
    if callback.message:
        await callback.message.edit_text(
            "🧹 <b>Очистка данных спама</b>\n\n" "Функция в разработке...",
            reply_markup=get_spam_analysis_keyboard(),
            parse_mode="HTML",
        )
