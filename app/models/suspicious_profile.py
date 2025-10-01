"""Suspicious profile model."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base

# from sqlalchemy.orm import relationship


class SuspiciousProfile(Base):
    """Suspicious profile model for tracking GPT-bots with bait channels."""

    __tablename__ = "suspicious_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Profile analysis
    linked_chat_id = Column(Integer, nullable=True)
    linked_chat_username = Column(String(255), nullable=True)
    linked_chat_title = Column(String(255), nullable=True)

    # Suspicion metrics
    post_count = Column(Integer, default=0, nullable=False)
    has_bait_channel = Column(Boolean, default=False, nullable=False)
    suspicion_score = Column(Float, default=0.0, nullable=False)

    # Analysis details
    analysis_reason = Column(Text, nullable=True)
    detected_patterns = Column(Text, nullable=True)  # JSON string

    # Status
    is_reviewed = Column(Boolean, default=False, nullable=False)
    is_confirmed_suspicious = Column(Boolean, default=False, nullable=False)
    is_false_positive = Column(Boolean, default=False, nullable=False)

    # Admin review
    reviewed_by = Column(Integer, nullable=True)  # admin telegram_id
    review_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        from app.models.secure_repr import secure_repr_suspicious_profile

        return secure_repr_suspicious_profile(self)
