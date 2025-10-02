"""Alert system for critical events and monitoring."""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    source: str
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[float] = None


class AlertManager:
    """Lightweight alert management system."""

    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_counters: Dict[str, int] = {}
        self.suppressed_alerts: Dict[str, float] = {}  # alert_id -> suppress_until

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
        logger.info("Alert handler added")

    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        source: str = "system",
        details: Optional[Dict[str, Any]] = None,
        alert_id: Optional[str] = None,
    ) -> Alert:
        """Create and process a new alert."""
        if alert_id is None:
            alert_id = f"{source}_{int(time.time())}"

        # Check if alert is suppressed
        if alert_id in self.suppressed_alerts:
            if time.time() < self.suppressed_alerts[alert_id]:
                logger.debug(f"Alert {alert_id} is suppressed")
                return None
            else:
                del self.suppressed_alerts[alert_id]

        alert = Alert(
            id=alert_id, level=level, title=title, message=message, timestamp=time.time(), source=source, details=details
        )

        # Add to alerts list
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts.pop(0)  # Remove oldest

        # Update counters
        self.alert_counters[alert_id] = self.alert_counters.get(alert_id, 0) + 1

        # Send to handlers
        self._send_alert(alert)

        logger.info(f"Alert created: {alert_id} - {title}")
        return alert

    def _send_alert(self, alert: Alert) -> None:
        """Send alert to all registered handlers."""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = time.time()
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False

    def suppress_alert(self, alert_id: str, duration_seconds: int = 300) -> None:
        """Suppress an alert for a specified duration."""
        self.suppressed_alerts[alert_id] = time.time() + duration_seconds
        logger.info(f"Alert suppressed: {alert_id} for {duration_seconds}s")

    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [alert for alert in self.alerts if not alert.resolved]

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get alerts by severity level."""
        return [alert for alert in self.alerts if alert.level == level]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert statistics summary."""
        active_alerts = self.get_active_alerts()

        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(self.alerts) - len(active_alerts),
            "alerts_by_level": {level.value: len(self.get_alerts_by_level(level)) for level in AlertLevel},
            "recent_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "timestamp": alert.timestamp,
                    "resolved": alert.resolved,
                }
                for alert in self.alerts[-10:]  # Last 10 alerts
            ],
            "suppressed_count": len(self.suppressed_alerts),
        }

    def cleanup_old_alerts(self, max_age_hours: int = 24) -> int:
        """Remove alerts older than specified hours."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        initial_count = len(self.alerts)

        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]

        removed_count = initial_count - len(self.alerts)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old alerts")

        return removed_count
