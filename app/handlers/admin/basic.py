"""
Базовые админские команды
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.admin import AdminService
from app.services.status import StatusService
from app.services.help import HelpService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging
from app.middlewares.silent_logging import send_silent_response

logger = logging.getLogger(__name__)

# Создаем роутер для базовых команд
basic_router = Router()


@basic_router.message(Command("start"))
@handle_errors(user_message="❌ Ошибка выполнения команды /start")
async def handle_start_command(
    message: Message,
    admin_service: AdminService,
    admin_id: int,
) -> None:
    """Приветствие админа."""
    try:
        if not message.from_user:
            return
        logger.info(f"Start command from {sanitize_for_logging(str(message.from_user.id))}")

        welcome_message = await admin_service.get_welcome_message()
        await send_silent_response(message, welcome_message)
        logger.info(f"Welcome message sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in start command: {sanitize_for_logging(str(e))}")
        raise


@basic_router.message(Command("status"))
async def handle_status_command(
    message: Message,
    status_service: StatusService,
    admin_id: int,
) -> None:
    """Показать статус бота."""
    try:
        if not message.from_user:
            return
        logger.info(f"Status command from {sanitize_for_logging(str(message.from_user.id))}")

        status_text = await status_service.get_bot_status(admin_id)
        await send_silent_response(message, status_text)
        logger.info(f"Status sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in status command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения статуса")


@basic_router.message(Command("settings"))
async def handle_settings_command(message: Message) -> None:
    """Настройки бота."""
    try:
        if not message.from_user:
            return
        logger.info(f"Settings command from {sanitize_for_logging(str(message.from_user.id))}")

        settings_text = (
            "⚙️ <b>Настройки AntiSpam Bot</b>\n\n"
            "🔧 <b>Основные параметры:</b>\n"
            "• <b>Лимиты сообщений:</b> настраиваются через /setlimits\n"
            "• <b>Пороги подозрительности:</b> настраиваются через /setlimit\n"
            "• <b>Каналы:</b> управляются через /channels\n"
            "• <b>Боты:</b> управляются через /bots\n\n"
            "📊 <b>Мониторинг:</b>\n"
            "• <b>Статус:</b> /status\n"
            "• <b>Заблокированные:</b> /banned\n"
            "• <b>Подозрительные:</b> /suspicious\n\n"
            "🛠️ <b>Утилиты:</b>\n"
            "• <b>Синхронизация каналов:</b> /sync_channels\n"
            "• <b>Синхронизация банов:</b> /sync_bans\n"
            "• <b>Перезагрузка лимитов:</b> /reload_limits\n\n"
            "🔔 <b>Уведомления:</b>\n"
            "• <b>Показ лимитов при запуске:</b> включен (настраивается в .env)\n"
            "• <b>Переменная:</b> SHOW_LIMITS_ON_STARTUP=true/false\n\n"
            "❓ <b>Помощь:</b> /help"
        )

        await send_silent_response(message, settings_text)
        logger.info(f"Settings sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in settings command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения настроек")


@basic_router.message(Command("help"))
async def handle_help_command(
    message: Message,
    help_service: HelpService,
    admin_id: int,
) -> None:
    """Показать справку по командам."""
    try:
        if not message.from_user:
            return
        logger.info(f"Help command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем аргументы команды
        command_args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []
        
        if command_args:
            # Запрошена справка по категории
            category = command_args[0].lower()
            help_text = help_service.get_category_help(category, message.from_user.id)
        else:
            # Общая справка
            help_text = await help_service.get_help_text(message.from_user.id)
        
        await send_silent_response(message, help_text)
        logger.info(f"Help sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in help command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения справки")


@basic_router.message(Command("instructions"))
async def handle_instructions_command(
    message: Message,
    help_service: HelpService,
    admin_id: int,
) -> None:
    """Показать инструкции по использованию."""
    try:
        if not message.from_user:
            return
        logger.info(f"Instructions command from {sanitize_for_logging(str(message.from_user.id))}")

        instructions_text = await help_service.get_instructions_text(message.from_user.id)
        await send_silent_response(message, instructions_text)
        logger.info(f"Instructions sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in instructions command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения инструкций")


@basic_router.message(Command("logs"))
async def handle_logs_command(
    message: Message,
    admin_id: int,
) -> None:
    """Показать последние логи."""
    try:
        if not message.from_user:
            return
        logger.info(f"Logs command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем аргументы команды
        command_args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []
        log_level = command_args[0].lower() if command_args else "all"
        
        # Пробуем разные пути к файлу логов
        log_files = ["bot.log", "logs/bot.log", "/var/log/antispam-bot.log"]
        log_text = ""
        
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        # Фильтруем по уровню логирования
                        if log_level == "error":
                            filtered_lines = [line for line in lines if "ERROR" in line]
                        elif log_level == "warning":
                            filtered_lines = [line for line in lines if "WARNING" in line or "ERROR" in line]
                        elif log_level == "info":
                            filtered_lines = [line for line in lines if "INFO" in line]
                        else:
                            filtered_lines = lines
                        
                        # Берем последние 30 строк
                        last_lines = filtered_lines[-30:] if len(filtered_lines) > 30 else filtered_lines
                        log_text = "".join(last_lines)
                        break
            except (FileNotFoundError, PermissionError, OSError):
                continue
        
        if not log_text:
            log_text = "Файл логов не найден. Проверьте:\n• bot.log\n• logs/bot.log\n• /var/log/antispam-bot.log"
        else:
            # Ограничиваем длину сообщения
            if len(log_text) > 3500:
                log_text = "..." + log_text[-3500:]

        # Формируем заголовок в зависимости от уровня
        if log_level == "error":
            title = "Логи системы (error)"
        elif log_level == "warning":
            title = "Логи системы (warning)"
        elif log_level == "info":
            title = "Логи системы (info)"
        else:
            title = "Последние логи"

        await send_silent_response(message, f"<b>{title}</b>\n\n<code>{log_text}</code>")
        logger.info(f"Logs sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in logs command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения логов")
