"""Bot model."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.secure_models import *


class Bot(Base):
    """Bot model for managing bot whitelist."""

    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Status
    is_whitelisted = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Metadata
    can_join_groups = Column(Boolean, default=True, nullable=False)
    can_read_all_group_messages = Column(Boolean, default=False, nullable=False)
    supports_inline_queries = Column(Boolean, default=False, nullable=False)

    # Description
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, nullable=True)

    # Relationships
    moderation_logs = relationship("ModerationLog", back_populates="bot")

    def __repr__(self) -> str:
        return f"<Bot(id={self.telegram_id}, username={self.username}, whitelisted={self.is_whitelisted})>"
