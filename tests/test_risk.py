from app.agent.actions import (
    ActionParameters,
    ProposedAction,
)
from app.agent.risk import assess_action_risk


def test_rollback_requires_human_approval():
    action = ProposedAction(
        action_type="rollback_deployment",
        service="payment-service",
        parameters=ActionParameters(
            from_version="v2.14",
            to_version="v2.13",
        ),
        rationale="Rollback the recent deployment.",
    )

    result = assess_action_risk(action)

    assert result["risk_level"] == "high"
    assert result["requires_approval"] is True


def test_read_only_action_is_low_risk():
    action = ProposedAction(
        action_type="inspect_configuration",
        service="payment-service",
        parameters=ActionParameters(),
        rationale="Inspect the current configuration.",
    )

    result = assess_action_risk(action)

    assert result["risk_level"] == "low"
    assert result["requires_approval"] is False


def test_configuration_change_requires_approval():
    action = ProposedAction(
        action_type="update_configuration",
        service="payment-service",
        parameters=ActionParameters(),
        rationale="Update service configuration.",
    )

    result = assess_action_risk(action)

    assert result["risk_level"] == "medium"
    assert result["requires_approval"] is True