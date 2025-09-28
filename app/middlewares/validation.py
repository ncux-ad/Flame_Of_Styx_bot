"""
Middleware для валидации входных данных
"""

import logging
from typing import Any, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.constants import ERROR_MESSAGES
from app.utils.security import (
    log_security_event,
    sanitize_for_logging,
    sanitize_user_input,
)
from app.utils.validation import input_validator, ValidationError, ValidationSeverity

logger = logging.getLogger(__name__)


class ValidationMiddleware(BaseMiddleware):
    """
    Middleware для валидации и санитизации входных данных.

    Проверяет:
    - Корректность сообщений
    - Безопасность пользовательского ввода
    - Валидность команд и параметров
    - Защиту от атак
    """

    async def __call__(
        self, handler: Callable[[TelegramObject, Dict[str, Any]], Any], event: TelegramObject, data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает событие с валидацией.

        Args:
            handler: Следующий обработчик
            event: Telegram событие
            data: Данные события

        Returns:
            Результат обработки
        """
        try:
            # Валидируем событие
            validation_result = await self._validate_event(event, data)

            if not validation_result["is_valid"]:
                await self._handle_validation_error(event, validation_result["errors"])
                return

            # Санитизируем данные
            await self._sanitize_event_data(event, data)

            # Логируем событие
            await self._log_event(event, data)

            # Передаем в следующий обработчик
            return await handler(event, data)

        except Exception as e:
            logger.error(f"Ошибка в ValidationMiddleware: {e}")
            await self._handle_validation_error(event, [f"Внутренняя ошибка: {str(e)}"])
            return

    async def _validate_event(self, event: TelegramObject, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидирует событие.

        Args:
            event: Telegram событие
            data: Данные события

        Returns:
            Результат валидации
        """
        errors = []

        if isinstance(event, Message):
            errors.extend(await self._validate_message(event))
        elif isinstance(event, CallbackQuery):
            errors.extend(await self._validate_callback_query(event))

        return {"is_valid": len(errors) == 0, "errors": errors}

    async def _validate_message(self, message: Message) -> List[str]:
        """
        Валидирует сообщение.

        Args:
            message: Сообщение для валидации

        Returns:
            Список ошибок валидации
        """
        # Для команд применяем только базовую валидацию
        if message.text and message.text.startswith("/"):
            # Для команд валидируем только текст сообщения, не профиль пользователя
            errors = []
            if message.text:
                text_errors = input_validator._validate_text_content(message.text, "message_text")
                for error in text_errors:
                    if error.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                        logger.warning(f"Command validation error: {error.field} - {error.message}")
                        errors.append(f"{error.field}: {error.message}")
            return errors
        
        # Проверяем, является ли это ответом в интерактивном режиме
        if message.from_user and message.text:
            # Импортируем словарь состояния (избегаем циклического импорта)
            try:
                from app.handlers.admin import waiting_for_user_input
                if message.from_user.id in waiting_for_user_input:
                    # Это ответ в интерактивном режиме - применяем только базовую валидацию
                    errors = []
                    if message.text:
                        text_errors = input_validator._validate_text_content(message.text, "message_text")
                        for error in text_errors:
                            if error.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH]:
                                logger.warning(f"Interactive input validation error: {error.field} - {error.message}")
                                errors.append(f"{error.field}: {error.message}")
                    return errors
            except ImportError:
                # Если не можем импортировать, продолжаем с обычной валидацией
                pass
        
        # Для обычных сообщений применяем полную валидацию
        validation_errors = input_validator.validate_message(message)
        
        # Конвертируем в старый формат для совместимости
        errors = []
        for error in validation_errors:
            # Логируем критические ошибки
            if error.severity == ValidationSeverity.CRITICAL:
                logger.critical(f"Critical validation error: {error.field} - {error.message}")
            elif error.severity == ValidationSeverity.HIGH:
                logger.warning(f"High severity validation error: {error.field} - {error.message}")
            
            errors.append(f"{error.field}: {error.message}")
        
        # Дополнительные проверки для медиа
        if message.photo or message.video or message.document:
            if not self._is_safe_media(message):
                errors.append("Небезопасное медиа")

        return errors

    async def _validate_callback_query(self, callback_query: CallbackQuery) -> List[str]:
        """
        Валидирует callback query.

        Args:
            callback_query: Callback query для валидации

        Returns:
            Список ошибок валидации
        """
        # Используем новый валидатор
        validation_errors = input_validator.validate_callback_query(callback_query)
        
        # Конвертируем в старый формат для совместимости
        errors = []
        for error in validation_errors:
            # Логируем критические ошибки
            if error.severity == ValidationSeverity.CRITICAL:
                logger.critical(f"Critical validation error: {error.field} - {error.message}")
            elif error.severity == ValidationSeverity.HIGH:
                logger.warning(f"High severity validation error: {error.field} - {error.message}")
            
            errors.append(f"{error.field}: {error.message}")

        return errors

    def _is_suspicious_text(self, text: str) -> bool:
        """
        Проверяет текст на подозрительные паттерны.

        Args:
            text: Текст для проверки

        Returns:
            True если текст подозрительный
        """
        suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # JavaScript
            r"javascript:",  # JavaScript URLs
            r"eval\s*\(",  # eval function
            r"alert\s*\(",  # alert function
            r"confirm\s*\(",  # confirm function
            r"prompt\s*\(",  # prompt function
            r"\.\./",  # Path traversal
            r"\.\.\\",  # Path traversal (Windows)
            r"SELECT.*FROM",  # SQL injection
            r"INSERT.*INTO",  # SQL injection
            r"UPDATE.*SET",  # SQL injection
            r"DELETE.*FROM",  # SQL injection
            r"DROP.*TABLE",  # SQL injection
        ]

        import re

        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True

        return False

    def _is_suspicious_callback_data(self, data: str) -> bool:
        """
        Проверяет callback data на подозрительные паттерны.

        Args:
            data: Callback data для проверки

        Returns:
            True если data подозрительные
        """
        suspicious_patterns = [
            r"<script",  # HTML/JavaScript
            r"javascript:",  # JavaScript URLs
            r"\.\./",  # Path traversal
            r"SELECT|INSERT|UPDATE|DELETE|DROP",  # SQL injection
        ]

        import re

        for pattern in suspicious_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return True

        return False

    def _is_safe_media(self, message: Message) -> bool:
        """
        Проверяет безопасность медиа.

        Args:
            message: Сообщение с медиа

        Returns:
            True если медиа безопасное
        """
        # Проверяем размер файлов
        if message.document:
            if message.document.file_size and message.document.file_size > 50 * 1024 * 1024:  # 50MB
                return False

        if message.video:
            if message.video.file_size and message.video.file_size > 100 * 1024 * 1024:  # 100MB
                return False

        if message.photo:
            # Проверяем размер самого большого фото
            if message.photo:
                largest_photo = max(message.photo, key=lambda p: p.file_size or 0)
                if largest_photo.file_size and largest_photo.file_size > 10 * 1024 * 1024:  # 10MB
                    return False

        return True

    async def _sanitize_event_data(self, event: TelegramObject, data: Dict[str, Any]) -> None:
        """
        Санитизирует данные события.

        Args:
            event: Telegram событие
            data: Данные события
        """
        # НЕ ИЗМЕНЯЕМ ЗАМОРОЖЕННЫЕ ОБЪЕКТЫ PYDANTIC
        # Вместо этого сохраняем санитизированные данные в data
        if isinstance(event, Message) and event.text:
            # Сохраняем санитизированный текст в data
            data["sanitized_text"] = sanitize_user_input(event.text)

        if isinstance(event, CallbackQuery) and event.data:
            # Сохраняем санитизированные данные в data
            data["sanitized_data"] = sanitize_user_input(event.data)

    async def _log_event(self, event: TelegramObject, data: Dict[str, Any]) -> None:
        """
        Логирует событие.

        Args:
            event: Telegram событие
            data: Данные события
        """
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            chat_id = event.chat.id if event.chat else None
            text = sanitize_for_logging(event.text) if event.text else None

            logger.info(f"Message validated: user_id={user_id}, chat_id={chat_id}, " f"text='{text[:100] if text else None}'")

        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            data_text = sanitize_for_logging(event.data) if event.data else None

            logger.info(f"Callback query validated: user_id={user_id}, " f"data='{data_text[:100] if data_text else None}'")

    async def _handle_validation_error(self, event: TelegramObject, errors: List[str]) -> None:
        """
        Обрабатывает ошибки валидации.

        Args:
            event: Telegram событие
            errors: Список ошибок
        """
        # Логируем ошибки валидации
        for error in errors:
            logger.warning(f"Validation error: {error}")

        # Логируем событие безопасности
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            log_security_event(
                "validation_error",
                user_id,
                {
                    "errors": errors,
                    "message_text": sanitize_for_logging(event.text) if event.text else None,
                    "chat_id": event.chat.id if event.chat else None,
                },
            )

        # Отправляем ответ пользователю (если это сообщение)
        if isinstance(event, Message):
            try:
                await event.answer(ERROR_MESSAGES["INVALID_INPUT"])
            except Exception as e:
                logger.error(f"Ошибка отправки ответа об ошибке валидации: {e}")


