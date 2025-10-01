"""
Админские хендлеры - модульная структура
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.filters.is_admin_or_silent import IsAdminOrSilentFilter
from app.utils.security import sanitize_for_logging
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.moderation import ModerationService
from app.models.moderation_log import ModerationAction
from app.services.profiles import ProfileService
from app.services.admin import AdminService
from app.services.status import StatusService
from app.services.channels_admin import ChannelsAdminService
from app.services.bots_admin import BotsAdminService
from app.services.suspicious_admin import SuspiciousAdminService
from app.services.callbacks import CallbacksService
from app.utils.error_handling import ValidationError, handle_errors
from app.utils.security import sanitize_for_logging, safe_format_message

# Импортируем все хендлеры
from .basic import basic_router
from .channels import channels_router
from .limits import limits_router
from .moderation import moderation_router
from .suspicious import suspicious_router
from .interactive import interactive_router
from .spam_analysis import router as spam_analysis_router
from .rate_limit import rate_limit_router
from .bots import bots_router

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
admin_router.include_router(spam_analysis_router)
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

# Импортируем необходимые сервисы для bots команд
from app.services.bots_admin import BotsAdminService
from app.utils.error_handling import handle_errors
from app.middlewares.silent_logging import send_silent_response
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
