"""Security utilities for safe logging and data handling."""

import hashlib
import html
import re
from typing import Any, Union


def hash_user_id(user_id: Union[int, str, None]) -> str:
    """Hash user ID for safe logging.

    Args:
        user_id: User ID to hash

    Returns:
        Hashed user ID (first 10 characters of SHA256)
    """
    if user_id is None:
        return "None"

    # Convert to string and hash
    user_str = str(user_id)
    hashed = hashlib.sha256(user_str.encode()).hexdigest()
    return hashed[:10]


def sanitize_for_logging(data: Any) -> str:
    """Sanitize data for safe logging to prevent log injection attacks.

    Args:
        data: Data to sanitize

    Returns:
        Sanitized string safe for logging
    """
    if data is None:
        return "None"

    # Convert to string
    data_str = str(data)

    # Remove or escape dangerous characters
    # Remove newlines and carriage returns
    data_str = data_str.replace("\n", "\\n").replace("\r", "\\r")

    # Remove control characters (except tab)
    data_str = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", data_str)

    # HTML escape to prevent XSS in log viewers
    data_str = html.escape(data_str, quote=False)

    # Limit length to prevent log flooding
    if len(data_str) > 1000:
        data_str = data_str[:1000] + "...[TRUNCATED]"

    return data_str


def sanitize_user_input(data: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks.

    Args:
        data: User input string

    Returns:
        Sanitized string safe for processing
    """
    if not data:
        return ""

    # HTML escape
    data = html.escape(data, quote=False)

    # Remove potentially dangerous characters
    data = re.sub(r'[<>"\']', "", data)

    # Limit length
    if len(data) > 500:
        data = data[:500]

    return data.strip()


def validate_user_id(user_id: Any) -> bool:
    """Validate that user_id is a valid integer.

    Args:
        user_id: User ID to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        if isinstance(user_id, int):
            return user_id > 0
        elif isinstance(user_id, str):
            return user_id.isdigit() and int(user_id) > 0
        return False
    except (ValueError, TypeError):
        return False


def validate_username(username: str) -> bool:
    """Validate username format.

    Args:
        username: Username to validate

    Returns:
        True if valid, False otherwise
    """
    if not username:
        return False

    # Telegram username format: 5-32 characters, alphanumeric and underscores
    return bool(re.match(r"^[a-zA-Z0-9_]{5,32}$", username))


def safe_format_message(message: str, **kwargs: Any) -> str:
    """Safely format message with user data.

    Args:
        message: Message template
        **kwargs: Data to insert

    Returns:
        Safely formatted message
    """
    # Sanitize all values
    safe_kwargs = {k: sanitize_for_logging(v) for k, v in kwargs.items()}

    try:
        return message.format(**safe_kwargs)
    except (KeyError, ValueError, TypeError):
        # Fallback to safe string representation
        return f"{message} - Data: {sanitize_for_logging(kwargs)}"
