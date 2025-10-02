"""
Универсальная система обработки ошибок для AntiSpam Bot
"""

import logging
import traceback
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
)
from aiogram.types import CallbackQuery, Message

from app.constants import ERROR_MESSAGES, ErrorCodes
from app.utils.security import log_security_event, sanitize_for_logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Категории ошибок"""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    DATABASE = "database"
    TELEGRAM_API = "telegram_api"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    SECURITY = "security"


class BotError(Exception):
    """Базовый класс для ошибок бота"""

    def __init__(
        self,
        message: str,
        code: int = ErrorCodes.UNKNOWN_ERROR,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or ERROR_MESSAGES.get("BOT_ERROR", "Произошла ошибка бота")


class ValidationError(BotError):
    """Ошибка валидации"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.INVALID_REQUEST,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=ERROR_MESSAGES["INVALID_INPUT"],
        )


class AuthenticationError(BotError):
    """Ошибка аутентификации"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.UNAUTHORIZED,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=ERROR_MESSAGES["UNAUTHORIZED"],
        )


class AuthorizationError(BotError):
    """Ошибка авторизации"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.FORBIDDEN,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=ERROR_MESSAGES["UNAUTHORIZED"],
        )


class RateLimitError(BotError):
    """Ошибка превышения лимитов"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=ERROR_MESSAGES["RATE_LIMIT_EXCEEDED"],
        )


class DatabaseError(BotError):
    """Ошибка базы данных"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.DB_QUERY_ERROR,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details=details,
            user_message=ERROR_MESSAGES["BOT_ERROR"],
        )


class BotTelegramAPIError(BotError):
    """Ошибка Telegram API"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.UNKNOWN_ERROR,
            category=ErrorCategory.TELEGRAM_API,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            user_message=ERROR_MESSAGES["BOT_ERROR"],
        )


class SecurityError(BotError):
    """Ошибка безопасности"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=ErrorCodes.UNKNOWN_ERROR,
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            user_message=ERROR_MESSAGES["BOT_ERROR"],
        )


class ErrorHandler:
    """Универсальный обработчик ошибок"""

    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_thresholds = {
            ErrorSeverity.LOW: 100,
            ErrorSeverity.MEDIUM: 50,
            ErrorSeverity.HIGH: 20,
            ErrorSeverity.CRITICAL: 5,
        }

    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> None:
        """
        Обрабатывает ошибку.

        Args:
            error: Ошибка для обработки
            context: Контекст ошибки
            user_id: ID пользователя
            chat_id: ID чата
        """
        try:
            # Определяем тип ошибки
            bot_error = self._classify_error(error)

            # Логируем ошибку
            await self._log_error(bot_error, context, user_id, chat_id)

            # Проверяем лимиты ошибок
            await self._check_error_limits(bot_error)

            # Логируем событие безопасности для критических ошибок
            if bot_error.severity == ErrorSeverity.CRITICAL:
                await self._log_security_event(bot_error, context, user_id, chat_id)

        except Exception as e:
            logger.error(f"Ошибка в обработчике ошибок: {e}")

    def _classify_error(self, error: Exception) -> BotError:
        """
        Классифицирует ошибку.

        Args:
            error: Ошибка для классификации

        Returns:
            BotError объект
        """
        if isinstance(error, BotError):
            return error

        # Классификация стандартных ошибок
        if isinstance(error, TelegramBadRequest):
            return BotTelegramAPIError(message=f"Telegram Bad Request: {error}", details={"original_error": str(error)})

        if isinstance(error, TelegramForbiddenError):
            return BotTelegramAPIError(message=f"Telegram Forbidden: {error}", details={"original_error": str(error)})

        if isinstance(error, TelegramAPIError):
            return BotTelegramAPIError(message=f"Telegram API Error: {error}", details={"original_error": str(error)})

        if isinstance(error, ValueError):
            return ValidationError(message=f"Validation Error: {error}", details={"original_error": str(error)})

        if isinstance(error, PermissionError):
            return AuthorizationError(message=f"Permission Error: {error}", details={"original_error": str(error)})

        # Неизвестная ошибка
        return BotError(
            message=f"Unknown Error: {error}", details={"original_error": str(error), "traceback": traceback.format_exc()}
        )

    async def _log_error(
        self, error: BotError, context: Optional[Dict[str, Any]], user_id: Optional[int], chat_id: Optional[int]
    ) -> None:
        """
        Логирует ошибку.

        Args:
            error: Ошибка для логирования
            context: Контекст ошибки
            user_id: ID пользователя
            chat_id: ID чата
        """
        # Санитизируем контекст
        safe_context = {}
        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    safe_context[key] = sanitize_for_logging(value)
                else:
                    safe_context[key] = value

        # Логируем в зависимости от серьезности
        log_message = (
            f"Error [{error.category.value.upper()}] "
            f"[{error.severity.value.upper()}] "
            f"Code: {error.code} - {error.message}"
        )

        if user_id:
            log_message += f" | User: {user_id}"
        if chat_id:
            log_message += f" | Chat: {chat_id}"
        if safe_context:
            log_message += f" | Context: {safe_context}"

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    async def _check_error_limits(self, error: BotError) -> None:
        """
        Проверяет лимиты ошибок.

        Args:
            error: Ошибка для проверки
        """
        error_key = f"{error.category.value}_{error.severity.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        threshold = self.error_thresholds.get(error.severity, 50)
        if self.error_counts[error_key] > threshold:
            logger.critical(
                f"Error threshold exceeded for {error_key}: " f"{self.error_counts[error_key]} errors (threshold: {threshold})"
            )

    async def _log_security_event(
        self, error: BotError, context: Optional[Dict[str, Any]], user_id: Optional[int], chat_id: Optional[int]
    ) -> None:
        """
        Логирует событие безопасности.

        Args:
            error: Ошибка для логирования
            context: Контекст ошибки
            user_id: ID пользователя
            chat_id: ID чата
        """
        log_security_event(
            "critical_error",
            user_id,
            {
                "error_code": error.code,
                "error_category": error.category.value,
                "error_severity": error.severity.value,
                "error_message": sanitize_for_logging(error.message),
                "chat_id": chat_id,
                "context": context,
            },
        )


# Глобальный обработчик ошибок
error_handler = ErrorHandler()


def handle_errors(user_message: Optional[str] = None, log_error: bool = True, reraise: bool = False):
    """
    Декоратор для обработки ошибок в функциях.

    Args:
        user_message: Сообщение для пользователя
        log_error: Логировать ли ошибку
        reraise: Пробрасывать ли ошибку дальше
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    # Извлекаем контекст из аргументов
                    context = {}
                    user_id = None
                    chat_id = None

                    for arg in args:
                        if isinstance(arg, Message):
                            user_id = arg.from_user.id if arg.from_user else None
                            chat_id = arg.chat.id if arg.chat else None
                            context["message_text"] = sanitize_for_logging(arg.text) if arg.text else None
                        elif isinstance(arg, CallbackQuery):
                            user_id = arg.from_user.id if arg.from_user else None
                            chat_id = arg.message.chat.id if arg.message and arg.message.chat else None
                            context["callback_data"] = sanitize_for_logging(arg.data) if arg.data else None

                    await error_handler.handle_error(e, context, user_id, chat_id)

                # Отправляем сообщение пользователю
                if user_message:
                    try:
                        for arg in args:
                            if isinstance(arg, Message):
                                await arg.answer(user_message)
                                break
                            elif isinstance(arg, CallbackQuery):
                                await arg.answer(user_message)
                                break
                    except Exception as send_error:
                        logger.error(f"Ошибка отправки сообщения об ошибке: {send_error}")

                if reraise:
                    raise

                return None

        return wrapper

    return decorator


async def send_error_message(
    event: Union[Message, CallbackQuery], error: BotError, custom_message: Optional[str] = None
) -> None:
    """
    Отправляет сообщение об ошибке пользователю.

    Args:
        event: Telegram событие
        error: Ошибка
        custom_message: Пользовательское сообщение
    """
    try:
        message = custom_message or error.user_message

        if isinstance(event, Message):
            await event.answer(message)
        elif isinstance(event, CallbackQuery):
            await event.answer(message)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения об ошибке: {e}")


def get_error_summary() -> Dict[str, Any]:
    """
    Возвращает сводку по ошибкам.

    Returns:
        Словарь со статистикой ошибок
    """
    return {
        "error_counts": error_handler.error_counts.copy(),
        "total_errors": sum(error_handler.error_counts.values()),
        "error_thresholds": error_handler.error_thresholds.copy(),
    }
