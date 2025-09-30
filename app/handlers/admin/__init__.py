"""
Админские хендлеры - модульная структура
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

# Применяем фильтр админа ко всем хендлерам
admin_router.message.filter(IsAdminOrSilentFilter())
admin_router.callback_query.filter(IsAdminOrSilentFilter())
