from app.agent.actions import (
    ActionParameters,
    ProposedAction,
)
from app.agent.state import AgentState
from app.agent.workflow import (
    action_cancelled,
    execute_authorized_action,
    route_after_approval,
    route_after_execution,
    verify_recovery,
)
from app.infrastructure.mock_environment import MOCK_SERVICES


def reset_payment_service():
    MOCK_SERVICES["payment-service"] = {
        "version": "v2.14",
        "status": "degraded",
        "error_rate": 17.3,
        "latency_ms": 840,
    }


def make_rollback_state(
    from_version="v2.14",
    to_version="v2.13",
):
    return AgentState(
        incident_title="Payment failures after deployment",
        incident_description=(
            "Customers are experiencing payment failures."
        ),
        service="payment-service",
        proposed_action=ProposedAction(
            action_type="rollback_deployment",
            service="payment-service",
            parameters=ActionParameters(
                from_version=from_version,
                to_version=to_version,
            ),
            rationale="Rollback the recent deployment.",
        ),
        risk_level="high",
        requires_approval=True,
    )


def test_rejected_action_routes_to_cancelled():
    state = make_rollback_state()
    state.approval_decision = "rejected"

    route = route_after_approval(state)

    assert route == "cancelled"


def test_cancelled_action_does_not_change_infrastructure():
    reset_payment_service()

    state = make_rollback_state()
    state.approval_decision = "rejected"

    result = action_cancelled(state)

    assert result["status"] == "action_cancelled"
    assert MOCK_SERVICES["payment-service"]["version"] == "v2.14"
    assert MOCK_SERVICES["payment-service"]["status"] == "degraded"


def test_approved_action_routes_to_execution():
    state = make_rollback_state()
    state.approval_decision = "approved"

    route = route_after_approval(state)

    assert route == "execution"


def test_successful_execution_routes_to_verification():
    reset_payment_service()

    state = make_rollback_state()

    execution = execute_authorized_action(state)

    state.execution_result = execution["execution_result"]

    route = route_after_execution(state)

    assert execution["status"] == "executed"
    assert state.execution_result["success"] is True
    assert route == "verify"


def test_failed_execution_does_not_route_to_verification():
    reset_payment_service()

    state = make_rollback_state(
        from_version="v9.99",
        to_version="v2.13",
    )

    execution = execute_authorized_action(state)

    state.execution_result = execution["execution_result"]

    route = route_after_execution(state)

    assert execution["status"] == "execution_failed"
    assert state.execution_result["success"] is False
    assert route == "failed"

    assert MOCK_SERVICES["payment-service"]["version"] == "v2.14"
    assert MOCK_SERVICES["payment-service"]["status"] == "degraded"


def test_successful_rollback_verifies_recovery():
    reset_payment_service()

    state = make_rollback_state()

    execution = execute_authorized_action(state)

    assert execution["status"] == "executed"

    state.execution_result = execution["execution_result"]

    verification = verify_recovery(state)

    assert verification["status"] == "resolved"
    assert verification["verification_result"]["recovered"] is True

    health = verification["verification_result"]["health"]

    assert health["status"] == "healthy"
    assert health["error_rate"] == 0.5
    assert health["latency_ms"] == 150