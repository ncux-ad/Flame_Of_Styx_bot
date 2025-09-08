"""Reply keyboards for user interactions."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main user menu keyboard."""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки"))

    builder.adjust(2)
    return builder.as_markup()


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get admin menu keyboard."""
    builder = ReplyKeyboardBuilder()

    builder.add(
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="📋 Каналы"),
        KeyboardButton(text="🤖 Боты"),
        KeyboardButton(text="⚠️ Подозрительные"),
        KeyboardButton(text="⚙️ Настройки"),
    )

    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get cancel keyboard."""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(text="❌ Отмена"))

    return builder.as_markup()
