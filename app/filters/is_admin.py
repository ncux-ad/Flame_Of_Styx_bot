"""Admin filter for checking admin permissions."""

from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.config import load_config


class IsAdminFilter(BaseFilter):
    """Filter to check if user is admin."""

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        """Check if user is admin."""
        config = load_config()

        # Get user ID
        if isinstance(obj, Message):
            user_id = obj.from_user.id if obj.from_user else None
        elif isinstance(obj, CallbackQuery):
            user_id = obj.from_user.id if obj.from_user else None
        else:
            return False

        if not user_id:
            return False

        # Check if user is in admin list
        return user_id in config.admin_ids_list
