"""Channel model."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.secure_models import *


class ChannelStatus(enum.Enum):
    """Channel status enum."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    PENDING = "pending"
    SUSPICIOUS = "suspicious"


class Channel(Base):
    """Channel model for managing channel whitelist/blacklist."""

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Status
    status = Column(Enum(ChannelStatus), default=ChannelStatus.PENDING, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_native = Column(Boolean, default=False, nullable=False)

    # Metadata
    member_count = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)

    # Relationships
    moderation_logs = relationship("ModerationLog", back_populates="channel")

    def __repr__(self) -> str:
        return f"<Channel(id={self.telegram_id}, username={self.username}, status={self.status})>"
