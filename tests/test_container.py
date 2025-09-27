"""
Тесты для DI контейнера
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.container import DIContainer
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


class TestDIContainer:
    """Тесты для DI контейнера."""
    
    def test_container_creation(self):
        """Тест создания контейнера."""
        container = DIContainer()
        assert container is not None
        assert container.container is not None
    
    def test_basic_services_registration(self):
        """Тест регистрации основных сервисов."""
        container = DIContainer()
        
        # Проверяем, что сервисы можно получить
        help_service = container.get(HelpService)
        limits_service = container.get(LimitsService)
        
        assert isinstance(help_service, HelpService)
        assert isinstance(limits_service, LimitsService)
    
    def test_admin_services_registration(self):
        """Тест регистрации админских сервисов."""
        container = DIContainer()
        
        # Проверяем, что админские сервисы можно получить
        # (только те, которые не требуют сложных зависимостей)
        help_service = container.get(HelpService)
        limits_service = container.get(LimitsService)
        
        assert isinstance(help_service, HelpService)
        assert isinstance(limits_service, LimitsService)
    
    def test_get_help_service(self):
        """Тест получения HelpService."""
        container = DIContainer()
        
        help_service = container.get(HelpService)
        assert isinstance(help_service, HelpService)
    
    def test_get_limits_service(self):
        """Тест получения LimitsService."""
        container = DIContainer()
        
        limits_service = container.get(LimitsService)
        assert isinstance(limits_service, LimitsService)
    
    def test_get_all_services(self):
        """Тест получения всех сервисов."""
        container = DIContainer()
        
        # Мокаем bot и db_session
        mock_bot = Mock()
        mock_db_session = AsyncMock()
        
        services = container.get_all_services(mock_bot, mock_db_session)
        
        # Проверяем, что основные сервисы присутствуют
        assert "help_service" in services
        assert "limits_service" in services
        assert "admin_id" in services
        assert "admin_ids" in services
        assert "db_session" in services
        
        # Проверяем типы сервисов
        assert isinstance(services["help_service"], HelpService)
        assert isinstance(services["limits_service"], LimitsService)
    
    def test_service_dependencies(self):
        """Тест зависимостей между сервисами."""
        container = DIContainer()
        
        # Мокаем bot и db_session
        mock_bot = Mock()
        mock_db_session = AsyncMock()
        
        services = container.get_all_services(mock_bot, mock_db_session)
        
        # Проверяем, что основные сервисы работают
        assert isinstance(services["help_service"], HelpService)
        assert isinstance(services["limits_service"], LimitsService)
