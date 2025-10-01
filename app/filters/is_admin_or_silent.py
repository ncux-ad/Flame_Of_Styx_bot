"""Admin filter that silently ignores non-admin users."""

from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.config import load_config


class IsAdminOrSilentFilter(BaseFilter):
    """Filter that allows admins and silently ignores non-admins."""

    def __init__(self):
        # Load config once during initialization
        self.config = load_config()
        self.admin_ids = self.config.admin_ids_list

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        """Check if user is admin, silently ignore others."""
        try:
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
            is_admin = user_id in self.admin_ids

            # Log admin filter results for debugging
            logger = __import__("logging").getLogger(__name__)
            if isinstance(obj, Message):
                logger.info(f"Admin filter: user {user_id}, is_admin: {is_admin}, text: {obj.text}")
                if obj.text and "bots" in obj.text.lower():
                    logger.info(f"BOTS COMMAND DETECTED: user {user_id}, is_admin: {is_admin}, admin_ids: {self.admin_ids}")

            # Log non-admin attempts for security monitoring
            if not is_admin:
                if isinstance(obj, Message):
                    logger.info(f"Non-admin user {user_id} attempted to use bot: {obj.text}")

            return is_admin
        except Exception as e:
            # If there's an error, deny access for security
            logger = __import__("logging").getLogger(__name__)
            logger.error(f"Error in admin filter: {e}")
            return False
