from pathlib import Path


RUNBOOK_DIRECTORY = (
    Path(__file__).resolve().parents[2]
    / "knowledge"
    / "runbooks"
)

SERVICE_RUNBOOKS = {
    "payment-service": "payment_service.md",
    "auth-service": "auth_service.md",
    "order-service": "order_service.md",
}


def retrieve_runbook(service: str) -> dict:
    """
    Retrieve the operational runbook associated with a service.

    The retrieval layer is intentionally independent from the
    LLM so that retrieved operational knowledge can be inspected
    and tested before being supplied to the reasoning layer.
    """

    filename = SERVICE_RUNBOOKS.get(service)

    if filename is None:
        return {
            "found": False,
            "service": service,
            "source": None,
            "content": None,
        }

    runbook_path = RUNBOOK_DIRECTORY / filename

    if not runbook_path.exists():
        return {
            "found": False,
            "service": service,
            "source": str(runbook_path),
            "content": None,
        }

    content = runbook_path.read_text(
        encoding="utf-8"
    )

    return {
        "found": True,
        "service": service,
        "source": filename,
        "content": content,
    }