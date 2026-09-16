from app.agent.actions import ProposedAction
from app.infrastructure.mock_environment import rollback_service


def execute_action(action: ProposedAction) -> dict:
    """
    Execute an authorized operational action in the
    controlled Aegis mock environment.

    Only explicitly allowlisted action types can execute.
    """

    if action.action_type == "rollback_deployment":

        from_version = action.parameters.from_version
        to_version = action.parameters.to_version

        if not from_version or not to_version:
            return {
                "success": False,
                "action_type": action.action_type,
                "service": action.service,
                "message": (
                    "Rollback requires from_version "
                    "and to_version."
                )
            }

        result = rollback_service(
            service_name=action.service,
            from_version=from_version,
            to_version=to_version
        )

        return {
            "action_type": action.action_type,
            **result
        }

    return {
        "success": False,
        "action_type": action.action_type,
        "service": action.service,
        "message": "Action type is not supported by the executor."
    }