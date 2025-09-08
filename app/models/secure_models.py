"""Secure models with XSS protection and input validation."""

import re
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.utils.security import sanitize_user_input, validate_user_id, validate_username


class SecureUser(BaseModel):
    """Secure user model with XSS protection."""

    id: int = Field(..., gt=0, description="User ID must be positive")
    username: Optional[str] = Field(None, max_length=32)
    first_name: Optional[str] = Field(None, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    is_bot: bool = False
    is_premium: bool = False

    @validator("id")
    def validate_user_id(cls, v):
        if not validate_user_id(v):
            raise ValueError("Invalid user ID")
        return v

    @validator("username")
    def validate_username(cls, v):
        if v and not validate_username(v):
            raise ValueError("Invalid username format")
        return v

    @validator("first_name", "last_name")
    def sanitize_names(cls, v):
        if v:
            return sanitize_user_input(v)
        return v


class SecureMessage(BaseModel):
    """Secure message model with XSS protection."""

    message_id: int = Field(..., gt=0)
    text: Optional[str] = Field(None, max_length=4096)
    from_user: Optional[SecureUser] = None
    chat_id: int = Field(..., description="Chat ID")
    date: int = Field(..., description="Message timestamp")

    @validator("text")
    def sanitize_text(cls, v):
        if v:
            return sanitize_user_input(v)
        return v

    @validator("chat_id")
    def validate_chat_id(cls, v):
        if not isinstance(v, int) or v == 0:
            raise ValueError("Invalid chat ID")
        return v


class SecureChannel(BaseModel):
    """Secure channel model with XSS protection."""

    id: int = Field(..., gt=0)
    title: str = Field(..., max_length=255)
    username: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=500)
    is_verified: bool = False
    is_scam: bool = False
    is_fake: bool = False

    @validator("title")
    def sanitize_title(cls, v):
        return sanitize_user_input(v)

    @validator("username")
    def validate_channel_username(cls, v):
        if v and not re.match(r"^[a-zA-Z0-9_]{5,32}$", v):
            raise ValueError("Invalid channel username format")
        return v

    @validator("description")
    def sanitize_description(cls, v):
        if v:
            return sanitize_user_input(v)
        return v


class SecureBot(BaseModel):
    """Secure bot model with XSS protection."""

    id: int = Field(..., gt=0)
    username: str = Field(..., max_length=32)
    first_name: str = Field(..., max_length=64)
    can_join_groups: bool = False
    can_read_all_group_messages: bool = False
    supports_inline_queries: bool = False

    @validator("username")
    def validate_bot_username(cls, v):
        if not validate_username(v):
            raise ValueError("Invalid bot username format")
        return v

    @validator("first_name")
    def sanitize_first_name(cls, v):
        return sanitize_user_input(v)


class SecureSuspiciousProfile(BaseModel):
    """Secure suspicious profile model with XSS protection."""

    user_id: int = Field(..., gt=0)
    username: Optional[str] = Field(None, max_length=32)
    first_name: Optional[str] = Field(None, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    reason: str = Field(..., max_length=500)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_reviewed: bool = False
    admin_id: Optional[int] = Field(None, gt=0)

    @validator("user_id", "admin_id")
    def validate_ids(cls, v):
        if v and not validate_user_id(v):
            raise ValueError("Invalid user ID")
        return v

    @validator("username")
    def validate_username(cls, v):
        if v and not validate_username(v):
            raise ValueError("Invalid username format")
        return v

    @validator("first_name", "last_name", "reason")
    def sanitize_text_fields(cls, v):
        if v:
            return sanitize_user_input(v)
        return v


class SecureCommand(BaseModel):
    """Secure command model with XSS protection."""

    command: str = Field(..., max_length=32)
    args: List[str] = Field(default_factory=list)
    user_id: int = Field(..., gt=0)
    chat_id: int = Field(..., description="Chat ID")

    @validator("command")
    def validate_command(cls, v):
        if not re.match(r"^/[a-zA-Z0-9_]+$", v):
            raise ValueError("Invalid command format")
        return v

    @validator("args")
    def sanitize_args(cls, v):
        return [sanitize_user_input(arg) for arg in v]

    @validator("user_id", "chat_id")
    def validate_ids(cls, v):
        if not isinstance(v, int) or v == 0:
            raise ValueError("Invalid ID")
        return v


class SecureConfig(BaseModel):
    """Secure configuration model with validation."""

    bot_token: str = Field(..., min_length=10)
    admin_ids: List[int] = Field(..., min_items=1)
    db_path: str = Field(..., min_length=1)

    @validator("bot_token")
    def validate_bot_token(cls, v):
        if not re.match(r"^\d+:[a-zA-Z0-9_-]+$", v):
            raise ValueError("Invalid bot token format")
        return v

    @validator("admin_ids")
    def validate_admin_ids(cls, v):
        for admin_id in v:
            if not validate_user_id(admin_id):
                raise ValueError(f"Invalid admin ID: {admin_id}")
        return v

    @validator("db_path")
    def validate_db_path(cls, v):
        # Prevent path traversal
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid database path")
        return v
