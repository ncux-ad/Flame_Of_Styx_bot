"""Profile analysis service for detecting GPT-bots."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiogram import Bot
from aiogram.types import Chat, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.auth.authorization import require_admin, safe_user_operation
# from app.models.moderation_log import ModerationAction, ModerationLog
from app.models.suspicious_profile import SuspiciousProfile
from app.services.moderation import ModerationService
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for analyzing user profiles and detecting GPT-bots."""

    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session
        self.moderation_service = ModerationService(bot, db_session)

    async def get_user_info(self, user_id: int) -> dict:
        """Get user information from Telegram API."""
        try:
            # Пробуем получить информацию о пользователе через get_chat
            try:
                user = await self.bot.get_chat(user_id)
                return {
                    "id": user.id,
                    "username": getattr(user, "username", None),
                    "first_name": getattr(user, "first_name", None),
                    "last_name": getattr(user, "last_name", None),
                    "is_bot": getattr(user, "is_bot", False),
                }
            except Exception:
                # Если get_chat не работает, возвращаем базовую информацию
                return {
                    "id": user_id,
                    "username": None,
                    "first_name": f"User {user_id}",
                    "last_name": None,
                    "is_bot": False,
                }
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
            return {
                "id": user_id,
                "username": None,
                "first_name": f"User {user_id}",
                "last_name": None,
                "is_bot": False,
            }

    async def analyze_user_profile(self, user: User, admin_id: int) -> Optional[SuspiciousProfile]:
        """Analyze user profile for suspicious patterns."""
        try:
            # Check if user already has suspicious profile
            existing_profile = await self._get_suspicious_profile(user.id)

            # Analyze profile
            analysis_result = await self._perform_profile_analysis(user)

            if analysis_result["is_suspicious"]:
                if existing_profile:
                    # Update existing profile
                    existing_profile.suspicion_score = analysis_result["suspicion_score"]
                    existing_profile.detected_patterns = ",".join(analysis_result["patterns"])
                    existing_profile.is_suspicious = analysis_result["is_suspicious"]
                    existing_profile.analysis_reason = (
                        f"Suspicion score: {analysis_result['suspicion_score']:.2f}"
                    )
                    existing_profile.updated_at = datetime.utcnow()

                    await self.db.commit()
                    await self.db.refresh(existing_profile)

                    # Only notify admin if profile is not reviewed yet
                    if not existing_profile.is_reviewed:
                        await self._notify_admin_about_suspicious_profile(
                            admin_id=admin_id, user=user, profile=existing_profile
                        )

                    return existing_profile
                else:
                    # Create new suspicious profile
                    profile = await self._create_suspicious_profile(
                        user_id=user.id, analysis_result=analysis_result
                    )

                    # Notify admin
                    await self._notify_admin_about_suspicious_profile(
                        admin_id=admin_id, user=user, profile=profile
                    )

                    return profile
            else:
                # If not suspicious and profile exists, mark as not suspicious
                if existing_profile and existing_profile.is_suspicious:
                    existing_profile.is_suspicious = False
                    existing_profile.updated_at = datetime.utcnow()
                    await self.db.commit()

            return None

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error analyzing profile for user {user_id}: {error}",
                    user_id=sanitize_for_logging(user.id),
                    error=sanitize_for_logging(e),
                )
            )
            return None

    async def _perform_profile_analysis(self, user: User) -> Dict[str, Any]:
        """Perform detailed profile analysis."""
        analysis = {
            "is_suspicious": False,
            "suspicion_score": 0.0,
            "patterns": [],
            "linked_chat": None,
            "post_count": 0,
            "has_bait_channel": False,
        }

        try:
            # Check if user has linked chat - this is NOT available in Telegram Bot API
            # linked_chat is only available for chats, not users
            logger.info(
                f"Checking for linked_chat - this is not available for users in Telegram Bot API"
            )

            # Note: linked_chat information is not available for users in Telegram Bot API
            # It's only available for chats via getChat() method
            # We'll skip this check as it's not possible to get user's linked chat via Bot API
            logger.info(f"Linked chat detection skipped - not available for users in Bot API")

            # Check for suspicious patterns
            patterns = await self._detect_suspicious_patterns(user)
            analysis["patterns"] = patterns

            # Calculate suspicion score
            analysis["suspicion_score"] = self._calculate_suspicion_score(analysis)
            analysis["is_suspicious"] = analysis["suspicion_score"] > 0.2
            logger.info(
                f"Analysis result for user {user.id}: score={analysis['suspicion_score']:.2f}, patterns={analysis['patterns']}, is_suspicious={analysis['is_suspicious']}"
            )

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error in profile analysis: {error}", error=sanitize_for_logging(e)
                )
            )

        return analysis

    async def _analyze_linked_chat(self, chat: Chat) -> Dict[str, Any]:
        """Analyze linked chat for suspicious patterns."""
        analysis = {"post_count": 0, "has_bait_channel": False, "is_public": True}

        try:
            # Try to get chat info
            chat_info = await self.bot.get_chat(chat.id)
            analysis["is_public"] = chat_info.type in ["channel", "supergroup"]

            # Try to get chat member count
            try:
                member_count = await self.bot.get_chat_member_count(chat.id)
                analysis["member_count"] = member_count
            except Exception:
                analysis["member_count"] = 0

            # Check if it's a bait channel (low post count, public)
            if analysis["is_public"] and analysis["member_count"] < 100:
                analysis["has_bait_channel"] = True
                analysis["post_count"] = 0  # We can't easily get post count

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error analyzing linked chat {chat_id}: {error}",
                    chat_id=sanitize_for_logging(chat.id),
                    error=sanitize_for_logging(e),
                )
            )

        return analysis

    async def _detect_suspicious_patterns(self, user: User) -> list:
        """Detect suspicious patterns in user profile."""
        patterns = []

        # Check for common GPT-bot patterns
        if user.first_name and len(user.first_name) < 3:
            patterns.append("short_first_name")

        if user.last_name and len(user.last_name) < 3:
            patterns.append("short_last_name")

        # More sensitive pattern: no username (common for bots)
        if not user.username:
            patterns.append("no_username")

        # More sensitive pattern: no last name (common for bots)
        if not user.last_name:
            patterns.append("no_last_name")

        # Check for suspicious username patterns
        if user.username:
            username = user.username.lower()
            if any(pattern in username for pattern in ["bot", "gpt", "ai", "assistant"]):
                patterns.append("bot_like_username")

        # Check for suspicious first name patterns
        if user.first_name:
            first_name = user.first_name.lower()
            if any(pattern in first_name for pattern in ["bot", "gpt", "ai", "test", "user"]):
                patterns.append("bot_like_first_name")

        return patterns

    def _calculate_suspicion_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate suspicion score based on analysis."""
        score = 0.0

        # Linked chat analysis
        if analysis["linked_chat"]:
            score += 0.2  # Снижено с 0.3

            if analysis["has_bait_channel"]:
                score += 0.3  # Снижено с 0.4

            if analysis["post_count"] == 0:
                score += 0.1  # Снижено с 0.2

        # Pattern analysis - balanced weights for better accuracy
        pattern_weights = {
            "short_first_name": 0.1,      # Снижено с 0.2
            "short_last_name": 0.1,       # Снижено с 0.2
            "no_identifying_info": 0.2,   # Снижено с 0.4
            "bot_like_username": 0.15,    # Снижено с 0.3
            "no_username": 0.1,           # Снижено с 0.25
            "no_last_name": 0.1,          # Снижено с 0.2
            "bot_like_first_name": 0.2,   # Снижено с 0.35
        }

        for pattern in analysis["patterns"]:
            score += pattern_weights.get(pattern, 0.0)

        return min(score, 1.0)

    async def _get_suspicious_profile(self, user_id: int) -> Optional[SuspiciousProfile]:
        """Get existing suspicious profile for user."""
        result = await self.db.execute(
            select(SuspiciousProfile).where(SuspiciousProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _create_suspicious_profile(
        self, user_id: int, analysis_result: Dict[str, Any]
    ) -> SuspiciousProfile:
        """Create suspicious profile entry."""
        profile = SuspiciousProfile(
            user_id=user_id,
            linked_chat_id=(
                analysis_result["linked_chat"]["id"] if analysis_result["linked_chat"] else None
            ),
            linked_chat_username=(
                analysis_result["linked_chat"]["username"]
                if analysis_result["linked_chat"]
                else None
            ),
            linked_chat_title=(
                analysis_result["linked_chat"]["title"] if analysis_result["linked_chat"] else None
            ),
            post_count=analysis_result["post_count"],
            has_bait_channel=analysis_result["has_bait_channel"],
            suspicion_score=analysis_result["suspicion_score"],
            detected_patterns=",".join(analysis_result["patterns"]),
            analysis_reason=f"Suspicion score: {analysis_result['suspicion_score']:.2f}",
        )

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)

        return profile

    async def _notify_admin_about_suspicious_profile(
        self, admin_id: int, user: User, profile: SuspiciousProfile
    ) -> None:
        """Notify admin about suspicious profile."""
        try:
            from app.keyboards.inline import get_suspicious_profile_keyboard

            message = "⚠️ <b>Подозрительный профиль обнаружен</b>\n\n"
            message += f"<b>Пользователь:</b> {user.first_name or 'Unknown'}\n"
            if user.username:
                message += f"<b>Username:</b> @{user.username}\n"
            message += f"<b>ID:</b> {user.id}\n"
            message += f"<b>Счет подозрительности:</b> {profile.suspicion_score:.2f}\n"

            if profile.linked_chat_title:
                message += f"<b>Связанный канал:</b> {profile.linked_chat_title}\n"
                if profile.linked_chat_username:
                    message += f"<b>Username канала:</b> @{profile.linked_chat_username}\n"

            if profile.detected_patterns:
                patterns = profile.detected_patterns.split(",") if profile.detected_patterns else []
                pattern_names = {
                    "short_first_name": "Короткое имя",
                    "short_last_name": "Короткая фамилия",
                    "no_identifying_info": "Нет идентификаторов",
                    "bot_like_username": "Bot-подобный username",
                    "no_username": "Нет username",
                    "no_last_name": "Нет фамилии",
                    "bot_like_first_name": "Bot-подобное имя",
                }
                pattern_text = ", ".join([pattern_names.get(p, p) for p in patterns])
                message += f"<b>Обнаруженные паттерны:</b> {pattern_text}\n"

            # Создаем клавиатуру для модерации
            keyboard = get_suspicious_profile_keyboard(user.id)

            await self.bot.send_message(chat_id=admin_id, text=message, reply_markup=keyboard)

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error notifying admin about suspicious profile: {error}",
                    error=sanitize_for_logging(e),
                )
            )

    async def mark_profile_as_reviewed(
        self, user_id: int, admin_id: int, is_confirmed: bool, notes: Optional[str] = None
    ) -> bool:
        """Mark suspicious profile as reviewed."""
        try:
            profile = await self._get_suspicious_profile(user_id)
            if not profile:
                return False

            profile.is_reviewed = True
            profile.is_confirmed_suspicious = is_confirmed
            profile.reviewed_by = admin_id
            profile.review_notes = notes

            await self.db.commit()

            logger.info(
                safe_format_message(
                    "Profile {user_id} marked as reviewed by admin {admin_id}",
                    user_id=sanitize_for_logging(user_id),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error marking profile as reviewed: {error}", error=sanitize_for_logging(e)
                )
            )
            return False

    async def get_suspicious_profiles(self, limit: int = 50) -> List[SuspiciousProfile]:
        """Get list of suspicious profiles."""
        try:
            result = await self.db.execute(
                select(SuspiciousProfile).order_by(SuspiciousProfile.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error getting suspicious profiles: {error}", error=sanitize_for_logging(e)
                )
            )
            return []

    async def reset_suspicious_profiles(self) -> int:
        """Reset all suspicious profiles to unreviewed status."""
        try:
            from sqlalchemy import update

            result = await self.db.execute(
                update(SuspiciousProfile)
                .where(SuspiciousProfile.is_reviewed == True)
                .values(is_reviewed=False, is_confirmed_suspicious=False)
            )
            await self.db.commit()
            return result.rowcount
        except Exception as e:
            logger.error(f"Error resetting suspicious profiles: {e}")
            await self.db.rollback()
            return 0
