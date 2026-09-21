import os
import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.sqlite import SqliteSaver

from app.agent.state import AgentState
from app.agent.risk import assess_action_risk

from app.tools.action_executor import execute_action
from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs

from app.retrieval.semantic_retriever import semantic_search
from app.retrieval.runbooks import retrieve_runbook
from app.retrieval.embeddings import EmbeddingUnavailableError

from app.llm.gemini import (
    analyze_evidence,
    propose_remediation,
    LLMUnavailableError,
)


# =========================================================
# Incident investigation nodes
# =========================================================

def initialize_incident(state: AgentState) -> dict:
    """
    Move a newly received incident into the investigation stage.
    """

    return {
        "status": "investigating"
    }


def collect_service_health(state: AgentState) -> dict:
    """
    Collect service-health evidence for the affected service.
    """

    health = get_service_health(
        state.service
    )

    return {
        "evidence": [
            {
                "source": "service_health",
                "data": health
            }
        ]
    }


def collect_deployments(state: AgentState) -> dict:
    """
    Collect recent deployment evidence for the affected service.
    """

    deployments = get_recent_deployments(
        state.service
    )

    return {
        "evidence": [
            {
                "source": "recent_deployments",
                "data": deployments
            }
        ]
    }


def collect_logs(state: AgentState) -> dict:
    """
    Collect relevant error logs for the affected service.
    """

    logs = search_logs(
        state.service,
        "ERROR"
    )

    return {
        "evidence": [
            {
                "source": "service_logs",
                "data": logs
            }
        ]
    }


def collect_runbook(state: AgentState) -> dict:
    """
    Retrieve operational knowledge relevant to the incident.

    Semantic retrieval is the primary retrieval mechanism.

    If the embedding provider remains unavailable after
    bounded retries, Aegis falls back to deterministic
    service-scoped runbook retrieval.

    Retrieved runbook content is reference knowledge only.
    It is not observed incident evidence and does not
    authorize execution.
    """

    query = (
        f"Service: {state.service}\n"
        f"Incident title: {state.incident_title}\n"
        f"Incident description: {state.incident_description}"
    )

    try:
        results = semantic_search(
            query=query,
            top_k=3,
        )

        return {
            "evidence": [
                {
                    "source": "operational_runbook",
                    "retrieval_method": "semantic_search",
                    "query": query,
                    "data": results,
                }
            ]
        }

    except EmbeddingUnavailableError:

        print(
            "[Aegis Retrieval] Semantic retrieval unavailable. "
            "Falling back to deterministic service runbook retrieval."
        )

        fallback = retrieve_runbook(
            state.service
        )

        return {
            "evidence": [
                {
                    "source": "operational_runbook",
                    "retrieval_method": (
                        "deterministic_service_fallback"
                    ),
                    "query": query,
                    "semantic_retrieval_available": False,
                    "data": fallback,
                }
            ]
        }


# =========================================================
# Reasoning nodes
# =========================================================

def analyze_incident(state: AgentState) -> dict:
    """
    Analyze accumulated evidence and generate
    a grounded incident hypothesis.

    If the configured LLM provider remains unavailable
    after controlled retries, move the workflow into a
    safe failure state instead of propagating the provider
    exception through the graph.
    """

    try:
        hypothesis = analyze_evidence(
            incident_title=state.incident_title,
            incident_description=state.incident_description,
            service=state.service,
            evidence=state.evidence
        )

        return {
            "hypothesis": hypothesis,
            "status": "analyzed"
        }

    except LLMUnavailableError:
        return {
            "hypothesis": None,
            "status": "llm_unavailable"
        }


def propose_action(state: AgentState) -> dict:
    """
    Generate a structured remediation action from the
    current incident hypothesis and evidence.

    If the LLM becomes unavailable during remediation
    generation, stop the reasoning path safely.
    """

    try:
        action = propose_remediation(
            incident_title=state.incident_title,
            service=state.service,
            hypothesis=state.hypothesis,
            evidence=state.evidence
        )

        return {
            "proposed_action": action,
            "status": "action_proposed"
        }

    except LLMUnavailableError:
        return {
            "proposed_action": None,
            "status": "llm_unavailable"
        }


# =========================================================
# Risk and human approval nodes
# =========================================================

def assess_risk(state: AgentState) -> dict:
    """
    Assess the operational risk of the proposed action
    using the application-owned risk policy.
    """

    risk_result = assess_action_risk(
        state.proposed_action
    )

    return {
        "risk_level": risk_result["risk_level"],
        "requires_approval": risk_result["requires_approval"],
        "status": "risk_assessed"
    }


def await_approval(state: AgentState) -> dict:
    """
    Pause the workflow and request a human decision
    for a consequential operational action.
    """

    decision = interrupt(
        {
            "message": "Human approval required",
            "service": state.service,
            "proposed_action": (
                state.proposed_action.model_dump()
            ),
            "risk_level": state.risk_level,
        }
    )

    return {
        "approval_decision": decision.get("decision"),
        "approval_reason": decision.get("reason"),
        "status": "approval_received"
    }


def action_cancelled(state: AgentState) -> dict:
    """
    Mark a proposed action as cancelled after
    human rejection.
    """

    return {
        "status": "action_cancelled"
    }


# =========================================================
# Execution and verification nodes
# =========================================================

