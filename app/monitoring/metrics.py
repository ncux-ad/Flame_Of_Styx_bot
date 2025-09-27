"""Lightweight metrics collection for monitoring."""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Lightweight metrics collector without external dependencies."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.start_time = time.time()
        
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self.counters[key] += value
        self._record_metric(name, self.counters[key], labels)
        logger.debug(f"Counter {name} incremented by {value}")
        
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        self._record_metric(name, value, labels)
        logger.debug(f"Gauge {name} set to {value}")
        
    def record_timing(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric."""
        self._record_metric(name, duration, labels)
        logger.debug(f"Timing {name} recorded: {duration:.3f}s")
        
    def _record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric point."""
        metric_point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.metrics[name].append(metric_point)
        
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for labeled metrics."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
        
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0)
        
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, labels)
        return self.gauges.get(key)
        
    def get_metric_history(self, name: str, limit: int = 100) -> list[MetricPoint]:
        """Get recent history for a metric."""
        if name not in self.metrics:
            return []
        return list(self.metrics[name])[-limit:]
        
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring."""
        uptime = time.time() - self.start_time
        
        # Calculate rates
        total_messages = self.get_counter("messages_processed")
        message_rate = total_messages / uptime if uptime > 0 else 0
        
        total_bans = self.get_counter("users_banned")
        ban_rate = total_bans / uptime if uptime > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "uptime_human": self._format_duration(uptime),
            "total_messages": total_messages,
            "message_rate_per_second": round(message_rate, 2),
            "total_bans": total_bans,
            "ban_rate_per_second": round(ban_rate, 2),
            "active_gauges": len(self.gauges),
            "total_metrics": len(self.metrics),
            "memory_usage_mb": self._get_memory_usage(),
        }
        
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"
            
    def _get_memory_usage(self) -> float:
        """Get approximate memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except ImportError:
            return 0.0
            
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external monitoring."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "summary": self.get_summary(),
            "timestamp": time.time()
        }
