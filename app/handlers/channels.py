"""Channel message handlers."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.services.channels import ChannelService
from app.services.moderation import ModerationService
from app.keyboards.inline import get_channel_decision_keyboard
from app.filters.is_admin import IsAdminFilter

logger = logging.getLogger(__name__)

# Create router
channel_router = Router()


@channel_router.message(F.sender_chat)
async def handle_channel_message(message: Message) -> None:
    """Handle messages from channels (sender_chat)."""
    try:
        if not message.sender_chat:
            return
        
        # TODO: Implement channel message handling
        # This will be implemented when services are properly integrated
        logger.info(f"Channel message from {message.sender_chat.title}")
        
    except Exception as e:
        logger.error(f"Error handling channel message: {e}")


@channel_router.callback_query(F.data.startswith("allow_channel:"))
async def handle_allow_channel_callback(callback: CallbackQuery) -> None:
    """Handle allow channel callback."""
    try:
        if not callback.data:
            return
        
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) != 3:
            return
        
        channel_id = int(parts[1])
        message_id = int(parts[2])
        
        # TODO: Implement channel allowing
        await callback.answer("✅ Канал разрешен")
        await callback.message.edit_text(
            f"✅ Канал {channel_id} добавлен в whitelist"
        )
        
    except Exception as e:
        logger.error(f"Error handling allow channel callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@channel_router.callback_query(F.data.startswith("block_channel:"))
async def handle_block_channel_callback(
    callback: CallbackQuery,
    channel_service: ChannelService
) -> None:
    """Handle block channel callback."""
    try:
        if not callback.data:
            return
        
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) != 3:
            return
        
        channel_id = int(parts[1])
        message_id = int(parts[2])
        
        # Block channel
        success = await channel_service.block_channel(
            channel_id=channel_id,
            admin_id=callback.from_user.id if callback.from_user else 0
        )
        
        if success:
            await callback.answer("🚫 Канал заблокирован")
            await callback.message.edit_text(
                f"🚫 Канал {channel_id} добавлен в blacklist"
            )
        else:
            await callback.answer("❌ Ошибка при блокировке канала")
        
    except Exception as e:
        logger.error(f"Error handling block channel callback: {e}")
        await callback.answer("❌ Произошла ошибка")


@channel_router.callback_query(F.data.startswith("delete_message:"))
async def handle_delete_message_callback(
    callback: CallbackQuery,
    moderation_service: ModerationService
) -> None:
    """Handle delete message callback."""
    try:
        if not callback.data:
            return
        
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) != 2:
            return
        
        message_id = int(parts[1])
        
        # Delete message
        success = await moderation_service.delete_message(
            chat_id=callback.message.chat.id if callback.message else 0,
            message_id=message_id,
            admin_id=callback.from_user.id if callback.from_user else 0
        )
        
        if success:
            await callback.answer("🗑 Сообщение удалено")
            await callback.message.edit_text("🗑 Сообщение удалено")
        else:
            await callback.answer("❌ Ошибка при удалении сообщения")
        
    except Exception as e:
        logger.error(f"Error handling delete message callback: {e}")
        await callback.answer("❌ Произошла ошибка")