def execute_authorized_action(state: AgentState) -> dict:
    """
    Execute an action only after it has passed the
    application's authorization path.
    """

    if state.proposed_action is None:
        return {
            "execution_result": {
                "success": False,
                "message": "No proposed action available."
            },
            "status": "execution_failed"
        }

    result = execute_action(
        state.proposed_action
    )

    return {
        "execution_result": result,
        "status": (
            "executed"
            if result["success"]
            else "execution_failed"
        )
    }


def verify_recovery(state: AgentState) -> dict:
    """
    Verify the operational health of the service
    after an authorized action has executed successfully.
    """

    health = get_service_health(
        state.service
    )

    recovered = (
        health["status"] == "healthy"
    )

    return {
        "verification_result": {
            "recovered": recovered,
            "health": health
        },
        "status": (
            "resolved"
            if recovered
            else "verification_failed"
        )
    }


# =========================================================
# Routing functions
# =========================================================

def route_after_analysis(state: AgentState) -> str:
    """
    Continue to remediation proposal only when
    LLM analysis completed successfully.
    """

    if state.status == "llm_unavailable":
        return "failed"

    return "continue"


def route_after_action_proposal(state: AgentState) -> str:
    """
    Continue to risk assessment only when the
    LLM successfully produced a remediation action.
    """

    if state.status == "llm_unavailable":
        return "failed"

    return "continue"


def route_after_risk_assessment(state: AgentState) -> str:
    """
    Route according to the application-owned
    risk and approval policy.
    """

    if state.requires_approval:
        return "approval"

    return "execution"


def route_after_approval(state: AgentState) -> str:
    """
    Route according to the human approval decision.
    """

    if state.approval_decision == "approved":
        return "execution"

    return "cancelled"


def route_after_execution(state: AgentState) -> str:
    """
    Route according to whether the authorized
    operational action executed successfully.
    """

    if (
        state.execution_result
        and state.execution_result.get("success")
    ):
        return "verify"

    return "failed"


# =========================================================
# Build workflow graph
# =========================================================

workflow_builder = StateGraph(
    AgentState
)


# =========================================================
# Register nodes
# =========================================================

workflow_builder.add_node(
    "initialize_incident",
    initialize_incident
)

workflow_builder.add_node(
    "collect_service_health",
    collect_service_health
)

workflow_builder.add_node(
    "collect_deployments",
    collect_deployments
)

workflow_builder.add_node(
    "collect_logs",
    collect_logs
)

workflow_builder.add_node(
    "collect_runbook",
    collect_runbook
)

workflow_builder.add_node(
    "analyze_incident",
    analyze_incident
)

workflow_builder.add_node(
    "propose_action",
    propose_action
)

workflow_builder.add_node(
    "assess_risk",
    assess_risk
)

workflow_builder.add_node(
    "await_approval",
    await_approval
)

workflow_builder.add_node(
    "execute_authorized_action",
    execute_authorized_action
)

workflow_builder.add_node(
    "verify_recovery",
    verify_recovery
)

workflow_builder.add_node(
    "action_cancelled",
    action_cancelled
)


# =========================================================
# Investigation flow
# =========================================================

workflow_builder.add_edge(
    START,
    "initialize_incident"
)

workflow_builder.add_edge(
    "initialize_incident",
    "collect_service_health"
)

workflow_builder.add_edge(
    "collect_service_health",
    "collect_deployments"
)

workflow_builder.add_edge(
    "collect_deployments",
    "collect_logs"
)

workflow_builder.add_edge(
    "collect_logs",
    "collect_runbook"
)


# =========================================================
# LLM analysis routing
# =========================================================

workflow_builder.add_edge(
    "collect_runbook",
    "analyze_incident"
)

workflow_builder.add_conditional_edges(
    "analyze_incident",
    route_after_analysis,
    {
        "continue": "propose_action",
        "failed": END
    }
)


# =========================================================
# LLM remediation routing
# =========================================================

workflow_builder.add_conditional_edges(
    "propose_action",
    route_after_action_proposal,
    {
        "continue": "assess_risk",
        "failed": END
    }
)


# =========================================================
# Risk-based routing
# =========================================================

workflow_builder.add_conditional_edges(
    "assess_risk",
    route_after_risk_assessment,
    {
        "approval": "await_approval",
        "execution": "execute_authorized_action"
    }
)


# =========================================================
# Human approval routing
# =========================================================

workflow_builder.add_conditional_edges(
    "await_approval",
    route_after_approval,
    {
        "execution": "execute_authorized_action",
        "cancelled": "action_cancelled"
    }
)


# =========================================================
# Execution-result routing
# =========================================================

workflow_builder.add_conditional_edges(
    "execute_authorized_action",
    route_after_execution,
    {
        "verify": "verify_recovery",
        "failed": END
    }
)


# =========================================================
# Terminal paths
# =========================================================

workflow_builder.add_edge(
    "verify_recovery",
    END
)

workflow_builder.add_edge(
    "action_cancelled",
    END
)

# =========================================================
# Durable checkpointing
# =========================================================

checkpoint_path = os.getenv(
    "AEGIS_CHECKPOINT_PATH",
    "aegis_checkpoints.sqlite",
)

checkpoint_connection = sqlite3.connect(
    checkpoint_path,
    check_same_thread=False,
)

checkpointer = SqliteSaver(
    checkpoint_connection
)

workflow = workflow_builder.compile(
    checkpointer=checkpointer
)