import logging
import json
from contextvars import ContextVar
from typing import Optional

# Context variables for request tracing
request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id: ContextVar[Optional[int]] = ContextVar("user_id", default=None)


class ServiceLogger:
    """Structured logger for domain services."""

    def __init__(self, service_name: str):
        self.logger = logging.getLogger(service_name)
        self.service_name = service_name

    def _base_context(self) -> dict:
        """Return base context with request tracing."""
        return {
            "service": self.service_name,
            "request_id": request_id.get(),
            "user_id": user_id.get(),
        }

    def business_rule_rejected(self, rule_name: str, **context) -> None:
        """Log when a business rule rejects an operation (warning level)."""
        payload = {
            "event": "business_rule_rejected",
            "rule": rule_name,
            "type": "business_validation",
            **self._base_context(),
            **context,
        }
        self.logger.warning(json.dumps(payload))

    def operation_failed(
        self, operation: str, reason: str, error: Optional[str] = None, **context
    ) -> None:
        """Log when an operation fails (error level)."""
        payload = {
            "event": f"{operation}_failed",
            "reason": reason,
            "type": "system_error",
            **self._base_context(),
            **context,
        }
        if error:
            payload["error"] = error
        self.logger.error(json.dumps(payload))

    def operation_succeeded(
        self, operation: str, duration_ms: Optional[int] = None, **context
    ) -> None:
        """Log when an operation succeeds (info level)."""
        payload = {
            "event": f"{operation}_succeeded",
            "type": "success",
            **self._base_context(),
            **context,
        }
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        self.logger.info(json.dumps(payload))
