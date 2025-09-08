"""Secure __repr__ methods for all models."""

from app.utils.security import sanitize_for_logging


def secure_repr_user(user):
    """Secure __repr__ for User model."""
    return f"<User(id={user.telegram_id}, username={sanitize_for_logging(user.username)}, is_bot={user.is_bot})>"


def secure_repr_suspicious_profile(profile):
    """Secure __repr__ for SuspiciousProfile model."""
    return f"<SuspiciousProfile(user_id={profile.user_id}, score={profile.suspicion_score}, reviewed={profile.is_reviewed})>"


def secure_repr_moderation_log(log):
    """Secure __repr__ for ModerationLog model."""
    return f"<ModerationLog(action={sanitize_for_logging(log.action)}, user_id={log.user_id}, created_at={log.created_at})>"


def secure_repr_channel(channel):
    """Secure __repr__ for Channel model."""
    return f"<Channel(id={channel.telegram_id}, title={sanitize_for_logging(channel.title)}, username={sanitize_for_logging(channel.username)})>"


def secure_repr_bot(bot):
    """Secure __repr__ for Bot model."""
    return f"<Bot(id={bot.telegram_id}, username={sanitize_for_logging(bot.username)}, is_whitelisted={bot.is_whitelisted})>"
