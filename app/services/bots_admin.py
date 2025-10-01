"""
Bots Admin Service - бизнес-логика для команды /bots
"""

import logging
from typing import Dict, List, Any
from aiogram.types import Message

from app.services.bots import BotService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class BotsAdminService:
    """Сервис для управления ботами в админке."""
    
    def __init__(self, bot_service: BotService):
        self.bot_service = bot_service

    async def get_bots_list(self) -> str:
        """Получить список ботов для команды /bots."""
        try:
            bots = await self.bot_service.get_all_bots()
            
            if not bots:
                return (
                    "🤖 <b>Управление ботами</b>\n\n"
                    "📋 <b>Список ботов пуст</b>\n\n"
                    "💡 <b>Доступные команды:</b>\n"
                    "• /add_bot @username - добавить бота в whitelist\n"
                    "• /remove_bot @username - удалить бота из whitelist\n\n"
                    "🛡️ <b>Защита от ботов:</b>\n"
                    "• Автоматическое обнаружение ботов\n"
                    "• Блокировка неизвестных ботов\n"
                    "• Уведомления о новых ботах"
                )
            
            # Формируем текст
            bots_text = "🤖 <b>Управление ботами</b>\n\n"
            bots_text += f"📊 <b>Всего ботов:</b> {len(bots)}\n\n"
            
            # Группируем по статусу
            whitelist_bots = [bot for bot in bots if getattr(bot, 'is_whitelisted', True)]
            blacklist_bots = [bot for bot in bots if not getattr(bot, 'is_whitelisted', True)]
            
            if whitelist_bots:
                bots_text += "✅ <b>В whitelist:</b>\n"
                for i, bot in enumerate(whitelist_bots[:5], 1):
                    username = bot.username or 'Без username'
                    bots_text += f"{i}. @{username}\n"
                    first_name = getattr(bot, 'first_name', None)
                    if first_name and str(first_name).strip():
                        bots_text += f"   Имя: {first_name}\n"
                    bots_text += f"   ID: <code>{bot.id}</code>\n\n"
                
                if len(whitelist_bots) > 5:
                    bots_text += f"... и еще {len(whitelist_bots) - 5} ботов\n\n"
            
            if blacklist_bots:
                bots_text += "🚫 <b>В blacklist:</b>\n"
                for i, bot in enumerate(blacklist_bots[:3], 1):
                    username = bot.username or 'Без username'
                    bots_text += f"{i}. @{username}\n"
                    first_name = getattr(bot, 'first_name', None)
                    if first_name and str(first_name).strip():
                        bots_text += f"   Имя: {first_name}\n"
                    bots_text += f"   ID: <code>{bot.id}</code>\n\n"
                
                if len(blacklist_bots) > 3:
                    bots_text += f"... и еще {len(blacklist_bots) - 3} ботов\n\n"
            
            bots_text += "💡 <b>Команды управления:</b>\n"
            bots_text += "• /add_bot @username - добавить в whitelist\n"
            bots_text += "• /remove_bot @username - удалить из whitelist\n"
            bots_text += "• /help bots - подробная справка"
            
            return bots_text
            
        except Exception as e:
            logger.error(f"Error getting bots list: {sanitize_for_logging(str(e))}")
            return "❌ Ошибка получения списка ботов"

    async def add_bot_to_whitelist(self, bot_username: str, admin_id: int) -> str:
        """Добавить бота в whitelist."""
        try:
            # Очищаем username от @
            clean_username = bot_username.lstrip("@")
            
            # Проверяем, что это валидный username
            if not clean_username or len(clean_username) < 5:
                return "❌ Некорректный username бота"
            
            # Добавляем бота
            result = await self.bot_service.add_bot_to_whitelist(clean_username, admin_id)
            
            if result:
                return f"✅ <b>Бот добавлен в whitelist</b>\n\n🤖 <b>Username:</b> @{clean_username}\n📊 <b>Статус:</b> Разрешен"
            else:
                return f"❌ <b>Ошибка добавления бота</b>\n\n🤖 <b>Username:</b> @{clean_username}\n💡 <b>Возможные причины:</b>\n• Бот уже в whitelist\n• Ошибка базы данных"
                
        except Exception as e:
            logger.error(f"Error adding bot to whitelist: {sanitize_for_logging(str(e))}")
            return f"❌ Ошибка добавления бота @{bot_username}"

    async def remove_bot_from_whitelist(self, bot_username: str, admin_id: int) -> str:
        """Удалить бота из whitelist."""
        try:
            # Очищаем username от @
            clean_username = bot_username.lstrip("@")
            
            # Проверяем, что это валидный username
            if not clean_username or len(clean_username) < 5:
                return "❌ Некорректный username бота"
            
            # Удаляем бота
            result = await self.bot_service.remove_bot_from_whitelist(clean_username, admin_id)
            
            if result:
                return f"✅ <b>Бот удален из whitelist</b>\n\n🤖 <b>Username:</b> @{clean_username}\n📊 <b>Статус:</b> Заблокирован"
            else:
                return f"❌ <b>Ошибка удаления бота</b>\n\n🤖 <b>Username:</b> @{clean_username}\n💡 <b>Возможные причины:</b>\n• Бот не найден в whitelist\n• Ошибка базы данных"
                
        except Exception as e:
            logger.error(f"Error removing bot from whitelist: {sanitize_for_logging(str(e))}")
            return f"❌ Ошибка удаления бота @{bot_username}"
