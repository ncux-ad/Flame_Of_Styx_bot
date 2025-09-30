"""
Dependency Injection Container using punq
"""

import logging
from typing import Any, Dict, Type, TypeVar

import punq
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import SessionLocal
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.services.admin import AdminService
from app.services.status import StatusService
from app.services.channels_admin import ChannelsAdminService
from app.services.bots_admin import BotsAdminService
from app.services.suspicious_admin import SuspiciousAdminService
from app.services.callbacks import CallbacksService
from app.services.redis_rate_limiter import get_redis_rate_limiter

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """Dependency Injection Container using punq."""
    
    def __init__(self):
        self.container = punq.Container()
        self._setup_container()
    
    def _setup_container(self) -> None:
        """Настройка контейнера зависимостей."""
        
        # Регистрируем конфигурацию
        from app.config import load_config
        config = load_config()
        self.container.register(Settings, instance=config)
        
        # Регистрируем фабрики для создания сессий БД
        self.container.register(AsyncSession, factory=self._create_db_session)
        
        # Регистрируем основные сервисы
        self.container.register(ModerationService, factory=self._create_moderation_service)
        self.container.register(LinkService, factory=self._create_link_service)
        self.container.register(ProfileService, factory=self._create_profile_service)
        self.container.register(ChannelService, factory=self._create_channel_service)
        self.container.register(BotService, factory=self._create_bot_service)
        self.container.register(HelpService, factory=self._create_help_service)
        self.container.register(LimitsService, factory=self._create_limits_service)
        
        # Регистрируем админские сервисы с зависимостями
        self.container.register(AdminService, factory=self._create_admin_service)
        self.container.register(StatusService, factory=self._create_status_service)
        self.container.register(ChannelsAdminService, factory=self._create_channels_admin_service)
        self.container.register(BotsAdminService, factory=self._create_bots_admin_service)
        self.container.register(SuspiciousAdminService, factory=self._create_suspicious_admin_service)
        self.container.register(CallbacksService, factory=self._create_callbacks_service)
        
        logger.info("DI Container setup completed")
    
    def _create_db_session(self) -> AsyncSession:
        """Создать сессию БД."""
        return SessionLocal()
    
    def _create_moderation_service(self, bot: Bot, db_session: AsyncSession) -> ModerationService:
        """Создать ModerationService."""
        return ModerationService(bot, db_session)
    
    def _create_link_service(self, bot: Bot, db_session: AsyncSession) -> LinkService:
        """Создать LinkService."""
        return LinkService(bot, db_session)
    
    def _create_profile_service(self, bot: Bot, db_session: AsyncSession) -> ProfileService:
        """Создать ProfileService."""
        return ProfileService(bot, db_session)
    
    def _create_channel_service(self, bot: Bot, db_session: AsyncSession, config: Settings) -> ChannelService:
        """Создать ChannelService."""
        return ChannelService(bot, db_session, config.native_channel_ids_list)
    
    def _create_bot_service(self, bot: Bot, db_session: AsyncSession) -> BotService:
        """Создать BotService."""
        return BotService(bot, db_session)
    
    def _create_help_service(self) -> HelpService:
        """Создать HelpService."""
        return HelpService()
    
    def _create_limits_service(self) -> LimitsService:
        """Создать LimitsService."""
        return LimitsService()
    
    def _create_admin_service(
        self, 
        moderation_service: ModerationService,
        bot_service: BotService,
        channel_service: ChannelService,
        profile_service: ProfileService,
        help_service: HelpService,
        limits_service: LimitsService,
    ) -> AdminService:
        """Создать AdminService."""
        return AdminService(
            moderation_service=moderation_service,
            bot_service=bot_service,
            channel_service=channel_service,
            profile_service=profile_service,
            help_service=help_service,
            limits_service=limits_service,
        )
    
    def _create_status_service(
        self,
        moderation_service: ModerationService,
        bot_service: BotService,
        channel_service: ChannelService,
    ) -> StatusService:
        """Создать StatusService."""
        return StatusService(
            moderation_service=moderation_service,
            bot_service=bot_service,
            channel_service=channel_service,
        )
    
    def _create_channels_admin_service(self, channel_service: ChannelService) -> ChannelsAdminService:
        """Создать ChannelsAdminService."""
        return ChannelsAdminService(channel_service)
    
    def _create_bots_admin_service(self, bot_service: BotService) -> BotsAdminService:
        """Создать BotsAdminService."""
        return BotsAdminService(bot_service)
    
    def _create_suspicious_admin_service(self, profile_service: ProfileService) -> SuspiciousAdminService:
        """Создать SuspiciousAdminService."""
        return SuspiciousAdminService(profile_service)
    
    def _create_callbacks_service(
        self,
        moderation_service: ModerationService,
        profile_service: ProfileService,
    ) -> CallbacksService:
        """Создать CallbacksService."""
        return CallbacksService(
            moderation_service=moderation_service,
            profile_service=profile_service,
        )
    
    def get(self, service_type: Type[T], **kwargs) -> T:
        """Получить сервис из контейнера."""
        return self.container.resolve(service_type, **kwargs)
    
    def get_all_services(self, bot: Bot, db_session: AsyncSession) -> Dict[str, Any]:
        """Получить все сервисы для хендлеров."""
        config = self.get(Settings)
        admin_id = config.admin_ids_list[0] if config.admin_ids_list else 0
        admin_ids = config.admin_ids_list
        
        # Создаем основные сервисы
        moderation_service = self.get(ModerationService, bot=bot, db_session=db_session)
        link_service = self.get(LinkService, bot=bot, db_session=db_session)
        profile_service = self.get(ProfileService, bot=bot, db_session=db_session)
        channel_service = self.get(ChannelService, bot=bot, db_session=db_session, config=config)
        bot_service = self.get(BotService, bot=bot, db_session=db_session)
        help_service = self.get(HelpService)
        limits_service = self.get(LimitsService)
        
        # Создаем админские сервисы вручную (из-за сложных зависимостей)
        admin_service = AdminService(
            moderation_service=moderation_service,
            bot_service=bot_service,
            channel_service=channel_service,
            profile_service=profile_service,
            help_service=help_service,
            limits_service=limits_service,
        )
        status_service = StatusService(
            moderation_service=moderation_service,
            bot_service=bot_service,
            channel_service=channel_service,
        )
        channels_admin_service = ChannelsAdminService(channel_service)
        bots_admin_service = BotsAdminService(bot_service)
        suspicious_admin_service = SuspiciousAdminService(profile_service)
        callbacks_service = CallbacksService(
            moderation_service=moderation_service,
            profile_service=profile_service,
        )
        
        # Redis rate limiter (singleton)
        redis_rate_limiter = get_redis_rate_limiter()
        
        return {
            # Основные сервисы для антиспама
            "moderation_service": moderation_service,
            "link_service": link_service,
            "profile_service": profile_service,
            "channel_service": channel_service,
            "bot_service": bot_service,
            "help_service": help_service,
            "limits_service": limits_service,
            # Админские сервисы
            "admin_service": admin_service,
            "status_service": status_service,
            "channels_admin_service": channels_admin_service,
            "bots_admin_service": bots_admin_service,
            "suspicious_admin_service": suspicious_admin_service,
            "callbacks_service": callbacks_service,
            # Rate limiting
            "redis_rate_limiter": redis_rate_limiter,
            # Метаданные
            "admin_id": admin_id,
            "admin_ids": admin_ids,
            "db_session": db_session,
        }


# Глобальный экземпляр контейнера
container = DIContainer()
