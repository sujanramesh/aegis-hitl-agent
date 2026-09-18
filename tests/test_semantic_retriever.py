from unittest.mock import patch

from app.agent.state import AgentState
from app.agent.workflow import collect_runbook

from app.retrieval.embeddings import EmbeddingUnavailableError
from app.retrieval.semantic_retriever import (
    chunk_markdown,
    cosine_similarity,
    load_runbook_chunks,
    semantic_search,
)


def test_cosine_similarity_identical_vectors():
    vector = [1.0, 2.0, 3.0]

    score = cosine_similarity(
        vector,
        vector,
    )

    assert abs(score - 1.0) < 1e-9


def test_runbook_chunks_are_loaded():
    chunks = load_runbook_chunks()

    assert len(chunks) > 0

    sources = {
        chunk["source"]
        for chunk in chunks
    }

    assert "payment_service.md" in sources
    assert "auth_service.md" in sources
    assert "order_service.md" in sources


def test_small_metadata_chunks_are_removed():
    content = """
# Payment Service

## Service
payment-service

## Authentication Failure Investigation

Payment requests are failing because the external
gateway is rejecting authentication credentials.
Investigate credentials and recent configuration changes.
"""

    chunks = chunk_markdown(content)

    assert len(chunks) == 1

    assert (
        "Authentication Failure Investigation"
        in chunks[0]
    )


def test_payment_incident_retrieves_payment_runbook():
    """
    Integration-style test using the real Gemini
    embedding provider.
    """

    results = semantic_search(
        query=(
            "Customers cannot complete payments because "
            "the payment provider is rejecting API credentials."
        ),
        top_k=1,
    )

    assert len(results) == 1

    assert (
        results[0]["source"]
        == "payment_service.md"
    )

    assert results[0]["similarity_score"] > 0


def test_collect_runbook_uses_semantic_retrieval_when_available():
    """
    Verify that semantic retrieval remains the primary
    runbook retrieval mechanism.
    """

    state = AgentState(
        incident_title="Checkout transactions failing",
        incident_description=(
            "Customers cannot complete purchases because "
            "the payment provider is rejecting requests."
        ),
        service="payment-service",
    )

    semantic_results = [
        {
            "source": "payment_service.md",
            "chunk_id": 0,
            "content": "Payment service runbook guidance.",
            "similarity_score": 0.9,
        }
    ]

    with patch(
        "app.agent.workflow.semantic_search",
        return_value=semantic_results,
    ) as mock_semantic_search:

        result = collect_runbook(state)

    mock_semantic_search.assert_called_once()

    evidence = result["evidence"][0]

    assert evidence["source"] == "operational_runbook"

    assert (
        evidence["retrieval_method"]
        == "semantic_search"
    )

    assert evidence["data"] == semantic_results


def test_collect_runbook_falls_back_when_embeddings_unavailable():
    """
    Verify that an embedding-provider outage does not
    terminate runbook retrieval.

    Semantic retrieval fails with EmbeddingUnavailableError,
    after which Aegis falls back to deterministic
    service-scoped runbook retrieval.
    """

    state = AgentState(
        incident_title="Checkout transactions failing",
        incident_description=(
            "Customers cannot complete purchases because "
            "the payment provider is rejecting requests."
        ),
        service="payment-service",
    )

    fallback_result = {
        "found": True,
        "service": "payment-service",
        "source": "payment_service.md",
        "content": "Deterministic payment runbook.",
    }

    with patch(
        "app.agent.workflow.semantic_search",
        side_effect=EmbeddingUnavailableError(
            "Embedding provider unavailable."
        ),
    ) as mock_semantic_search:

        with patch(
            "app.agent.workflow.retrieve_runbook",
            return_value=fallback_result,
        ) as mock_retrieve_runbook:

            result = collect_runbook(state)

    mock_semantic_search.assert_called_once()

    mock_retrieve_runbook.assert_called_once_with(
        "payment-service"
    )

    evidence = result["evidence"][0]

    assert evidence["source"] == "operational_runbook"

    assert (
        evidence["retrieval_method"]
        == "deterministic_service_fallback"
    )

    assert (
        evidence["semantic_retrieval_available"]
        is False
    )

    assert evidence["data"] == fallback_result