class CommandValidationMiddleware(BaseMiddleware):
    """
    Middleware для валидации команд.

    Проверяет:
    - Корректность команд
    - Валидность параметров команд
    - Безопасность команд
    """

    async def __call__(
        self, handler: Callable[[TelegramObject, Dict[str, Any]], Any], event: TelegramObject, data: Dict[str, Any]
    ) -> Any:
        """
        Обрабатывает команду с валидацией.

        Args:
            handler: Следующий обработчик
            event: Telegram событие
            data: Данные события

        Returns:
            Результат обработки
        """
        if isinstance(event, Message) and event.text and event.text.startswith("/"):
            # Валидируем команду
            validation_result = await self._validate_command(event)

            if not validation_result["is_valid"]:
                await self._handle_command_validation_error(event, validation_result["errors"])
                return

        return await handler(event, data)

    async def _validate_command(self, message: Message) -> Dict[str, Any]:
        """
        Валидирует команду.

        Args:
            message: Сообщение с командой

        Returns:
            Результат валидации
        """
        if not message.text:
            return {"is_valid": False, "errors": ["Отсутствует текст команды"]}

        # Извлекаем команду и параметры
        parts = message.text.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Используем новый валидатор
        validation_errors = input_validator.validate_command(command, args)
        
        # Конвертируем в старый формат для совместимости
        errors = []
        for error in validation_errors:
            # Логируем критические ошибки
            if error.severity == ValidationSeverity.CRITICAL:
                logger.critical(f"Critical command validation error: {error.field} - {error.message}")
            elif error.severity == ValidationSeverity.HIGH:
                logger.warning(f"High severity command validation error: {error.field} - {error.message}")
            
            errors.append(f"{error.field}: {error.message}")

        return {"is_valid": len(errors) == 0, "errors": errors}

    def _is_suspicious_text(self, text: str) -> bool:
        """
        Проверяет текст на подозрительные паттерны.

        Args:
            text: Текст для проверки

        Returns:
            True если текст подозрительный
        """
        suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # JavaScript
            r"javascript:",  # JavaScript URLs
            r"eval\s*\(",  # eval function
            r"\.\./",  # Path traversal
            r"SELECT.*FROM",  # SQL injection
        ]

        import re

        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True

        return False

    async def _handle_command_validation_error(self, message: Message, errors: List[str]) -> None:
        """
        Обрабатывает ошибки валидации команд.

        Args:
            message: Сообщение с командой
            errors: Список ошибок
        """
        # Логируем ошибки
        for error in errors:
            logger.warning(f"Command validation error: {error}")

        # Логируем событие безопасности
        user_id = message.from_user.id if message.from_user else None
        log_security_event(
            "command_validation_error",
            user_id,
            {
                "errors": errors,
                "command": sanitize_for_logging(message.text),
                "chat_id": message.chat.id if message.chat else None,
            },
        )

        # Не отправляем ответ - это делает основной ValidationMiddleware
        # try:
        #     await message.answer(ERROR_MESSAGES["INVALID_INPUT"])
        # except Exception as e:
        #     logger.error(f"Ошибка отправки ответа об ошибке валидации команды: {e}")
