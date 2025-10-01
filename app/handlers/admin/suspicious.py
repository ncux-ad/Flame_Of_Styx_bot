"""
Команды для работы с подозрительными профилями
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.profiles import ProfileService
from app.utils.error_handling import handle_errors
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)

# Создаем роутер для команд подозрительных профилей
suspicious_router = Router()


@suspicious_router.message(Command("suspicious"))
async def handle_suspicious_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Показать подозрительные профили."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious command from {sanitize_for_logging(str(message.from_user.id))}")

        # Получаем подозрительные профили
        profiles = await profile_service.get_suspicious_profiles(limit=10)
        
        if not profiles:
            await message.answer("✅ Подозрительных профилей не найдено")
            return

        text = "🔍 <b>Подозрительные профили:</b>\n\n"
        
        for i, profile in enumerate(profiles, 1):
            # Получаем информацию о пользователе
            user_info = await profile_service.get_user_info(int(str(profile.user_id)))
            username = f"@{user_info.get('username')}" if user_info.get('username') else "Нет username"
            name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            
            # Экранируем HTML символы
            def escape_html(text):
                if not text:
                    return ""
                return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            text += f"{i}. <b>{escape_html(name)}</b>\n"
            text += f"   ID: <code>{profile.user_id}</code>\n"
            text += f"   Username: {escape_html(username)}\n"
            text += f"   Счет подозрительности: {profile.suspicion_score:.2f}\n"
            text += f"   Паттерны: {escape_html(str(profile.detected_patterns))}\n"
            if profile.linked_chat_title and str(profile.linked_chat_title).strip():
                text += f"   Связанный чат: {escape_html(str(profile.linked_chat_title))}\n"
            text += f"   Дата: {profile.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

        text += "💡 <b>Команды управления:</b>\n"
        text += "• /suspicious_reset - сбросить все подозрительные профили\n"
        text += "• /suspicious_analyze <user_id> - проанализировать пользователя\n"
        text += "• /suspicious_remove <user_id> - удалить из подозрительных\n"
        
        # Отладочная информация
        logger.info(f"Generated text length: {len(text)}")
        logger.info(f"Text preview: {text[:500]}...")
        
        # Проверяем на наличие подозрительных символов
        if '<user_id' in text:
            logger.error("Found '<user_id' in text!")
            text = text.replace('<user_id', '&lt;user_id')
        if 'user_id>' in text:
            logger.error("Found 'user_id>' in text!")
            text = text.replace('user_id>', 'user_id&gt;')
        
        await message.answer(text)
        logger.info(f"Suspicious profiles response sent to {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in suspicious command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка получения подозрительных профилей")


@suspicious_router.message(Command("suspicious_reset"))
async def handle_suspicious_reset_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Сбросить все подозрительные профили."""
    try:
        if not message.from_user:
            return
        logger.info(f"Suspicious reset command from {sanitize_for_logging(str(message.from_user.id))}")

        # Сбрасываем все подозрительные профили
        deleted_count = await profile_service.reset_suspicious_profiles()
        
        await message.answer(
            f"✅ <b>Подозрительные профили сброшены</b>\n\n"
            f"🗑️ Удалено записей: {deleted_count}\n"
            f"📊 Система анализа сброшена"
        )
        logger.info(f"Reset {sanitize_for_logging(str(deleted_count))} suspicious profiles for {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in suspicious_reset command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка сброса подозрительных профилей")


@suspicious_router.message(Command("recalculate_suspicious"))
async def handle_recalculate_suspicious_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Пересчитать подозрительные профили с новыми весами."""
    try:
        if not message.from_user:
            return
        logger.info(f"Recalculate suspicious command from {sanitize_for_logging(str(message.from_user.id))}")

        # Пересчитываем все подозрительные профили
        recalculated_count = await profile_service.recalculate_suspicious_profiles()
        
        await message.answer(
            f"✅ <b>Подозрительные профили пересчитаны</b>\n\n"
            f"🔄 Пересчитано профилей: {recalculated_count}\n"
            f"📊 Применены обновленные веса паттернов"
        )
        logger.info(f"Recalculated {sanitize_for_logging(str(recalculated_count))} suspicious profiles for {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in recalculate_suspicious command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка пересчета подозрительных профилей")


@suspicious_router.message(Command("cleanup_duplicates"))
async def handle_cleanup_duplicates_command(
    message: Message,
    profile_service: ProfileService,
    admin_id: int,
) -> None:
    """Очистить дублирующие подозрительные профили."""
    try:
        if not message.from_user:
            return
        logger.info(f"Cleanup duplicates command from {sanitize_for_logging(str(message.from_user.id))}")

        # Очищаем дублирующие записи
        cleaned_count = await profile_service.cleanup_duplicate_profiles()
        
        await message.answer(
            f"✅ <b>Дублирующие профили очищены</b>\n\n"
            f"🗑️ Удалено дубликатов: {cleaned_count}\n"
            f"📊 Оставлены только самые свежие записи"
        )
        logger.info(f"Cleaned up {sanitize_for_logging(str(cleaned_count))} duplicate profiles for {sanitize_for_logging(str(message.from_user.id))}")

    except Exception as e:
        logger.error(f"Error in cleanup_duplicates command: {sanitize_for_logging(str(e))}")
        await message.answer("❌ Ошибка очистки дубликатов")