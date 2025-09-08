"""Moderation log model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
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
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="moderation_logs")
    channel = relationship("Channel", back_populates="moderation_logs")
    bot = relationship("Bot", back_populates="moderation_logs")
    
    def __repr__(self) -> str:
        return f"<ModerationLog(action={self.action}, user_id={self.user_id}, created_at={self.created_at})>"
