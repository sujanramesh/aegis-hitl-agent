from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.risk import assess_action_risk

from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs

from app.llm.gemini import (
    analyze_evidence,
    propose_remediation,
)


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


def analyze_incident(state: AgentState) -> dict:
    """
    Analyze accumulated evidence and generate
    a grounded incident hypothesis.
    """

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


def propose_action(state: AgentState) -> dict:
    """
    Generate a proposed remediation action from the
    current incident hypothesis and evidence.
    """

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
    Route a consequential action toward human approval.

    This currently represents an approval state only.
    A real workflow interrupt and resume mechanism
    will be added later.
    """

    return {
        "status": "awaiting_approval"
    }


def ready_for_execution(state: AgentState) -> dict:
    """
    Mark a low-risk action as eligible for controlled execution.

    No operational action is executed by this node.
    """

    return {
        "status": "ready_for_execution"
    }


def route_after_risk_assessment(state: AgentState) -> str:
    """
    Select the next workflow path using the
    application-owned approval decision.
    """

    if state.requires_approval:
        return "approval"

    return "execution"


# Create the graph using Aegis's state schema.
workflow_builder = StateGraph(AgentState)


# Register workflow nodes.
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
    "ready_for_execution",
    ready_for_execution
)


# Define workflow transitions.
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
    "analyze_incident"
)

workflow_builder.add_edge(
    "analyze_incident",
    "propose_action"
)

workflow_builder.add_edge(
    "propose_action",
    "assess_risk"
)


# Route the workflow according to the risk-policy decision.
workflow_builder.add_conditional_edges(
    "assess_risk",
    route_after_risk_assessment,
    {
        "approval": "await_approval",
        "execution": "ready_for_execution"
    }
)


# Both paths currently stop here.
# Actual approval/resume and execution will be added later.
workflow_builder.add_edge(
    "await_approval",
    END
)

workflow_builder.add_edge(
    "ready_for_execution",
    END
)


# Compile only after all nodes and edges
# have been registered.
workflow = workflow_builder.compile()