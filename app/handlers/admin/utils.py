"""
Вспомогательные функции для админских хендлеров
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def format_user_display(user_info: Dict[str, Any], user_id: int) -> str:
    """Форматирует отображение пользователя."""
    if user_info.get("username"):
        return f"@{user_info.get('username')}"
    else:
        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        return full_name if full_name else f"User {user_id}"


def format_chat_display(chat_info: Dict[str, Any]) -> str:
    """Форматирует отображение чата."""
    if chat_info.get("username"):
        return f"@{chat_info.get('username')}"
    else:
        return chat_info.get("title", "Unknown Chat")


def escape_html(text: str) -> str:
    """Экранирует HTML символы."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_suspicion_status(score: float) -> str:
    """Возвращает статус подозрительности по счету."""
    if score >= 0.7:
        return "🔴 Высокий риск"
    elif score >= 0.4:
        return "🟡 Средний риск"
    else:
        return "🟢 Низкий риск"


def format_date(date_obj) -> str:
    """Форматирует дату для отображения."""
    try:
        if date_obj and hasattr(date_obj, "strftime"):
            return date_obj.strftime("%d.%m.%Y %H:%M")
        else:
            return "Неизвестно"
    except Exception:
        return "Неизвестно"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Обрезает текст до указанной длины."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
