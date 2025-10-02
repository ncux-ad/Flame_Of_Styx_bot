"""Health check system for monitoring bot status."""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Lightweight health check system."""

    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self.last_check_time = 0
        self.check_interval = 30  # seconds
        self.cached_results: Dict[str, HealthCheck] = {}

    def register_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    def run_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheck(
                name=name, status=HealthStatus.UNKNOWN, message=f"Check '{name}' not found", timestamp=time.time()
            )

        try:
            result = self.checks[name]()
            if isinstance(result, tuple):
                status, message, details = result
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                message = result.get("message", "No message")
                details = result.get("details")
            else:
                status = HealthStatus.HEALTHY
                message = "Check passed"
                details = None

            health_check = HealthCheck(name=name, status=status, message=message, timestamp=time.time(), details=details)

            self.cached_results[name] = health_check
            return health_check

        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}")
            return HealthCheck(
                name=name, status=HealthStatus.CRITICAL, message=f"Check failed: {str(e)}", timestamp=time.time()
            )

    def run_all_checks(self, force: bool = False) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        current_time = time.time()

        if not force and (current_time - self.last_check_time) < self.check_interval:
            return self.cached_results

        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)

        self.last_check_time = current_time
        self.cached_results = results
        return results

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        results = self.run_all_checks()

        if not results:
            return HealthStatus.UNKNOWN

        statuses = [check.status for check in results.values()]

        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        results = self.run_all_checks()
        overall_status = self.get_overall_status()

        return {
            "overall_status": overall_status.value,
            "timestamp": time.time(),
            "total_checks": len(results),
            "healthy_checks": sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY),
            "warning_checks": sum(1 for r in results.values() if r.status == HealthStatus.WARNING),
            "critical_checks": sum(1 for r in results.values() if r.status == HealthStatus.CRITICAL),
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "timestamp": check.timestamp,
                    "details": check.details,
                }
                for name, check in results.items()
            },
        }
