from app.agent.actions import ProposedAction


def assess_action_risk(
    action: ProposedAction
) -> dict:
    """
    Assess the operational risk of a structured action.

    Risk policy is deterministic and application-owned.
    The LLM does not decide whether its proposed action
    is safe or whether human approval is required.
    """

    high_risk_actions = {
        "rollback_deployment",
        "restart_service",
        "rotate_credential",
        "revoke_credential",
        "deploy_service",
        "disable_service",
        "delete_resource",
    }

    medium_risk_actions = {
        "update_configuration",
        "modify_configuration",
        "refresh_configuration",
    }

    if action.action_type in high_risk_actions:
        return {
            "risk_level": "high",
            "requires_approval": True
        }

    if action.action_type in medium_risk_actions:
        return {
            "risk_level": "medium",
            "requires_approval": True
        }

    return {
        "risk_level": "low",
        "requires_approval": False
    }