import json
import logging

from app.observability.context import (
    generate_request_id,
    get_request_id,
    reset_request_id,
    set_request_id,
)
from app.observability.logging import (
    JSONFormatter,
    sanitize_data,
)


# =========================================================
# Sensitive-data sanitization
# =========================================================

def test_sensitive_fields_are_redacted():

    data = {
        "username": "operator",
        "password": "super-secret",
        "access_token": "jwt-value",
        "api_key": "api-secret",
    }

    sanitized = sanitize_data(data)

    assert sanitized["username"] == "operator"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"


def test_nested_sensitive_fields_are_redacted():

    data = {
        "incident": {
            "service": "payment-service",
            "credentials": {
                "token": "secret-token",
            },
        }
    }

    sanitized = sanitize_data(data)

    assert (
        sanitized["incident"]["service"]
        == "payment-service"
    )

    assert (
        sanitized["incident"]
        ["credentials"]
        == "[REDACTED]"
    )


# =========================================================
# Request context
# =========================================================

def test_request_context_lifecycle():

    assert get_request_id() is None

    request_id = generate_request_id()

    token = set_request_id(
        request_id
    )

    assert get_request_id() == request_id

    reset_request_id(
        token
    )

    assert get_request_id() is None


def test_generated_request_ids_are_unique():

    first = generate_request_id()
    second = generate_request_id()

    assert first != second


# =========================================================
# JSON structured logging
# =========================================================

def test_json_formatter_produces_valid_json():

    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="aegis.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test_event",
        args=(),
        exc_info=None,
    )

    record.structured_data = {
        "event": "test_event",
        "incident_id": "incident-123",
        "service": "payment-service",
    }

    output = formatter.format(
        record
    )

    parsed = json.loads(
        output
    )

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "aegis.test"
    assert parsed["event"] == "test_event"

    assert (
        parsed["incident_id"]
        == "incident-123"
    )

    assert (
        parsed["service"]
        == "payment-service"
    )


def test_json_formatter_includes_request_id():

    formatter = JSONFormatter()

    request_id = generate_request_id()

    token = set_request_id(
        request_id
    )

    try:
        record = logging.LogRecord(
            name="aegis.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="correlation_test",
            args=(),
            exc_info=None,
        )

        record.structured_data = {
            "event": "correlation_test",
        }

        output = formatter.format(
            record
        )

        parsed = json.loads(
            output
        )

        assert (
            parsed["request_id"]
            == request_id
        )

    finally:
        reset_request_id(
            token
        )


def test_json_formatter_redacts_secrets():

    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="aegis.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="security_test",
        args=(),
        exc_info=None,
    )

    record.structured_data = {
        "event": "security_test",
        "access_token": (
            "must-not-appear"
        ),
    }

    output = formatter.format(
        record
    )

    parsed = json.loads(
        output
    )

    assert (
        parsed["access_token"]
        == "[REDACTED]"
    )

    assert (
        "must-not-appear"
        not in output
    )