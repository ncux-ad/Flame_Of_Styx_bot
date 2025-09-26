"""Link checking service for bot detection."""

import logging
import re
from typing import List, Optional, Tuple

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.auth.authorization import require_admin, safe_user_operation
from app.models.bot import Bot as BotModel
from app.services.moderation import ModerationService
from app.utils.security import safe_format_message, sanitize_for_logging

logger = logging.getLogger(__name__)


class LinkService:
    """Service for checking links and detecting bots."""

    def __init__(self, bot: Bot, db_session: AsyncSession):
        self.bot = bot
        self.db = db_session
        self.moderation_service = ModerationService(bot, db_session)
        
        # Load limits service for configuration
        from app.services.limits import LimitsService
        self.limits_service = LimitsService()

    async def check_message_for_bot_links(self, message: Message) -> List[Tuple[str, bool]]:
        """Check message for bot links and return list of (username, is_bot) tuples."""
        results = []

        # Skip bot link checking for messages from channels (sender_chat)
        if message.sender_chat:
            logger.info(
                f"Skipping bot link check for message from channel: {message.sender_chat.title}"
            )
            return results

        # Check text content
        if message.text:
            text_matches = await self._extract_bot_links_from_text(message.text)
            results.extend(text_matches)

        # Check caption for photos, videos, documents, etc.
        if message.caption:
            caption_matches = await self._extract_bot_links_from_text(message.caption)
            results.extend(caption_matches)

        # Check forwarded message content
        if message.forward_from_chat or message.forward_from:
            # Check if forwarded message contains bot links
            if hasattr(message, "text") and message.text:
                forwarded_matches = await self._extract_bot_links_from_text(message.text)
                results.extend(forwarded_matches)

        # Check reply to message content
        if message.reply_to_message:
            reply_matches = await self.check_message_for_bot_links(message.reply_to_message)
            results.extend(reply_matches)

        # Check for media with potential QR codes or embedded links
        if message.photo or message.video or message.document:
            media_matches = await self._check_media_for_suspicious_content(message)
            results.extend(media_matches)

        return results

    async def _check_media_for_suspicious_content(self, message: Message) -> List[Tuple[str, bool]]:
        """Check media messages for suspicious content like QR codes."""
        results = []

        # Check if media has suspicious captions
        if message.caption:
            caption_lower = message.caption.lower()
            suspicious_keywords = [
                "bot",
                "бот",
                "telegram",
                "телеграм",
                "канал",
                "channel",
                "подписка",
                "subscribe",
                "ссылка",
                "link",
                "qr",
                "код",
            ]

            if any(keyword in caption_lower for keyword in suspicious_keywords):
                logger.warning(f"Suspicious media caption detected: {message.caption}")
                # Flag as potentially containing bot links
                results.append(("suspicious_media", True))

        # Check for forwarded media from suspicious sources
        if message.forward_from_chat:
            if message.forward_from_chat.type in ["channel", "supergroup"]:
                logger.info(
                    f"Media forwarded from {message.forward_from_chat.type}: {message.forward_from_chat.title}"
                )
                # Flag forwarded media as potentially suspicious
                results.append(("forwarded_media", True))

        # Check for media without text but with potential QR codes
        # Only check if enabled in config
        limits = self.limits_service.get_current_limits()
        if (
            limits.get("check_media_without_caption", True)
            and (message.photo or message.video or message.document)
            and not message.caption
            and not message.text
        ):
            # Check if it's a document (potential QR code)
            if message.document:
                # Check document size and type for suspicious patterns
                if await self._is_document_suspicious(message.document):
                    logger.info("Suspicious document without caption detected - potential QR code")
                    results.append(("document_without_caption", True))
                else:
                    logger.info("Document without caption detected - allowing (normal document)")
            else:
                # For photos and videos, check configuration settings
                if message.video:
                    if limits.get("allow_videos_without_caption", True):
                        logger.info("Video without caption detected - allowing (config enabled)")
                    else:
                        logger.info("Video without caption detected - flagging (config disabled)")
                        results.append(("video_without_caption", True))
                elif message.photo:
                    if limits.get("allow_photos_without_caption", True):
                        logger.info("Photo without caption detected - allowing (config enabled)")
                    else:
                        logger.info("Photo without caption detected - flagging (config disabled)")
                        results.append(("photo_without_caption", True))
                else:
                    logger.info("Media without caption detected - allowing (likely normal content)")

        return results

    async def _is_document_suspicious(self, document) -> bool:
        """Check if document is suspicious (potential QR code)."""
        try:
            limits = self.limits_service.get_current_limits()
            max_size = limits.get("max_document_size_suspicious", 50000)
            
            # Check file size - very small files might be QR codes
            if document.file_size and document.file_size < max_size:
                logger.info(f"Small document detected: {document.file_size} bytes (threshold: {max_size})")
                return True
            
            # Check MIME type for suspicious patterns
            if document.mime_type:
                suspicious_types = [
                    "image/png",
                    "image/jpeg", 
                    "image/jpg",
                    "application/pdf"
                ]
                if document.mime_type in suspicious_types and document.file_size and document.file_size < 100000:  # Less than 100KB
                    logger.info(f"Suspicious document type: {document.mime_type}, size: {document.file_size}")
                    return True
            
            # Check file name for suspicious patterns
            if document.file_name:
                file_name_lower = document.file_name.lower()
                suspicious_patterns = [
                    "qr", "код", "code", "scan", "сканировать",
                    "bot", "бот", "telegram", "телеграм"
                ]
                if any(pattern in file_name_lower for pattern in suspicious_patterns):
                    logger.info(f"Suspicious document name: {document.file_name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking document suspiciousness: {e}")
            return False

    async def _extract_bot_links_from_text(self, text: str) -> List[Tuple[str, bool]]:
        """Extract bot links from text content."""
        if not text:
            return []

        results = []

        # Find all t.me/username patterns
        t_me_pattern = r"t\.me/([a-zA-Z0-9_]+)"
        t_me_matches = re.findall(t_me_pattern, text, re.IGNORECASE)

        # Find all @username mentions
        mention_pattern = r"@([a-zA-Z0-9_]+)"
        mention_matches = re.findall(mention_pattern, text, re.IGNORECASE)

        # Find telegram.me links (alternative format)
        telegram_me_pattern = r"telegram\.me/([a-zA-Z0-9_]+)"
        telegram_me_matches = re.findall(telegram_me_pattern, text, re.IGNORECASE)

        # Process t.me links
        for username in t_me_matches:
            is_bot = await self._check_if_username_is_bot(username)
            results.append(("bot_link", is_bot))

        # Process @username mentions
        for username in mention_matches:
            is_bot = await self._check_if_username_is_bot(username)
            results.append(("username_mention", is_bot))

        # Process telegram.me links
        for username in telegram_me_matches:
            is_bot = await self._check_if_username_is_bot(username)
            results.append(("bot_link", is_bot))

        return results

    async def _check_if_username_is_bot(self, username: str) -> bool:
        """Check if username belongs to a bot - simple pattern matching."""
        try:
            # First check if it's in our whitelist
            if await self._is_bot_whitelisted(username):
                return False  # Whitelisted bots are allowed

            # Simple pattern: if username contains 'bot' anywhere, it's a bot
            if "bot" in username.lower():
                logger.info(f"Bot detected by pattern: @{username}")
                return True

            return False

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error checking if {username} is bot: {error}",
                    username=sanitize_for_logging(username),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    async def _is_bot_whitelisted(self, username: str) -> bool:
        """Check if bot is in whitelist."""
        result = await self.db.execute(
            select(BotModel.is_whitelisted).where(BotModel.username == username)
        )
        is_whitelisted = result.scalar_one_or_none()
        return is_whitelisted is True

    async def handle_bot_link_detection(
        self, message: Message, bot_links: List[Tuple[str, bool]]
    ) -> bool:
        """Handle detection of bot links in message."""
        if not bot_links:
            return False

        # Check if any of the links are to non-whitelisted bots
        non_whitelisted_bots = [username for username, is_bot in bot_links if is_bot]

        # Check for suspicious media content
        suspicious_media = [
            link_type
            for link_type, is_suspicious in bot_links
            if link_type in ["suspicious_media", "forwarded_media", "document_without_caption", "video_without_caption", "photo_without_caption"]
            and is_suspicious
        ]

        # Take action if there are bot links or suspicious media
        if non_whitelisted_bots or suspicious_media:
            # Delete message and ban user
            await self.moderation_service.delete_message(
                chat_id=message.chat.id, message_id=message.message_id, admin_id=0  # System action
            )

            if message.from_user:
                # Create detailed reason
                reason_parts = []
                if non_whitelisted_bots:
                    reason_parts.append(f"Posted bot links: {', '.join(non_whitelisted_bots)}")
                if suspicious_media:
                    reason_parts.append(f"Suspicious media: {', '.join(suspicious_media)}")

                reason = "; ".join(reason_parts)

                await self.moderation_service.ban_user(
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    admin_id=0,  # System action
                    reason=reason,
                )

            logger.info(
                safe_format_message(
                    "Deleted message with bot links: {bots}, suspicious media: {media}",
                    bots=sanitize_for_logging(non_whitelisted_bots),
                    media=sanitize_for_logging(suspicious_media),
                )
            )
            return True

        return False

    async def add_bot_to_whitelist(
        self, username: str, admin_id: int, telegram_id: Optional[int] = None
    ) -> bool:
        """Add bot to whitelist."""
        try:
            # Check if bot already exists
            result = await self.db.execute(select(BotModel).where(BotModel.username == username))
            existing_bot = result.scalar_one_or_none()

            if existing_bot:
                # Update existing bot
                existing_bot.is_whitelisted = True
                existing_bot.telegram_id = telegram_id or existing_bot.telegram_id
            else:
                # Create new bot entry
                new_bot = BotModel(
                    username=username, telegram_id=telegram_id or 0, is_whitelisted=True
                )
                self.db.add(new_bot)

            await self.db.commit()
            logger.info(
                safe_format_message(
                    "Bot {username} added to whitelist by admin {admin_id}",
                    username=sanitize_for_logging(username),
                    admin_id=sanitize_for_logging(admin_id),
                )
            )
            return True

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error adding bot {username} to whitelist: {error}",
                    username=sanitize_for_logging(username),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    async def remove_bot_from_whitelist(self, username: str, admin_id: int) -> bool:
        """Remove bot from whitelist."""
        try:
            result = await self.db.execute(select(BotModel).where(BotModel.username == username))
            bot = result.scalar_one_or_none()

            if bot:
                bot.is_whitelisted = False
                await self.db.commit()
                logger.info(
                    safe_format_message(
                        "Bot {username} removed from whitelist by admin {admin_id}",
                        username=sanitize_for_logging(username),
                        admin_id=sanitize_for_logging(admin_id),
                    )
                )
                return True
            else:
                logger.warning(
                    safe_format_message(
                        "Bot {username} not found in whitelist",
                        username=sanitize_for_logging(username),
                    )
                )
                return False

        except Exception as e:
            logger.error(
                safe_format_message(
                    "Error removing bot {username} from whitelist: {error}",
                    username=sanitize_for_logging(username),
                    error=sanitize_for_logging(e),
                )
            )
            return False

    async def get_whitelisted_bots(self) -> List[BotModel]:
        """Get list of whitelisted bots."""
        result = await self.db.execute(select(BotModel).where(BotModel.is_whitelisted))
        return result.scalars().all()
