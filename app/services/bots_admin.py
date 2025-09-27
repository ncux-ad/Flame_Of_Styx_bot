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

    async def get_bots_display(self) -> str:
        """Получить отображение ботов для админки."""
        try:
            bots = await self.bot_service.get_all_bots()
            
            if not bots:
                return "🤖 Боты не найдены"
            
            # Формируем текст
            bots_text = "🤖 <b>Управление ботами</b>\n\n"
            
            for i, bot in enumerate(bots[:10], 1):  # Показываем первые 10
                bots_text += f"{i}. <b>{bot.username or 'Без username'}</b>\n"
                bots_text += f"   ID: <code>{bot.id}</code>\n"
                if bot.first_name:
                    bots_text += f"   Имя: {bot.first_name}\n"
                bots_text += "\n"
            
            if len(bots) > 10:
                bots_text += f"\n... и еще {len(bots) - 10} ботов"
            
            return bots_text
            
        except Exception as e:
            logger.error(f"Error getting bots display: {sanitize_for_logging(str(e))}")
            raise
