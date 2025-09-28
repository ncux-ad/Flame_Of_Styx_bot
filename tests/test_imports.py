"""
Tests for basic imports and module loading
"""

import pytest


@pytest.mark.unit
class TestImports:
    """Test that all modules can be imported without errors."""
    
    def test_config_import(self):
        """Test config module import."""
        from app.config import load_config, Settings
        assert load_config is not None
        assert Settings is not None
    
    def test_redis_import(self):
        """Test Redis service import."""
        from app.services.redis import RedisService, get_redis_service
        assert RedisService is not None
        assert get_redis_service is not None
    
    def test_handlers_import(self):
        """Test handlers import."""
        from app.handlers.admin import admin_router
        assert admin_router is not None
    
    def test_services_import(self):
        """Test services import."""
        from app.services.help import HelpService
        from app.services.limits import LimitsService
        from app.services.moderation import ModerationService
        assert HelpService is not None
        assert LimitsService is not None
        assert ModerationService is not None
    
    def test_middlewares_import(self):
        """Test middlewares import."""
        from app.middlewares.ratelimit import RateLimitMiddleware
        from app.middlewares.validation import ValidationMiddleware
        assert RateLimitMiddleware is not None
        assert ValidationMiddleware is not None
