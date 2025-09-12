"""Enhanced authorization system with proper security checks."""

import logging
from enum import Enum
from functools import wraps
from typing import List, Optional

from aiogram.types import CallbackQuery, Message

from app.config import load_config
from app.utils.security import safe_format_message, sanitize_for_logging, validate_user_id

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Available permissions."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    MODERATE = "moderate"
    VIEW_LOGS = "view_logs"
    MANAGE_USERS = "manage_users"
    MANAGE_CHANNELS = "manage_channels"
    MANAGE_BOTS = "manage_bots"
    CHANGE_LIMITS = "change_limits"


class Role(Enum):
    """User roles with permissions."""

    USER = [Permission.READ]
    MODERATOR = [Permission.READ, Permission.WRITE, Permission.MODERATE]
    ADMIN = [
        Permission.READ,
        Permission.WRITE,
        Permission.ADMIN,
        Permission.MODERATE,
        Permission.VIEW_LOGS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_CHANNELS,
        Permission.MANAGE_BOTS,
    ]
    SUPER_ADMIN = [
        Permission.READ,
        Permission.WRITE,
        Permission.ADMIN,
        Permission.SUPER_ADMIN,
        Permission.MODERATE,
        Permission.VIEW_LOGS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_CHANNELS,
        Permission.MANAGE_BOTS,
        Permission.CHANGE_LIMITS,
    ]


class AuthorizationService:
    """Service for handling user authorization and permissions."""

    def __init__(self):
        self.config = load_config()
        self.admin_ids = set(self.config.admin_ids_list)
        self.super_admin_id = self.config.admin_ids_list[0] if self.config.admin_ids_list else None

    def get_user_role(self, user_id: int) -> Role:
        """Get user role based on user ID."""
        if not validate_user_id(user_id):
            return Role.USER

        if user_id == self.super_admin_id:
            return Role.SUPER_ADMIN
        elif user_id in self.admin_ids:
            return Role.ADMIN
        else:
            return Role.USER

    def has_permission(self, user_id: int, permission: Permission) -> bool:
        """Check if user has specific permission."""
        if not validate_user_id(user_id):
            logger.warning(
                safe_format_message(
                    "Invalid user ID in permission check: {user_id}",
                    user_id=sanitize_for_logging(user_id),
                )
            )
            return False

        role = self.get_user_role(user_id)
        return permission in role.value

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return self.has_permission(user_id, Permission.ADMIN)

    def is_super_admin(self, user_id: int) -> bool:
        """Check if user is super admin."""
        return self.has_permission(user_id, Permission.SUPER_ADMIN)

    def can_moderate(self, user_id: int) -> bool:
        """Check if user can moderate."""
        return self.has_permission(user_id, Permission.MODERATE)

    def can_manage_users(self, user_id: int) -> bool:
        """Check if user can manage users."""
        return self.has_permission(user_id, Permission.MANAGE_USERS)

    def can_change_limits(self, user_id: int) -> bool:
        """Check if user can change limits."""
        return self.has_permission(user_id, Permission.CHANGE_LIMITS)

    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for user."""
        if not validate_user_id(user_id):
            return []

        role = self.get_user_role(user_id)
        return role.value

    def validate_action(self, user_id: int, action: str, target_id: Optional[int] = None) -> bool:
        """Validate if user can perform action on target."""
        if not validate_user_id(user_id):
            return False

        # Super admin can do everything
        if self.is_super_admin(user_id):
            return True

        # Admin can do most things
        if self.is_admin(user_id):
            # Admins can't modify super admin
            if target_id and target_id == self.super_admin_id:
                return False
            return True

        # Regular users have limited permissions
        if action in ["read", "help"]:
            return True

        return False


def require_permission(permission: Permission):
    """Decorator to require specific permission."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from arguments
            user_id = None

            # Try to get user_id from args (aiogram 3.x style)
            for arg in args:
                if isinstance(arg, (Message, CallbackQuery)):
                    user_id = arg.from_user.id if arg.from_user else None
                    break

            # Try to get user_id from kwargs (fallback)
            if not user_id:
                for key, value in kwargs.items():
                    if isinstance(value, (Message, CallbackQuery)):
                        user_id = value.from_user.id if value.from_user else None
                        break

            if not user_id:
                logger.error("Could not extract user_id from function arguments")
                return

            auth_service = AuthorizationService()
            if not auth_service.has_permission(user_id, permission):
                logger.warning(
                    safe_format_message(
                        "User {user_id} attempted unauthorized action {action}",
                        user_id=sanitize_for_logging(user_id),
                        action=sanitize_for_logging(permission.value),
                    )
                )

                # Send error message if possible
                for arg in args:
                    if isinstance(arg, Message):
                        await arg.answer("❌ У вас нет прав для выполнения этого действия")
                        return
                    elif isinstance(arg, CallbackQuery):
                        await arg.answer("❌ У вас нет прав для выполнения этого действия")
                        return
                return

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(func):
    """Decorator to require admin permission."""
    return require_permission(Permission.ADMIN)(func)


def require_super_admin(func):
    """Decorator to require super admin permission."""
    return require_permission(Permission.SUPER_ADMIN)(func)


def require_moderator(func):
    """Decorator to require moderator permission."""
    return require_permission(Permission.MODERATE)(func)


def safe_user_operation(user_id: int, operation: str, target_id: Optional[int] = None) -> bool:
    """Safely check if user can perform operation on target."""
    try:
        auth_service = AuthorizationService()
        return auth_service.validate_action(user_id, operation, target_id)
    except Exception as e:
        logger.error(
            safe_format_message(
                "Error in safe_user_operation: {error}", error=sanitize_for_logging(e)
            )
        )
        return False


def log_security_event(event_type: str, user_id: int, details: str = ""):
    """Log security-related events."""
    logger.warning(
        safe_format_message(
            "SECURITY_EVENT: {event_type} - User: {user_id} - Details: {details}",
            event_type=sanitize_for_logging(event_type),
            user_id=sanitize_for_logging(user_id),
            details=sanitize_for_logging(details),
        )
    )
