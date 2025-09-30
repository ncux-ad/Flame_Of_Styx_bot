"""
Rate Limit Admin Commands
Команды для управления Redis rate limiting
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.redis_rate_limiter import get_redis_rate_limiter
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging
from app.middlewares.silent_logging import send_silent_response

logger = logging.getLogger(__name__)

# Создаем роутер для rate limit команд
rate_limit_router = Router()


@rate_limit_router.message(Command("rate_limit"))
@handle_errors(user_message="❌ Ошибка получения информации о rate limit")
async def handle_rate_limit_command(
    message: Message,
    admin_id: int,
) -> None:
    """Показать информацию о rate limit."""
    try:
        if not message.from_user:
            return
        
        logger.info(f"Rate limit command from {sanitize_for_logging(str(message.from_user.id))}")
        
        # Получаем rate limiter
        rate_limiter = await get_redis_rate_limiter()
        
        # Получаем информацию о rate limit для пользователя
        user_id = str(message.from_user.id)
        
        # Собираем информацию по всем конфигурациям
        rate_limit_info = []
        
        for config_name in ["user_messages", "admin_commands", "spam_analysis", "channel_management"]:
            try:
                info = await rate_limiter.get_rate_limit_info(config_name, user_id)
                if "error" not in info:
                    rate_limit_info.append({
                        "config": config_name,
                        "info": info
                    })
            except Exception as e:
                logger.error(f"Error getting rate limit info for {config_name}: {e}")
        
        if not rate_limit_info:
            await send_silent_response(message, "❌ Не удалось получить информацию о rate limit")
            return
        
        # Формируем сообщение
        response_text = "⏰ <b>Информация о Rate Limit</b>\n\n"
        
        for item in rate_limit_info:
            config = item["config"]
            info = item["info"]
            
            config_names = {
                "user_messages": "Сообщения пользователей",
                "admin_commands": "Админские команды", 
                "spam_analysis": "Анализ спама",
                "channel_management": "Управление каналами"
            }
            
            config_display = config_names.get(config, config)
            
            response_text += f"📊 <b>{config_display}:</b>\n"
            response_text += f"• Использовано: {info['current_count']}/{info['max_requests']}\n"
            response_text += f"• Осталось: {info['remaining']}\n"
            response_text += f"• Окно: {info['window_seconds']}с\n"
            response_text += f"• Сброс через: {info['reset_in_seconds']:.0f}с\n\n"
        
        # Добавляем кнопки управления
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="rate_limit_refresh"
        ))
        keyboard.add(InlineKeyboardButton(
            text="🗑️ Сбросить все",
            callback_data="rate_limit_reset_all"
        ))
        keyboard.add(InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="rate_limit_stats"
        ))
        keyboard.adjust(2)
        
        await send_silent_response(
            message, 
            response_text,
            reply_markup=keyboard.as_markup()
        )
        
        logger.info(f"Rate limit info sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in rate limit command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения информации о rate limit")


@rate_limit_router.message(Command("reset_rate_limit"))
@handle_errors(user_message="❌ Ошибка сброса rate limit")
async def handle_reset_rate_limit_command(
    message: Message,
    admin_id: int,
) -> None:
    """Сбросить rate limit для пользователя."""
    try:
        if not message.from_user:
            return
        
        logger.info(f"Reset rate limit command from {sanitize_for_logging(str(message.from_user.id))}")
        
        # Получаем rate limiter
        rate_limiter = await get_redis_rate_limiter()
        
        user_id = str(message.from_user.id)
        
        # Сбрасываем rate limit для всех конфигураций
        reset_count = 0
        for config_name in ["user_messages", "admin_commands", "spam_analysis", "channel_management"]:
            try:
                success = await rate_limiter.reset_rate_limit(config_name, user_id)
                if success:
                    reset_count += 1
            except Exception as e:
                logger.error(f"Error resetting rate limit for {config_name}: {e}")
        
        if reset_count > 0:
            await send_silent_response(
                message, 
                f"✅ Rate limit сброшен для {reset_count} конфигураций"
            )
        else:
            await send_silent_response(
                message, 
                "❌ Не удалось сбросить rate limit"
            )
        
        logger.info(f"Rate limit reset for {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in reset rate limit command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка сброса rate limit")


@rate_limit_router.message(Command("rate_limit_stats"))
@handle_errors(user_message="❌ Ошибка получения статистики rate limit")
async def handle_rate_limit_stats_command(
    message: Message,
    admin_id: int,
) -> None:
    """Показать статистику rate limit."""
    try:
        if not message.from_user:
            return
        
        logger.info(f"Rate limit stats command from {sanitize_for_logging(str(message.from_user.id))}")
        
        # Получаем rate limiter
        rate_limiter = await get_redis_rate_limiter()
        
        # Получаем список всех конфигураций
        configs = rate_limiter.list_configs()
        
        response_text = "📊 <b>Статистика Rate Limit</b>\n\n"
        
        for config_name, config in configs.items():
            config_names = {
                "user_messages": "Сообщения пользователей",
                "admin_commands": "Админские команды",
                "spam_analysis": "Анализ спама", 
                "channel_management": "Управление каналами"
            }
            
            config_display = config_names.get(config_name, config_name)
            
            response_text += f"⚙️ <b>{config_display}:</b>\n"
            response_text += f"• Лимит: {config.max_requests}\n"
            response_text += f"• Окно: {config.window_seconds}с\n"
            response_text += f"• Префикс: {config.key_prefix}\n\n"
        
        response_text += "💡 <b>Примечание:</b>\n"
        response_text += "Rate limiting защищает от спама и перегрузки бота\n"
        response_text += "Используйте /reset_rate_limit для сброса лимитов"
        
        await send_silent_response(message, response_text)
        
        logger.info(f"Rate limit stats sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in rate limit stats command: {sanitize_for_logging(str(e))}")
        await send_silent_response(message, "❌ Ошибка получения статистики rate limit")
