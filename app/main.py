from uuid import uuid4

from fastapi import FastAPI, HTTPException
from langgraph.types import Command

from app.models import (
    IncidentRequest,
    ApprovalDecisionRequest,
)
from app.agent.workflow import workflow
from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs


app = FastAPI(
    title="Aegis",
    description=(
        "Human-in-the-Loop AI Operations Agent "
        "for safe incident investigation and remediation."
    ),
    version="0.2.0",
)


# =========================================================
# Helpers
# =========================================================

def build_config(thread_id: str) -> dict:
    """
    Build the LangGraph configuration used to identify
    a checkpointed incident workflow.
    """
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }


def serialize_workflow_result(
    thread_id: str,
    result: dict,
) -> dict:
    """
    Convert LangGraph state into an API-safe response.
    """

    proposed_action = result.get("proposed_action")

    if hasattr(proposed_action, "model_dump"):
        proposed_action = proposed_action.model_dump()

    interrupts = result.get("__interrupt__")

    awaiting_approval = bool(interrupts)

    return {
        "incident_id": thread_id,
        "status": result.get("status"),
        "hypothesis": result.get("hypothesis"),
        "proposed_action": proposed_action,
        "risk_level": result.get("risk_level"),
        "requires_approval": result.get(
            "requires_approval",
            False,
        ),
        "awaiting_approval": awaiting_approval,
        "approval_decision": result.get(
            "approval_decision"
        ),
        "execution_result": result.get(
            "execution_result"
        ),
        "verification_result": result.get(
            "verification_result"
        ),
    }


# =========================================================
# System health
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "aegis",
    }


# =========================================================
# Incident workflow
# =========================================================

@app.post("/incidents")
def create_incident(
    incident: IncidentRequest,
):
    """
    Start a new Aegis incident workflow.
    """

    thread_id = str(uuid4())

    config = build_config(thread_id)

    initial_state = {
        "incident_title": incident.title,
        "incident_description": incident.description,
        "service": incident.service,
    }

    result = workflow.invoke(
        initial_state,
        config=config,
    )

    return serialize_workflow_result(
        thread_id,
        result,
    )


@app.get("/incidents/{thread_id}")
def get_incident(
    thread_id: str,
):
    """
    Retrieve the latest checkpointed state of an incident.
    """

    config = build_config(thread_id)

    snapshot = workflow.get_state(config)

    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    result = dict(snapshot.values)

    if snapshot.next:
        result["__interrupt__"] = True

    return serialize_workflow_result(
        thread_id,
        result,
    )


@app.post("/incidents/{thread_id}/decision")
def submit_decision(
    thread_id: str,
    decision: ApprovalDecisionRequest,
):
    """
    Resume a checkpointed incident after a human
    approval or rejection decision.
    """

    config = build_config(thread_id)

    snapshot = workflow.get_state(config)

    if not snapshot.values:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    if not snapshot.next:
        raise HTTPException(
            status_code=409,
            detail=(
                "Incident is not currently awaiting "
                "a workflow decision."
            ),
        )

    result = workflow.invoke(
        Command(
            resume={
                "decision": decision.decision,
                "reason": decision.reason,
            }
        ),
        config=config,
    )

    return serialize_workflow_result(
        thread_id,
        result,
    )


# =========================================================
# Operational inspection endpoints
# =========================================================

@app.get("/services/{service_name}/health")
def service_health(
    service_name: str,
):
    return get_service_health(service_name)


@app.get("/services/{service_name}/deployments")
def recent_deployments(
    service_name: str,
):
    return get_recent_deployments(service_name)


@app.get("/services/{service_name}/logs")
def service_logs(
    service_name: str,
    query: str,
):
    return search_logs(
        service_name,
        query,
    )