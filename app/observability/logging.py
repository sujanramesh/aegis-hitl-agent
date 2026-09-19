import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any
from app.observability.context import get_request_id


# =========================================================
# Sensitive data protection
# =========================================================

SENSITIVE_FIELDS = {
    "password",
    "token",
    "access_token",
    "authorization",
    "api_key",
    "secret",
    "jwt",
    "credential",
    "credentials",
}


def _is_sensitive_field(key: str) -> bool:
    normalized_key = key.lower().replace("-", "_")

    return any(
        sensitive_field in normalized_key
        for sensitive_field in SENSITIVE_FIELDS
    )


def sanitize_data(data: Any) -> Any:
    """
    Recursively redact sensitive information before it is logged.
    """

    if isinstance(data, dict):
        sanitized = {}

        for key, value in data.items():
            if _is_sensitive_field(str(key)):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_data(value)

        return sanitized

    if isinstance(data, list):
        return [
            sanitize_data(item)
            for item in data
        ]

    if isinstance(data, tuple):
        return tuple(
            sanitize_data(item)
            for item in data
        )

    return data


# =========================================================
# JSON formatter
# =========================================================

class JSONFormatter(logging.Formatter):

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        log_entry = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()

        if request_id:
            log_entry["request_id"] = request_id

        structured_data = getattr(
            record,
            "structured_data",
            None,
        )

        if structured_data:
            log_entry.update(
                sanitize_data(
                    structured_data
                )
            )

        if record.exc_info:
            log_entry["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            log_entry,
            default=str,
        )


# =========================================================
# Logger configuration
# =========================================================

def configure_logging(
    level: int = logging.INFO,
) -> None:

    root_logger = logging.getLogger()

    root_logger.setLevel(level)

    # Avoid duplicate handlers when FastAPI reloads.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        JSONFormatter()
    )

    root_logger.addHandler(
        handler
    )


# =========================================================
# Application logger
# =========================================================

def get_logger(
    name: str,
) -> logging.Logger:

    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    **context: Any,
) -> None:

    structured_data = {
        "event": event,
        **context,
    }

    logger.log(
        level,
        event,
        extra={
            "structured_data": (
                structured_data
            )
        },
    )