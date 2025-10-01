"""
Dependency Injection Middleware для Aiogram 3.x.

Этот middleware предоставляет встроенный DI контейнер для Aiogram,
заменяя внешние библиотеки типа punq.
"""

import logging
from typing import Any, Dict, Type, TypeVar
from aiogram import Bot
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.services.moderation import ModerationService
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.profiles import ProfileService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.admin import AdminService
from app.services.bots_admin import BotsAdminService
from app.services.channels_admin import ChannelsAdminService
from app.services.suspicious_admin import SuspiciousAdminService
from app.services.callbacks import CallbacksService
from app.services.links import LinkService

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIMiddleware(BaseMiddleware):
    """
    Middleware для Dependency Injection в Aiogram 3.x.
    
    Создает и кэширует все сервисы, предоставляя их хендлерам
    через data dictionary.
    """
    
    def __init__(self):
        super().__init__()
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Основной метод middleware.
        
        Создает сервисы при первом вызове и добавляет их в data.
        Оптимизирован для Aiogram 3.x с кэшированием и проверками.
        """
        if not self._initialized:
            await self._initialize_services(data)
            self._initialized = True
        
        # Добавляем все сервисы в data для хендлеров
        # Это позволяет хендлерам получать сервисы через DI
        data.update(self._services)
        
        # Логируем успешную инъекцию (только для отладки)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"DI services injected: {list(self._services.keys())}")
        
        return await handler(event, data)
    
    async def _initialize_services(self, data: Dict[str, Any]) -> None:
        """
        Инициализация всех сервисов.
        
        Создает все сервисы один раз и кэширует их.
        """
        try:
            # Получаем основные зависимости из data
            bot = data.get('bot')
            config = data.get('config')
            
            if not all([bot, config]):
                logger.error("Missing required dependencies: bot or config")
                return
            
            # Type assertions для mypy
            assert isinstance(bot, Bot)
            assert isinstance(config, Settings)
            
            # Создаем db_session
            from app.database import SessionLocal
            db_session = SessionLocal()
            
            # Добавляем admin_id в data
            data['admin_id'] = config.admin_ids[0]
            
            logger.info("Initializing DI services...")
            
            # Создаем базовые сервисы
            moderation_service = ModerationService(bot, db_session)
            bot_service = BotService(bot, db_session)
            channel_service = ChannelService(bot, db_session, config.native_channel_ids_list)
            profile_service = ProfileService(bot, db_session)
            help_service = HelpService()
            limits_service = LimitsService()
            
            # Создаем status_service
            from app.services.status import StatusService
            status_service = StatusService(
                moderation_service=moderation_service,
                bot_service=bot_service,
                channel_service=channel_service,
            )
            
            # Создаем сервисы с зависимостями
            admin_service = AdminService(
                moderation_service=moderation_service,
                bot_service=bot_service,
                channel_service=channel_service,
                profile_service=profile_service,
                help_service=help_service,
                limits_service=limits_service,
            )
            
            bots_admin_service = BotsAdminService(
                bot_service=bot_service,
            )
            
            channels_admin_service = ChannelsAdminService(
                channel_service=channel_service,
            )
            
            suspicious_admin_service = SuspiciousAdminService(
                profile_service=profile_service,
            )
            
            callbacks_service = CallbacksService(
                moderation_service=moderation_service,
                profile_service=profile_service,
            )
            
            # Создаем LinkService (он создает свои зависимости внутри себя)
            link_service = LinkService(
                bot=bot,
                db_session=db_session,
            )
            
            # RedisService временно отключен из-за проблем с aioredis на Python 3.11
            # from app.services.redis import RedisService
            # redis_service = RedisService()
            
            # Сохраняем все сервисы
            self._services = {
                'moderation_service': moderation_service,
                'bot_service': bot_service,
                'channel_service': channel_service,
                'profile_service': profile_service,
                'help_service': help_service,
                'limits_service': limits_service,
                'status_service': status_service,
                'admin_service': admin_service,
                'bots_admin_service': bots_admin_service,
                'channels_admin_service': channels_admin_service,
                'suspicious_admin_service': suspicious_admin_service,
                'callbacks_service': callbacks_service,
                'link_service': link_service,
                # 'redis_service': redis_service,  # Временно отключен
            }
            
            logger.info(f"DI services initialized: {list(self._services.keys())}")
            
        except Exception as e:
            logger.error(f"Error initializing DI services: {e}")
            import traceback
            logger.error(f"DI initialization traceback: {traceback.format_exc()}")
            raise
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Получить сервис по типу.
        
        Args:
            service_type: Тип сервиса для получения
            
        Returns:
            Экземпляр сервиса
            
        Raises:
            KeyError: Если сервис не найден
        """
        service_name = self._get_service_name(service_type)
        if service_name not in self._services:
            raise KeyError(f"Service {service_name} not found")
        
        return self._services[service_name]
    
    def _get_service_name(self, service_type: Type[T]) -> str:
        """
        Получить имя сервиса по типу.
        
        Args:
            service_type: Тип сервиса
            
        Returns:
            Имя сервиса в словаре
        """
        # Простое преобразование типа в имя
        type_name = service_type.__name__
        
        # Маппинг типов на имена в словаре
        type_mapping = {
            'ModerationService': 'moderation_service',
            'BotService': 'bot_service',
            'ChannelService': 'channel_service',
            'ProfileService': 'profile_service',
            'HelpService': 'help_service',
            'LimitsService': 'limits_service',
            'AdminService': 'admin_service',
            'BotsAdminService': 'bots_admin_service',
            'ChannelsAdminService': 'channels_admin_service',
            'SuspiciousAdminService': 'suspicious_admin_service',
            'CallbacksService': 'callbacks_service',
            'LinkService': 'link_service',
        }
        
        return type_mapping.get(type_name, type_name.lower())
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        Получить все сервисы.
        
        Returns:
            Словарь всех сервисов
        """
        return self._services.copy()
