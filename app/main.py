import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends
from langgraph.types import Command
from sqlalchemy.orm import Session

from app.models import (
    IncidentRequest,
    ApprovalDecisionRequest,
)
from app.agent.workflow import workflow
from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs

from app.database.connection import get_db
from app.database.repository import (
    create_incident as create_incident_record,
    update_incident_status,
    create_audit_event,
)


app = FastAPI(
    title="Aegis",
    description=(
        "Human-in-the-Loop AI Operations Agent "
        "for safe incident investigation and remediation."
    ),
    version="0.4.0",
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
    db: Session = Depends(get_db),
):
    """
    Start a new Aegis incident workflow.

    The incident and important lifecycle events are
    persisted to MySQL.
    """

    thread_id = str(uuid4())

    # -----------------------------------------------------
    # Persist incident
    # -----------------------------------------------------

    create_incident_record(
        db=db,
        incident_id=thread_id,
        title=incident.title,
        description=incident.description,
        service=incident.service,
    )

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type="INCIDENT_CREATED",
        actor="system",
        details=(
            f"Incident created for service: "
            f"{incident.service}"
        ),
    )

    # -----------------------------------------------------
    # Start LangGraph workflow
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Persist latest workflow state
    # -----------------------------------------------------

    final_status = result.get(
        "status",
        "unknown",
    )

    update_incident_status(
        db=db,
        incident_id=thread_id,
        status=final_status,
    )

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type="INVESTIGATION_COMPLETED",
        actor="agent",
        details=json.dumps({
            "status": final_status,
            "hypothesis": result.get(
                "hypothesis"
            ),
            "risk_level": result.get(
                "risk_level"
            ),
            "requires_approval": result.get(
                "requires_approval",
                False,
            ),
        }),
    )

    # -----------------------------------------------------
    # Record approval requirement
    # -----------------------------------------------------

    if result.get(
        "requires_approval",
        False,
    ):
        create_audit_event(
            db=db,
            incident_id=thread_id,
            event_type="APPROVAL_REQUESTED",
            actor="system",
            details=json.dumps({
                "risk_level": result.get(
                    "risk_level"
                ),
                "status": final_status,
            }),
        )

    return serialize_workflow_result(
        thread_id,
        result,
    )


# =========================================================
# Retrieve incident
# =========================================================

@app.get("/incidents/{thread_id}")
def get_incident(
    thread_id: str,
):
    """
    Retrieve the latest checkpointed state of an incident.

    LangGraph is currently the workflow-state source.
    MySQL stores durable incident and audit records.
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


# =========================================================
# Human approval / rejection
# =========================================================

@app.post("/incidents/{thread_id}/decision")
def submit_decision(
    thread_id: str,
    decision: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    """
    Resume a checkpointed incident after an explicit
    human approval or rejection decision.

    The human decision, execution result and recovery
    verification are persisted to the audit trail.
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

    # -----------------------------------------------------
    # Persist human authorization decision
    # -----------------------------------------------------

    if decision.decision == "approved":
        decision_event = "HUMAN_APPROVED"
    else:
        decision_event = "HUMAN_REJECTED"

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type=decision_event,
        actor="human",
        details=decision.reason,
    )

    # -----------------------------------------------------
    # Resume the same LangGraph workflow
    # -----------------------------------------------------

    result = workflow.invoke(
        Command(
            resume={
                "decision": decision.decision,
                "reason": decision.reason,
            }
        ),
        config=config,
    )

    final_status = result.get(
        "status",
        "unknown",
    )

    # -----------------------------------------------------
    # Persist latest incident status
    # -----------------------------------------------------

    update_incident_status(
        db=db,
        incident_id=thread_id,
        status=final_status,
    )

    # -----------------------------------------------------
    # Persist execution result
    # -----------------------------------------------------

    execution_result = result.get(
        "execution_result"
    )

    if execution_result is not None:
        create_audit_event(
            db=db,
            incident_id=thread_id,
            event_type="ACTION_EXECUTED",
            actor="executor",
            details=json.dumps(
                execution_result
            ),
        )

    # -----------------------------------------------------
    # Persist recovery verification
    # -----------------------------------------------------

    verification_result = result.get(
        "verification_result"
    )

    if verification_result is not None:
        create_audit_event(
            db=db,
            incident_id=thread_id,
            event_type="RECOVERY_VERIFIED",
            actor="system",
            details=json.dumps(
                verification_result
            ),
        )

    # -----------------------------------------------------
    # Persist workflow completion
    # -----------------------------------------------------

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type="WORKFLOW_COMPLETED",
        actor="system",
        details=json.dumps({
            "status": final_status,
            "approval_decision": result.get(
                "approval_decision"
            ),
        }),
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
    return get_service_health(
        service_name
    )


@app.get("/services/{service_name}/deployments")
def recent_deployments(
    service_name: str,
):
    return get_recent_deployments(
        service_name
    )


@app.get("/services/{service_name}/logs")
def service_logs(
    service_name: str,
    query: str,
):
    return search_logs(
        service_name,
        query,
    )