import json
import logging
import os
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from langgraph.types import Command
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)

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
    list_incidents,
    create_audit_event,
    list_audit_events,
)

from app.auth.models import Token, User
from app.auth.security import (
    create_access_token,
    verify_password,
)

from app.auth.users import get_user
from app.auth.dependencies import require_roles

from app.observability.logging import (
    configure_logging,
    get_logger,
    log_event,
)

from app.observability.middleware import ObservabilityMiddleware
from app.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    INCIDENTS_TOTAL,
    APPROVAL_REQUESTS_TOTAL,
    APPROVAL_DECISIONS_TOTAL,
    ACTION_EXECUTIONS_TOTAL,
    RECOVERY_VERIFICATIONS_TOTAL,
    WORKFLOW_DURATION_SECONDS,
)


# =========================================================
# Observability configuration
# =========================================================

configure_logging()

logger = get_logger(
    "aegis.api"
)


# =========================================================
# FastAPI application
# =========================================================

app = FastAPI(
    title="Aegis",
    description=(
        "Human-in-the-Loop AI Operations Agent "
        "for safe incident investigation and remediation."
    ),
    version="0.8.0",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


# =========================================================
# Middleware
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    ObservabilityMiddleware
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

    Includes incident context, investigation evidence,
    remediation state, approval state, execution output,
    and recovery verification.
    """

    proposed_action = result.get(
        "proposed_action"
    )

    if hasattr(
        proposed_action,
        "model_dump",
    ):
        proposed_action = (
            proposed_action.model_dump()
        )

    interrupts = result.get(
        "__interrupt__"
    )

    awaiting_approval = bool(
        interrupts
    )

    return {
        "incident_id": thread_id,

        "title": result.get(
            "incident_title"
        ),

        "description": result.get(
            "incident_description"
        ),

        "service": result.get(
            "service"
        ),

        "status": result.get(
            "status"
        ),

        "evidence": result.get(
            "evidence",
            [],
        ),

        "hypothesis": result.get(
            "hypothesis"
        ),

        "proposed_action": proposed_action,

        "risk_level": result.get(
            "risk_level"
        ),

        "requires_approval": result.get(
            "requires_approval",
            False,
        ),

        "awaiting_approval": (
            awaiting_approval
        ),

        "approval_decision": result.get(
            "approval_decision"
        ),

        "approval_reason": result.get(
            "approval_reason"
        ),

        "execution_result": result.get(
            "execution_result"
        ),

        "verification_result": result.get(
            "verification_result"
        ),
    }


def get_action_type(
    result: dict,
) -> str:
    """
    Safely extract the proposed remediation action type
    for metrics and structured logs.
    """

    proposed_action = result.get(
        "proposed_action"
    )

    if proposed_action is None:
        return "unknown"

    if hasattr(
        proposed_action,
        "action_type",
    ):
        return str(
            proposed_action.action_type
        )

    if isinstance(
        proposed_action,
        dict,
    ):
        return str(
            proposed_action.get(
                "action_type",
                "unknown",
            )
        )

    return "unknown"


def get_execution_outcome(
    execution_result,
) -> str:
    """
    Convert execution output into a bounded metric label.
    """

    if not isinstance(
        execution_result,
        dict,
    ):
        return "unknown"

    success = execution_result.get(
        "success"
    )

    if success is True:
        return "success"

    if success is False:
        return "failure"

    return "unknown"


def get_verification_outcome(
    verification_result,
) -> str:
    """
    Convert recovery verification output into a bounded
    metric label.
    """

    if not isinstance(
        verification_result,
        dict,
    ):
        return "unknown"

    if verification_result.get(
        "recovered"
    ) is True:
        return "recovered"

    if verification_result.get(
        "recovered"
    ) is False:
        return "not_recovered"

    if verification_result.get(
        "healthy"
    ) is True:
        return "recovered"

    if verification_result.get(
        "healthy"
    ) is False:
        return "not_recovered"

    return "unknown"

def get_counter_samples(
    metric,
) -> list[dict]:
    """
    Convert a Prometheus Counter into JSON-safe samples.
    """

    samples = []

    for metric_family in metric.collect():
        for sample in metric_family.samples:
            if not sample.name.endswith(
                "_total"
            ):
                continue

            samples.append({
                "labels": dict(
                    sample.labels
                ),
                "value": sample.value,
            })

    return samples


def get_histogram_summary(
    metric,
) -> list[dict]:
    """
    Convert Prometheus Histogram count and sum values
    into JSON-safe summaries grouped by labels.
    """

    summaries = {}

    for metric_family in metric.collect():
        for sample in metric_family.samples:
            labels = dict(
                sample.labels
            )

            key = tuple(
                sorted(
                    labels.items()
                )
            )

            if key not in summaries:
                summaries[key] = {
                    "labels": labels,
                    "count": 0,
                    "sum": 0.0,
                }

            if sample.name.endswith(
                "_count"
            ):
                summaries[key]["count"] = (
                    sample.value
                )

            elif sample.name.endswith(
                "_sum"
            ):
                summaries[key]["sum"] = (
                    sample.value
                )

    result = []

    for summary in summaries.values():
        count = summary["count"]
        total = summary["sum"]

        average = (
            total / count
            if count
            else 0.0
        )

        result.append({
            "labels": summary["labels"],
            "count": count,
            "sum_seconds": round(
                total,
                6,
            ),
            "average_seconds": round(
                average,
                6,
            ),
        })

    return result


# =========================================================
# System health
# =========================================================

@app.get("/health")
def health_check():
    """
    Lightweight public service-health endpoint.

    Infrastructure health checks must be able to reach
    this endpoint without authentication.
    """

    return {
        "status": "healthy",
        "service": "aegis",
    }


@app.get("/metrics")
def metrics():
    """
    Expose Prometheus-compatible Aegis metrics.

    This endpoint will later be scraped by the
    production monitoring system.
    """

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

@app.get("/observability/summary")
def observability_summary(
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Return authenticated JSON operational metrics for
    the Aegis frontend observability dashboard.

    Prometheus remains the monitoring source of truth.
    This endpoint provides a frontend-friendly projection.
    """

    summary = {
        "http_requests": get_counter_samples(
            HTTP_REQUESTS_TOTAL
        ),
        "http_latency": get_histogram_summary(
            HTTP_REQUEST_DURATION_SECONDS
        ),
        "incidents": get_counter_samples(
            INCIDENTS_TOTAL
        ),
        "approval_requests": get_counter_samples(
            APPROVAL_REQUESTS_TOTAL
        ),
        "approval_decisions": get_counter_samples(
            APPROVAL_DECISIONS_TOTAL
        ),
        "action_executions": get_counter_samples(
            ACTION_EXECUTIONS_TOTAL
        ),
        "recovery_verifications": get_counter_samples(
            RECOVERY_VERIFICATIONS_TOTAL
        ),
        "workflow_latency": get_histogram_summary(
            WORKFLOW_DURATION_SECONDS
        ),
    }

    log_event(
        logger,
        logging.INFO,
        "observability_summary_retrieved",
        actor=current_user.username,
        role=current_user.role,
    )

    return summary


# =========================================================
# Authentication
# =========================================================

@app.post(
    "/auth/token",
    response_model=Token,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Authenticate an Aegis user and issue a signed
    JWT access token.
    """

    user = get_user(
        form_data.username
    )

    if user is None:
        log_event(
            logger,
            logging.WARNING,
            "authentication_failed",
            username=form_data.username,
            reason="invalid_credentials",
        )

        raise HTTPException(
            status_code=401,
            detail=(
                "Incorrect username "
                "or password."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        log_event(
            logger,
            logging.WARNING,
            "authentication_failed",
            username=form_data.username,
            reason="invalid_credentials",
        )

        raise HTTPException(
            status_code=401,
            detail=(
                "Incorrect username "
                "or password."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if user.disabled:
        log_event(
            logger,
            logging.WARNING,
            "authentication_failed",
            username=user.username,
            reason="disabled_account",
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "User account is disabled."
            ),
        )

    access_token = create_access_token(
        username=user.username,
        role=user.role,
    )

    log_event(
        logger,
        logging.INFO,
        "authentication_succeeded",
        actor=user.username,
        role=user.role,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@app.get(
    "/auth/me",
    response_model=User,
)
def get_authenticated_user(
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Return the currently authenticated Aegis user.

    The frontend uses this endpoint to establish the
    authenticated session and determine role-aware UI state.
    """

    return current_user


# =========================================================
# Incident workflow
# =========================================================

@app.post("/incidents")
def create_incident(
    incident: IncidentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "operator",
            "approver",
        )
    ),
):
    """
    Start a new Aegis incident workflow.

    Only operators and approvers may create incidents.

    The incident and important lifecycle events are
    persisted to MySQL.
    """

    workflow_started_at = (
        perf_counter()
    )

    thread_id = str(
        uuid4()
    )

    INCIDENTS_TOTAL.labels(
        service=incident.service,
    ).inc()

    log_event(
        logger,
        logging.INFO,
        "incident_created",
        incident_id=thread_id,
        service=incident.service,
        actor=current_user.username,
        role=current_user.role,
    )

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
        actor=current_user.username,
        details=json.dumps({
            "service": incident.service,
            "role": current_user.role,
        }),
    )

    # -----------------------------------------------------
    # Start LangGraph workflow
    # -----------------------------------------------------

    config = build_config(
        thread_id
    )

    initial_state = {
        "incident_title": (
            incident.title
        ),
        "incident_description": (
            incident.description
        ),
        "service": (
            incident.service
        ),
    }

    log_event(
        logger,
        logging.INFO,
        "investigation_started",
        incident_id=thread_id,
        service=incident.service,
    )

    investigation_started_at = (
        perf_counter()
    )

    result = workflow.invoke(
        initial_state,
        config=config,
    )

    investigation_duration = (
        perf_counter()
        - investigation_started_at
    )

    WORKFLOW_DURATION_SECONDS.labels(
        operation="investigation",
    ).observe(
        investigation_duration
    )

    # -----------------------------------------------------
    # Persist latest workflow state
    # -----------------------------------------------------

    final_status = result.get(
        "status",
        "unknown",
    )

    risk_level = (
        result.get(
            "risk_level"
        )
        or "unknown"
    )

    requires_approval = result.get(
        "requires_approval",
        False,
    )

    update_incident_status(
        db=db,
        incident_id=thread_id,
        status=final_status,
    )

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type=(
            "INVESTIGATION_COMPLETED"
        ),
        actor="agent",
        details=json.dumps({
            "status": final_status,
            "hypothesis": result.get(
                "hypothesis"
            ),
            "risk_level": result.get(
                "risk_level"
            ),
            "requires_approval": (
                requires_approval
            ),
        }),
    )

    log_event(
        logger,
        logging.INFO,
        "investigation_completed",
        incident_id=thread_id,
        service=incident.service,
        status=final_status,
        risk_level=risk_level,
        requires_approval=requires_approval,
        duration_ms=round(
            investigation_duration * 1000,
            2,
        ),
    )

    # -----------------------------------------------------
    # Record approval requirement
    # -----------------------------------------------------

    if requires_approval:
        APPROVAL_REQUESTS_TOTAL.labels(
            risk_level=risk_level,
        ).inc()

        create_audit_event(
            db=db,
            incident_id=thread_id,
            event_type=(
                "APPROVAL_REQUESTED"
            ),
            actor="system",
            details=json.dumps({
                "risk_level": result.get(
                    "risk_level"
                ),
                "status": final_status,
            }),
        )

        log_event(
            logger,
            logging.INFO,
            "approval_requested",
            incident_id=thread_id,
            service=incident.service,
            risk_level=risk_level,
            action_type=get_action_type(
                result
            ),
        )

    request_workflow_duration = (
        perf_counter()
        - workflow_started_at
    )

    WORKFLOW_DURATION_SECONDS.labels(
        operation="incident_creation",
    ).observe(
        request_workflow_duration
    )

    log_event(
        logger,
        logging.INFO,
        "incident_processing_paused"
        if requires_approval
        else "incident_processing_completed",
        incident_id=thread_id,
        service=incident.service,
        status=final_status,
        duration_ms=round(
            request_workflow_duration
            * 1000,
            2,
        ),
    )

    return serialize_workflow_result(
        thread_id,
        result,
    )


