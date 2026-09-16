from operator import add
from typing import Annotated, Any

from pydantic import BaseModel, Field
from app.agent.actions import ProposedAction


class AgentState(BaseModel):
    """
    Represents the current state of an Aegis incident workflow.
    """

    incident_title: str
    incident_description: str
    service: str

    status: str = "received"

    evidence: Annotated[
        list[dict[str, Any]],
        add
    ] = Field(default_factory=list)

    hypothesis: str | None = None

    proposed_action: ProposedAction | None = None

    risk_level: str | None = None

    requires_approval: bool = False

    approval_decision: str | None = None
    approval_reason: str | None = None

    execution_result: dict[str, Any] | None = None
    verification_result: dict[str, Any] | None = None

    