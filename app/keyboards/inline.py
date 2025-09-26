"""Inline keyboards for admin actions."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_channel_decision_keyboard(channel_id: int, message_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for channel decision."""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="✅ Разрешить", callback_data=f"allow_channel:{channel_id}:{message_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🚫 Заблокировать", callback_data=f"block_channel:{channel_id}:{message_id}"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🗑 Удалить сообщение", callback_data=f"delete_message:{message_id}"
        )
    )

    builder.adjust(2, 1)
    return builder.as_markup()


def get_suspicious_profile_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for suspicious profile decision."""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="🚫 Забанить", callback_data=f"ban_suspicious:{user_id}"))
    builder.add(
        InlineKeyboardButton(text="👀 Наблюдать", callback_data=f"watch_suspicious:{user_id}")
    )
    builder.add(
        InlineKeyboardButton(text="✅ Разрешить", callback_data=f"allow_suspicious:{user_id}")
    )

    builder.adjust(2, 1)
    return builder.as_markup()


def get_moderation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for user moderation."""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="🚫 Забанить", callback_data=f"ban_user:{user_id}"))
    builder.add(InlineKeyboardButton(text="🔇 Замутить", callback_data=f"mute_user:{user_id}"))
    builder.add(InlineKeyboardButton(text="✅ Разбанить", callback_data=f"unban_user:{user_id}"))
    builder.add(InlineKeyboardButton(text="🔊 Размутить", callback_data=f"unmute_user:{user_id}"))

    builder.adjust(2, 2)
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main admin menu keyboard."""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.add(InlineKeyboardButton(text="📋 Список каналов", callback_data="admin_channels"))
    builder.add(InlineKeyboardButton(text="🤖 Список ботов", callback_data="admin_bots"))
    builder.add(InlineKeyboardButton(text="⚠️ Подозрительные", callback_data="admin_suspicious"))

    builder.adjust(2, 2)
    return builder.as_markup()
