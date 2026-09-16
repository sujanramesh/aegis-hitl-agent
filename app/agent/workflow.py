from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs
from app.llm.gemini import analyze_evidence


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
    END
)


# Compile only after all nodes and edges
# have been registered.
workflow = workflow_builder.compile()