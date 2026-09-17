from app.agent.state import AgentState
from app.agent.workflow import (
    analyze_incident,
    propose_action,
    route_after_analysis,
    route_after_action_proposal,
)
from app.llm.gemini import LLMUnavailableError


def make_incident_state():
    return AgentState(
        incident_title="Payment failures after deployment",
        incident_description=(
            "Customers started experiencing payment failures "
            "shortly after today's deployment."
        ),
        service="payment-service",
        evidence=[
            {
                "source": "service_health",
                "data": {
                    "status": "degraded",
                    "error_rate": 17.3,
                    "latency_ms": 840,
                },
            }
        ],
    )


def test_analysis_provider_failure_becomes_safe_state(
    monkeypatch,
):
    def fake_analyze_evidence(**kwargs):
        raise LLMUnavailableError(
            "Simulated Gemini outage"
        )

    monkeypatch.setattr(
        "app.agent.workflow.analyze_evidence",
        fake_analyze_evidence,
    )

    state = make_incident_state()

    result = analyze_incident(state)

    assert result["status"] == "llm_unavailable"
    assert result["hypothesis"] is None


def test_analysis_failure_routes_to_end():
    state = make_incident_state()
    state.status = "llm_unavailable"

    route = route_after_analysis(state)

    assert route == "failed"


def test_remediation_provider_failure_becomes_safe_state(
    monkeypatch,
):
    def fake_propose_remediation(**kwargs):
        raise LLMUnavailableError(
            "Simulated Gemini outage"
        )

    monkeypatch.setattr(
        "app.agent.workflow.propose_remediation",
        fake_propose_remediation,
    )

    state = make_incident_state()
    state.hypothesis = (
        "Payment gateway authentication failures "
        "are contributing to the incident."
    )

    result = propose_action(state)

    assert result["status"] == "llm_unavailable"
    assert result["proposed_action"] is None


def test_remediation_failure_routes_to_end():
    state = make_incident_state()
    state.status = "llm_unavailable"

    route = route_after_action_proposal(state)

    assert route == "failed"