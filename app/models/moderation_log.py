"""Moderation log model."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ModerationAction(enum.Enum):
    """Moderation action enum."""

    BAN = "ban"
    UNBAN = "unban"
    MUTE = "mute"
    UNMUTE = "unmute"
    DELETE_MESSAGE = "delete_message"
    ALLOW_CHANNEL = "allow_channel"
    BLOCK_CHANNEL = "block_channel"
    ALLOW_BOT = "allow_bot"
    BLOCK_BOT = "block_bot"
    MARK_SUSPICIOUS = "mark_suspicious"
    BLOCK = "block"


class ModerationLog(Base):
    """Moderation log model for tracking all moderation actions."""

    __tablename__ = "moderation_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Action details
    action = Column(Enum(ModerationAction), nullable=False)
    reason = Column(Text, nullable=True)
    details = Column(Text, nullable=True)

    # Related entities
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=True)

    # Admin who performed the action
    admin_telegram_id = Column(Integer, nullable=False)
    admin_username = Column(String(255), nullable=True)

    # Message details
    message_id = Column(Integer, nullable=True)
    chat_id = Column(Integer, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="moderation_logs")
    channel = relationship("Channel", back_populates="moderation_logs")
    bot = relationship("Bot", back_populates="moderation_logs")

    def __repr__(self) -> str:
        from app.models.secure_repr import secure_repr_moderation_log

        return secure_repr_moderation_log(self)
