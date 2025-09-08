"""User message handlers."""

import logging
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, LEFT, MEMBER

from app.services.links import LinkService
from app.services.profiles import ProfileService
from app.services.moderation import ModerationService

logger = logging.getLogger(__name__)

# Create router
user_router = Router()


@user_router.message()
async def handle_user_message(message: Message) -> None:
    """Handle user messages."""
    try:
        # Skip if message is from bot
        if message.from_user and message.from_user.is_bot:
            return
        
        # TODO: Implement link checking and profile analysis
        # This will be implemented when services are properly integrated
        pass
        
    except Exception as e:
        logger.error(f"Error handling user message: {e}")


@user_router.my_chat_member()
async def handle_new_member(update: ChatMemberUpdated) -> None:
    """Handle new chat member."""
    try:
        # Check if user was added to chat
        if update.new_chat_member.status in [MEMBER, KICKED, LEFT]:
            user = update.new_chat_member.user
            
            # Skip if it's a bot and not whitelisted
            if user.is_bot:
                # TODO: Implement bot banning
                # This will be implemented when services are properly integrated
                logger.info(f"Bot {user.username} joined chat {update.chat.id}")
        
    except Exception as e:
        logger.error(f"Error handling new member: {e}")


@user_router.chat_member()
async def handle_chat_member_update(update: ChatMemberUpdated) -> None:
    """Handle chat member updates."""
    try:
        # Check if user was banned or left
        if update.new_chat_member.status in [KICKED, LEFT]:
            user = update.new_chat_member.user
            
            # Log the event
            logger.info(f"User {user.username} {update.new_chat_member.status} from chat {update.chat.id}")
        
    except Exception as e:
        logger.error(f"Error handling chat member update: {e}")
