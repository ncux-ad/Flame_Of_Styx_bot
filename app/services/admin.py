"""
Admin Service - бизнес-логика для админских команд
"""

import logging
from typing import Dict, List, Optional, Any
from aiogram.types import Message, CallbackQuery, User

from app.services.bots import BotService
from app.services.channels import ChannelService
from app.services.help import HelpService
from app.services.limits import LimitsService
from app.services.moderation import ModerationService
from app.services.profiles import ProfileService
from app.utils.security import sanitize_for_logging

logger = logging.getLogger(__name__)


class AdminService:
    """Сервис для админских команд и операций."""
    
    def __init__(
        self,
        moderation_service: ModerationService,
        bot_service: BotService,
        channel_service: ChannelService,
        profile_service: ProfileService,
        help_service: HelpService,
        limits_service: LimitsService,
    ):
        self.moderation_service = moderation_service
        self.bot_service = bot_service
        self.channel_service = channel_service
        self.profile_service = profile_service
        self.help_service = help_service
        self.limits_service = limits_service

    async def get_welcome_message(self) -> str:
        """Получить приветственное сообщение для админа."""
        return (
            "🤖 <b>AntiSpam Bot - Упрощенная версия</b>\n\n"
            "Доступные команды:\n"
            "/status - статистика бота\n"
            "/channels - управление каналами\n"
            "/sync_channels - синхронизировать статус каналов\n"
            "/bots - управление ботами\n"
            "/suspicious - подозрительные профили\n"
            "/unban - разблокировать пользователя\n"
            "/banned - список заблокированных\n"
            "/sync_bans - синхронизировать баны с Telegram\n"
            "/force_unban - принудительный разбан по ID/username\n"
            "/help - помощь"
        )

    async def get_status_info(self, admin_id: int) -> Dict[str, Any]:
        """Получить информацию о статусе бота."""
        try:
            # Получаем статистику модерации
            banned_users = await self.moderation_service.get_banned_users(limit=100)
            spam_stats = await self.moderation_service.get_spam_statistics()
            deleted_messages = spam_stats.get("deleted_messages", 0)
            total_actions = spam_stats.get("total_actions", 0)

            # Получаем каналы
            all_channels = await self.channel_service.get_all_channels()
            
            # Разделяем на нативные и Foreign
            native_channels = []
            foreign_channels = []
            comment_groups = []
            
            for channel in all_channels:
                if hasattr(channel, "is_comment_group") and bool(channel.is_comment_group):
                    comment_groups.append({
                        "title": channel.title or f"Группа {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "type": "Группа для комментариев",
                    })
                elif hasattr(channel, "is_native") and bool(channel.is_native):
                    native_channels.append({
                        "title": channel.title or f"Канал {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "type": "Канал",
                    })
                else:
                    foreign_channels.append({
                        "title": channel.title or f"Канал {channel.telegram_id}",
                        "chat_id": str(channel.telegram_id),
                        "type": "Иностранный канал",
                    })

            return {
                "bot_id": "7977609078",
                "bot_username": "@FlameOfStyx_bot",
                "banned_users_count": len(banned_users),
                "deleted_messages": deleted_messages,
                "total_actions": total_actions,
                "native_channels": native_channels,
                "foreign_channels": foreign_channels,
                "comment_groups": comment_groups,
                "admin_id": admin_id,
            }
        except Exception as e:
            logger.error(f"Error getting status info: {sanitize_for_logging(str(e))}")
            raise

    async def get_channels_info(self) -> Dict[str, Any]:
        """Получить информацию о каналах."""
        try:
            channels = await self.channel_service.get_all_channels()
            
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

            return {
                "native_channels": native_channels,
                "foreign_channels": foreign_channels,
                "comment_groups": comment_groups,
                "total_channels": len(channels),
            }
        except Exception as e:
            logger.error(f"Error getting channels info: {sanitize_for_logging(str(e))}")
            raise

    async def get_bots_info(self) -> Dict[str, Any]:
        """Получить информацию о ботах."""
        try:
            bots = await self.bot_service.get_all_bots()
            return {
                "bots": bots,
                "total_bots": len(bots),
            }
        except Exception as e:
            logger.error(f"Error getting bots info: {sanitize_for_logging(str(e))}")
            raise

    async def analyze_user_profile(self, user_id: int, admin_id: int) -> Dict[str, Any]:
        """Анализировать профиль пользователя."""
        try:
            # Получаем информацию о пользователе
            user_info = await self.profile_service.get_user_info(user_id)
            
            # Создаем объект User для анализа
            from aiogram.types import User
            user = User(
                id=user_info['id'],
                is_bot=user_info['is_bot'],
                first_name=user_info['first_name'],
                last_name=user_info['last_name'],
                username=user_info['username']
            )
            
            # Анализируем профиль
            profile = await self.profile_service.analyze_user_profile(user, admin_id)
            
            return {
                "user_info": user_info,
                "profile": profile,
                "user_id": user_id,
            }
        except Exception as e:
            logger.error(f"Error analyzing user profile: {sanitize_for_logging(str(e))}")
            raise

    async def handle_ban_suspicious_user(
        self, 
        user_id: int, 
        chat_id: int, 
        admin_id: int,
        suspicion_score: float
    ) -> Dict[str, Any]:
        """Забанить подозрительного пользователя."""
        try:
            # Получаем информацию о пользователе
            user_info = await self.profile_service.get_user_info(user_id)
            
            # Баним пользователя
            success = await self.moderation_service.ban_user(
                user_id=user_id,
                chat_id=chat_id,
                reason=f"Подозрительный профиль (счет: {suspicion_score:.2f})",
                admin_id=admin_id,
            )
            
            if success:
                # Отмечаем профиль как проверенный и подтвержденный
                await self.profile_service.mark_profile_as_reviewed(
                    user_id=user_id,
                    admin_id=admin_id,
                    is_confirmed=True,
                    notes="Забанен за подозрительный профиль",
                )
            
            return {
                "success": success,
                "user_info": user_info,
                "user_id": user_id,
            }
        except Exception as e:
            logger.error(f"Error banning suspicious user: {sanitize_for_logging(str(e))}")
            raise

    async def handle_watch_suspicious_user(
        self, 
        user_id: int, 
        admin_id: int
    ) -> Dict[str, Any]:
        """Добавить подозрительного пользователя в наблюдение."""
        try:
            # Отмечаем профиль как проверенный, но не подтвержденный
            await self.profile_service.mark_profile_as_reviewed(
                user_id=user_id,
                admin_id=admin_id,
                is_confirmed=False,
                notes="Добавлен в наблюдение",
            )
            
            return {
                "success": True,
                "user_id": user_id,
            }
        except Exception as e:
            logger.error(f"Error watching suspicious user: {sanitize_for_logging(str(e))}")
            raise

    async def handle_allow_suspicious_user(
        self, 
        user_id: int, 
        admin_id: int
    ) -> Dict[str, Any]:
        """Разрешить подозрительного пользователя (ложное срабатывание)."""
        try:
            # Отмечаем профиль как проверенный и ложное срабатывание
            await self.profile_service.mark_profile_as_reviewed(
                user_id=user_id,
                admin_id=admin_id,
                is_confirmed=False,
                notes="Ложное срабатывание - разрешен",
            )
            
            return {
                "success": True,
                "user_id": user_id,
            }
        except Exception as e:
            logger.error(f"Error allowing suspicious user: {sanitize_for_logging(str(e))}")
            raise
