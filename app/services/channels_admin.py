"""
Channels Admin Service - бизнес-логика для команды /channels
"""

import logging
from typing import Dict, List, Any
from aiogram.types import Message

from app.services.channels import ChannelService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class ChannelsAdminService:
    """Сервис для управления каналами в админке."""
    
    def __init__(self, channel_service: ChannelService):
        self.channel_service = channel_service

    async def get_channels_display(self) -> str:
        """Получить отображение каналов для админки."""
        try:
            channels = await self.channel_service.get_all_channels()
            
            if not channels:
                return "📢 Каналы не найдены"
            
            # Разделяем каналы
            native_channels = []
            foreign_channels = []
            comment_groups = []
            
            for channel in channels:
                if hasattr(channel, "is_comment_group") and bool(channel.is_comment_group):
                    comment_groups.append({
                        "title": channel.title or f"Группа {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "username": channel.username,
                        "member_count": getattr(channel, 'member_count', None),
                    })
                elif hasattr(channel, "is_native") and bool(channel.is_native):
                    native_channels.append({
                        "title": channel.title or f"Канал {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "username": channel.username,
                        "member_count": getattr(channel, 'member_count', None),
                    })
                else:
                    foreign_channels.append({
                        "title": channel.title or f"Канал {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "username": channel.username,
                        "member_count": getattr(channel, 'member_count', None),
                    })

            # Формируем текст
            channels_text = "📢 <b>Управление каналами</b>\n\n"
            
            # Нативные каналы
            if native_channels:
                channels_text += f"✅ <b>Нативные каналы ({len(native_channels)})</b>\n"
                channels_text += "<i>Каналы где бот является администратором</i>\n\n"
                
                for channel in native_channels[:5]:  # Показываем первые 5
                    username = f"@{channel['username']}" if channel.get('username') else "Без username"
                    channels_text += f"<b>{channel.get('title') or 'Без названия'}</b>\n"
                    channels_text += f"   ID: <code>{channel.get('chat_id')}</code> | {username}\n"
                    if channel.get('member_count'):
                        channels_text += f"   👥 Участников: {channel.get('member_count')}\n"
                    channels_text += "\n"
            
            # Foreign каналы
            if foreign_channels:
                channels_text += f"🔍 <b>Foreign каналы ({len(foreign_channels)})</b>\n"
                channels_text += "<i>Каналы откуда приходят сообщения (бот не админ)</i>\n\n"
                
                for channel in foreign_channels[:5]:  # Показываем первые 5
                    username = f"@{channel['username']}" if channel.get('username') else "Без username"
                    channels_text += f"<b>{channel.get('title') or 'Без названия'}</b>\n"
                    channels_text += f"   ID: <code>{channel.get('chat_id')}</code> | {username}\n"
                    if channel.get('member_count'):
                        channels_text += f"   👥 Участников: {channel.get('member_count')}\n"
                    channels_text += "\n"
            
            # Группы комментариев
            if comment_groups:
                channels_text += f"💬 <b>Группы комментариев ({len(comment_groups)})</b>\n"
                channels_text += "<i>Группы для модерации комментариев к постам</i>\n\n"
                
                for group in comment_groups:
                    channels_text += f"<b>{group['title']}</b>\n"
                    channels_text += f"   ID: <code>{group['chat_id']}</code>\n"
                    channels_text += f"   Тип: Группа для комментариев\n"
                    channels_text += f"   Статус: ✅ Антиспам активен\n\n"
            
            # Общая статистика
            channels_text += "📊 <b>Общая статистика:</b>\n"
            channels_text += f"• Нативных каналов: {len(native_channels)}\n"
            channels_text += f"• Иностранных каналов: {len(foreign_channels)}\n"
            channels_text += f"• Групп комментариев: {len(comment_groups)}\n"
            channels_text += f"• Всего чатов: {len(channels) + len(comment_groups)}"
            
            return channels_text
            
        except Exception as e:
            logger.error(f"Error getting channels display: {sanitize_for_logging(str(e))}")
            raise
