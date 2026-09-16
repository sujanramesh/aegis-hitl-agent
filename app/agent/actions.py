from pydantic import BaseModel


class ActionParameters(BaseModel):
    """
    Validated parameters that may be required
    by an Aegis operational action.
    """

    from_version: str | None = None
    to_version: str | None = None


class ProposedAction(BaseModel):
    """
    Structured representation of an operational action
    proposed by the Aegis reasoning layer.
    """

    action_type: str
    service: str
    parameters: ActionParameters
    rationale: str