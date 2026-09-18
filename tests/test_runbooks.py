from app.retrieval.runbooks import retrieve_runbook


def test_payment_service_runbook_is_retrieved():
    result = retrieve_runbook(
        "payment-service"
    )

    assert result["found"] is True
    assert result["service"] == "payment-service"
    assert result["source"] == "payment_service.md"
    assert result["content"] is not None

    assert (
        "Payment Gateway Authentication Failures"
        in result["content"]
    )


def test_auth_service_runbook_is_retrieved():
    result = retrieve_runbook(
        "auth-service"
    )

    assert result["found"] is True
    assert result["service"] == "auth-service"
    assert result["source"] == "auth_service.md"
    assert result["content"] is not None


def test_order_service_runbook_is_retrieved():
    result = retrieve_runbook(
        "order-service"
    )

    assert result["found"] is True
    assert result["service"] == "order-service"
    assert result["source"] == "order_service.md"
    assert result["content"] is not None


def test_unknown_service_returns_safe_miss():
    result = retrieve_runbook(
        "unknown-service"
    )

    assert result["found"] is False
    assert result["service"] == "unknown-service"
    assert result["source"] is None
    assert result["content"] is None