from app.infrastructure.mock_environment import MOCK_SERVICES


def get_service_health(service_name: str) -> dict:
    """
    Get the current operational health of a service
    from the shared Aegis mock environment.
    """

    service = MOCK_SERVICES.get(service_name)

    if service is None:
        return {
            "status": "unknown",
            "error_rate": None,
            "latency_ms": None
        }

    return {
        "status": service["status"],
        "error_rate": service["error_rate"],
        "latency_ms": service["latency_ms"]
    }