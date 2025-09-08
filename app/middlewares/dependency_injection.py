"""Dependency Injection middleware for aiogram."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.database import SessionLocal, get_db
from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.links import LinkService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService


class DependencyInjectionMiddleware(BaseMiddleware):
    """Middleware for dependency injection."""

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Inject dependencies into handler."""
        # Get bot instance
        bot = event.bot

        # Get database session
        async with SessionLocal() as db_session:
            # Create services
            services = {
                "link_service": LinkService(bot, db_session),
                "profile_service": ProfileService(bot, db_session),
                "channel_service": ChannelService(bot, db_session),
                "bot_service": BotService(bot, db_session),
                "moderation_service": ModerationService(bot, db_session),
                "db_session": db_session,
            }

            # Add services to data
            data.update(services)

            # Call handler with event and data (aiogram 3.x style)
            # According to aiogram 3 docs, middleware should pass data dict
            return await handler(event, data)
