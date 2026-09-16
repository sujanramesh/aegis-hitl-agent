def assess_action_risk(action: str) -> dict:
    """
    Assess the operational risk of a proposed action.

    The risk decision is owned by the application,
    not by the LLM.
    """

    action_lower = action.lower()

    high_risk_keywords = [
        "rollback",
        "roll back",
        "restart",
        "delete",
        "disable",
        "deploy",
        "rotate",
        "revoke",
    ]

    medium_risk_keywords = [
        "update",
        "modify",
        "change",
        "refresh",
    ]

    if any(
        keyword in action_lower
        for keyword in high_risk_keywords
    ):
        return {
            "risk_level": "high",
            "requires_approval": True
        }

    if any(
        keyword in action_lower
        for keyword in medium_risk_keywords
    ):
        return {
            "risk_level": "medium",
            "requires_approval": True
        }

    return {
        "risk_level": "low",
        "requires_approval": False
    }