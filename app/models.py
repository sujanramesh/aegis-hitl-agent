from typing import Literal

from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=200,
    )
    description: str = Field(
        min_length=10,
        max_length=2000,
    )
    service: str = Field(
        min_length=2,
        max_length=100,
    )


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )