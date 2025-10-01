"""
Команды для работы с лимитами
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.limits import LimitsService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging
from app.middlewares.silent_logging import send_silent_response

logger = logging.getLogger(__name__)

# Создаем роутер для команд лимитов
limits_router = Router()


@limits_router.message(Command("setlimits"))
async def handle_setlimits_command(
    message: Message,
    limits_service: LimitsService,
    admin_id: int,
) -> None:
    """Просмотр лимитов системы."""
    try:
        if not message.from_user:
            return
        logger.info(f"Setlimits command from {sanitize_for_logging(str(message.from_user.id))}")

        limits = limits_service.get_current_limits()
        
        text = "⚙️ <b>Текущие лимиты системы</b>\n\n"
        text += f"📊 <b>Сообщения:</b> {limits.get('max_messages_per_minute', 'N/A')} в минуту\n"
        text += f"🔗 <b>Ссылки:</b> {limits.get('max_links_per_message', 'N/A')} в сообщении\n"
        text += f"⏰ <b>Блокировка:</b> {limits.get('ban_duration_hours', 'N/A')} часов\n"
        text += f"🎯 <b>Порог подозрительности:</b> {limits.get('suspicion_threshold', 'N/A')}\n"
        text += f"📷 <b>Проверка медиа:</b> {'Включена' if limits.get('check_media_without_caption', False) else 'Отключена'}\n"
        text += f"🖼️ <b>Фото без подписи:</b> {'Разрешены' if limits.get('allow_photos_without_caption', False) else 'Запрещены'}\n"
        text += f"🎬 <b>Видео без подписи:</b> {'Разрешены' if limits.get('allow_videos_without_caption', False) else 'Запрещены'}\n"
        text += f"📄 <b>Размер документа:</b> {limits.get('max_document_size_suspicious', 'N/A')} байт\n\n"
        text += "💡 <b>Для изменения используйте:</b> /setlimit"

        await send_silent_response(message, text)
        logger.info(f"Limits sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in setlimits command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения лимитов")


@limits_router.message(Command("reload_limits"))
async def handle_reload_limits_command(
    message: Message,
    limits_service: LimitsService,
    admin_id: int,
) -> None:
    """Принудительная перезагрузка лимитов из файла."""
    try:
        if not message.from_user:
            return
        logger.info(f"Reload limits command from {sanitize_for_logging(str(message.from_user.id))}")

        # Перезагружаем лимиты
        success = limits_service.reload_limits()
        
        if success:
            await send_silent_response(message,
                "✅ <b>Лимиты перезагружены!</b>\n\n"
                "🔄 Все настройки обновлены из файла конфигурации\n"
                "📊 Изменения применены немедленно"
            )
        else:
            await send_silent_response(message, "❌ Ошибка при перезагрузке лимитов!")

        logger.info(f"Reload limits completed for {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in reload_limits command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка перезагрузки лимитов")
