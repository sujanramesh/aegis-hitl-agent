from app.agent.actions import (
    ActionParameters,
    ProposedAction,
)
from app.infrastructure.mock_environment import MOCK_SERVICES
from app.tools.action_executor import execute_action


def reset_payment_service():
    """
    Reset the shared mock environment before each test.
    This keeps tests independent from one another.
    """
    MOCK_SERVICES["payment-service"] = {
        "version": "v2.14",
        "status": "degraded",
        "error_rate": 17.3,
        "latency_ms": 840,
    }


def test_valid_rollback_executes_successfully():
    reset_payment_service()

    action = ProposedAction(
        action_type="rollback_deployment",
        service="payment-service",
        parameters=ActionParameters(
            from_version="v2.14",
            to_version="v2.13",
        ),
        rationale="Rollback the recent deployment.",
    )

    result = execute_action(action)

    assert result["success"] is True
    assert result["from_version"] == "v2.14"
    assert result["to_version"] == "v2.13"

    assert MOCK_SERVICES["payment-service"]["version"] == "v2.13"
    assert MOCK_SERVICES["payment-service"]["status"] == "healthy"


def test_stale_rollback_is_blocked():
    reset_payment_service()

    action = ProposedAction(
        action_type="rollback_deployment",
        service="payment-service",
        parameters=ActionParameters(
            from_version="v9.99",
            to_version="v2.13",
        ),
        rationale="Attempt a stale rollback.",
    )

    result = execute_action(action)

    assert result["success"] is False
    assert "Version mismatch" in result["message"]

    assert MOCK_SERVICES["payment-service"]["version"] == "v2.14"
    assert MOCK_SERVICES["payment-service"]["status"] == "degraded"


def test_unsupported_action_is_blocked():
    reset_payment_service()

    action = ProposedAction(
        action_type="execute_shell_command",
        service="payment-service",
        parameters=ActionParameters(),
        rationale="Attempt an unsupported action.",
    )

    result = execute_action(action)

    assert result["success"] is False
    assert result["action_type"] == "execute_shell_command"
    assert "not supported" in result["message"]

    assert MOCK_SERVICES["payment-service"]["version"] == "v2.14"
    assert MOCK_SERVICES["payment-service"]["status"] == "degraded"


def test_rollback_requires_versions():
    reset_payment_service()

    action = ProposedAction(
        action_type="rollback_deployment",
        service="payment-service",
        parameters=ActionParameters(),
        rationale="Rollback without required version parameters.",
    )

    result = execute_action(action)

    assert result["success"] is False
    assert "requires from_version" in result["message"]

    assert MOCK_SERVICES["payment-service"]["version"] == "v2.14"