from typing import Any

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    Represents the current state of an Aegis incident workflow.
    """

    incident_title: str
    incident_description: str
    service: str

    status: str = "received"

    evidence: list[dict[str, Any]] = Field(
        default_factory=list
    )

    hypothesis: str | None = None

    proposed_action: str | None = None

    requires_approval: bool = False