# =========================================================
# Retrieve incidents
# =========================================================

@app.get("/incidents")
def get_incidents(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Return persisted incidents ordered from newest to oldest.

    All authenticated Aegis roles may inspect the incident list.
    MySQL is the durable source for incident summary records.
    """

    safe_limit = max(
        1,
        min(limit, 100),
    )

    incidents = list_incidents(
        db,
        limit=safe_limit,
    )

    log_event(
        logger,
        logging.INFO,
        "incidents_listed",
        actor=current_user.username,
        role=current_user.role,
        count=len(incidents),
    )

    return [
        {
            "incident_id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "service": incident.service,
            "status": incident.status,
            "created_at": (
                incident.created_at.isoformat()
                if incident.created_at
                else None
            ),
            "updated_at": (
                incident.updated_at.isoformat()
                if incident.updated_at
                else None
            ),
        }
        for incident in incidents
    ]


@app.get("/incidents/{thread_id}")
def get_incident(
    thread_id: str,
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Retrieve the latest checkpointed state of an incident.

    All authenticated Aegis roles may inspect incidents.

    LangGraph is currently the workflow-state source.
    MySQL stores durable incident and audit records.
    """

    config = build_config(
        thread_id
    )

    snapshot = workflow.get_state(
        config
    )

    if not snapshot.values:
        log_event(
            logger,
            logging.WARNING,
            "incident_not_found",
            incident_id=thread_id,
            actor=current_user.username,
        )

        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    result = dict(
        snapshot.values
    )

    if snapshot.next:
        result[
            "__interrupt__"
        ] = True

    log_event(
        logger,
        logging.INFO,
        "incident_retrieved",
        incident_id=thread_id,
        actor=current_user.username,
        role=current_user.role,
        status=result.get(
            "status"
        ),
    )

    return serialize_workflow_result(
        thread_id,
        result,
    )


# =========================================================
# Human approval / rejection
# =========================================================

@app.post(
    "/incidents/{thread_id}/decision"
)
def submit_decision(
    thread_id: str,
    decision: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "approver",
        )
    ),
):
    """
    Resume a checkpointed incident after an explicit
    approval or rejection decision.

    Only an authenticated user with the approver role
    may authorize or reject a consequential operation.

    The authenticated identity, decision, execution result,
    and recovery verification are persisted to the audit
    trail.
    """

    decision_started_at = (
        perf_counter()
    )

    config = build_config(
        thread_id
    )

    snapshot = workflow.get_state(
        config
    )

    if not snapshot.values:
        log_event(
            logger,
            logging.WARNING,
            "decision_incident_not_found",
            incident_id=thread_id,
            actor=current_user.username,
        )

        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    if not snapshot.next:
        log_event(
            logger,
            logging.WARNING,
            "decision_rejected_by_state",
            incident_id=thread_id,
            actor=current_user.username,
            reason="not_awaiting_decision",
        )

        raise HTTPException(
            status_code=409,
            detail=(
                "Incident is not currently "
                "awaiting a workflow decision."
            ),
        )

    # -----------------------------------------------------
    # Persist authenticated authorization decision
    # -----------------------------------------------------

    if (
        decision.decision
        == "approved"
    ):
        decision_event = (
            "HUMAN_APPROVED"
        )
    else:
        decision_event = (
            "HUMAN_REJECTED"
        )

    APPROVAL_DECISIONS_TOTAL.labels(
        decision=decision.decision,
    ).inc()

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type=decision_event,
        actor=current_user.username,
        details=json.dumps({
            "decision": decision.decision,
            "reason": decision.reason,
            "role": current_user.role,
        }),
    )

    log_event(
        logger,
        logging.INFO,
        "human_decision_recorded",
        incident_id=thread_id,
        actor=current_user.username,
        role=current_user.role,
        decision=decision.decision,
    )

    # -----------------------------------------------------
    # Resume the same LangGraph workflow
    # -----------------------------------------------------

    resume_started_at = (
        perf_counter()
    )

    log_event(
        logger,
        logging.INFO,
        "workflow_resume_started",
        incident_id=thread_id,
        actor=current_user.username,
        decision=decision.decision,
    )

    result = workflow.invoke(
        Command(
            resume={
                "decision": (
                    decision.decision
                ),
                "reason": (
                    decision.reason
                ),
            }
        ),
        config=config,
    )

    resume_duration = (
        perf_counter()
        - resume_started_at
    )

    WORKFLOW_DURATION_SECONDS.labels(
        operation="decision_resume",
    ).observe(
        resume_duration
    )

    final_status = result.get(
        "status",
        "unknown",
    )

    log_event(
        logger,
        logging.INFO,
        "workflow_resume_completed",
        incident_id=thread_id,
        status=final_status,
        duration_ms=round(
            resume_duration * 1000,
            2,
        ),
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
        action_type = get_action_type(
            result
        )

        execution_outcome = (
            get_execution_outcome(
                execution_result
            )
        )

        ACTION_EXECUTIONS_TOTAL.labels(
            action_type=action_type,
            outcome=execution_outcome,
        ).inc()

        create_audit_event(
            db=db,
            incident_id=thread_id,
            event_type=(
                "ACTION_EXECUTED"
            ),
            actor="executor",
            details=json.dumps(
                execution_result
            ),
        )

        log_event(
            logger,
            logging.INFO,
            "action_executed",
            incident_id=thread_id,
            action_type=action_type,
            outcome=execution_outcome,
        )

    # -----------------------------------------------------
    # Persist recovery verification
    # -----------------------------------------------------

    verification_result = result.get(
        "verification_result"
    )

    if (
        verification_result
        is not None
    ):
        verification_outcome = (
            get_verification_outcome(
                verification_result
            )
        )

        RECOVERY_VERIFICATIONS_TOTAL.labels(
            outcome=verification_outcome,
        ).inc()

        create_audit_event(
            db=db,
            incident_id=thread_id,
            event_type=(
                "RECOVERY_VERIFIED"
            ),
            actor="system",
            details=json.dumps(
                verification_result
            ),
        )

        log_event(
            logger,
            logging.INFO,
            "recovery_verified",
            incident_id=thread_id,
            outcome=verification_outcome,
        )

    # -----------------------------------------------------
    # Persist workflow completion
    # -----------------------------------------------------

    create_audit_event(
        db=db,
        incident_id=thread_id,
        event_type=(
            "WORKFLOW_COMPLETED"
        ),
        actor="system",
        details=json.dumps({
            "status": final_status,
            "approval_decision": (
                result.get(
                    "approval_decision"
                )
            ),
            "authorized_by": (
                current_user.username
            ),
        }),
    )

    decision_duration = (
        perf_counter()
        - decision_started_at
    )

    WORKFLOW_DURATION_SECONDS.labels(
        operation="decision_processing",
    ).observe(
        decision_duration
    )

    log_event(
        logger,
        logging.INFO,
        "workflow_completed",
        incident_id=thread_id,
        status=final_status,
        approval_decision=result.get(
            "approval_decision"
        ),
        authorized_by=current_user.username,
        duration_ms=round(
            decision_duration * 1000,
            2,
        ),
    )

    return serialize_workflow_result(
        thread_id,
        result,
    )


# =========================================================
# Operational inspection endpoints
# =========================================================

@app.get(
    "/services/{service_name}/health"
)
def service_health(
    service_name: str,
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Inspect current service health.

    Available to all authenticated Aegis roles.
    """

    return get_service_health(
        service_name
    )


@app.get(
    "/services/{service_name}/deployments"
)
def recent_deployments(
    service_name: str,
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Inspect recent service deployments.

    Available to all authenticated Aegis roles.
    """

    return get_recent_deployments(
        service_name
    )


@app.get(
    "/services/{service_name}/logs"
)
def service_logs(
    service_name: str,
    query: str,
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Search operational logs.

    Available to all authenticated Aegis roles.
    """

    return search_logs(
        service_name,
        query,
    )

# =========================================================
# Pending human approvals
# =========================================================

@app.get("/approvals/pending")
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Return checkpointed incident workflows that are
    currently paused awaiting human authorization.

    MySQL provides the durable incident registry.
    LangGraph remains the source of truth for the
    current workflow execution state.

    Historical incidents without a surviving
    LangGraph checkpoint are skipped safely.
    """

    incidents = list_incidents(
        db,
        limit=100,
    )

    pending_approvals = []

    for incident in incidents:
        config = build_config(
            incident.id
        )

        snapshot = workflow.get_state(
            config
        )

        # Historical MySQL incidents may exist even when
        # their LangGraph checkpoint is no longer present.
        if not snapshot.values:
            continue

        # A workflow with no next node is not currently
        # suspended awaiting continuation.
        if not snapshot.next:
            continue

        result = dict(
            snapshot.values
        )

        # Only expose workflows whose application-owned
        # risk policy requires explicit human approval.
        if not result.get(
            "requires_approval",
            False,
        ):
            continue

        # serialize_workflow_result() determines
        # awaiting_approval from the interrupt marker.
        result["__interrupt__"] = True

        pending_approvals.append(
            serialize_workflow_result(
                incident.id,
                result,
            )
        )

    log_event(
        logger,
        logging.INFO,
        "pending_approvals_listed",
        actor=current_user.username,
        role=current_user.role,
        count=len(pending_approvals),
    )

    return pending_approvals

# =========================================================
# Audit trail
# =========================================================

@app.get("/audit-events")
def get_audit_events(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    """
    Return persisted operational audit events ordered
    from newest to oldest.

    All authenticated Aegis roles may inspect the audit trail.
    MySQL is the durable source of truth for audit records.
    """

    safe_limit = max(
        1,
        min(limit, 500),
    )

    events = list_audit_events(
        db,
        limit=safe_limit,
    )

    log_event(
        logger,
        logging.INFO,
        "audit_events_listed",
        actor=current_user.username,
        role=current_user.role,
        count=len(events),
    )

    return [
        {
            "id": event.id,
            "incident_id": event.incident_id,
            "event_type": event.event_type,
            "actor": event.actor,
            "details": event.details,
            "created_at": (
                event.created_at.isoformat()
                if event.created_at
                else None
            ),
        }
        for event in events
    ]