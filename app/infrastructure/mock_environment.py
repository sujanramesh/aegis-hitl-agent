MOCK_SERVICES = {
    "payment-service": {
        "version": "v2.14",
        "status": "degraded",
        "error_rate": 17.3,
        "latency_ms": 840
    },
    "auth-service": {
        "version": "v1.8",
        "status": "healthy",
        "error_rate": 0.4,
        "latency_ms": 120
    },
    "order-service": {
        "version": "v1.5",
        "status": "healthy",
        "error_rate": 0.8,
        "latency_ms": 180
    }
}


def rollback_service(
    service_name: str,
    from_version: str,
    to_version: str
) -> dict:
    """
    Simulate a deployment rollback in the controlled
    Aegis mock environment.
    """

    service = MOCK_SERVICES.get(service_name)

    if service is None:
        return {
            "success": False,
            "message": "Service not found."
        }

    if service["version"] != from_version:
        return {
            "success": False,
            "message": (
                f"Version mismatch. Expected {from_version}, "
                f"but service is running {service['version']}."
            )
        }

    service["version"] = to_version
    service["status"] = "healthy"
    service["error_rate"] = 0.5
    service["latency_ms"] = 150

    return {
        "success": True,
        "service": service_name,
        "from_version": from_version,
        "to_version": to_version,
        "message": (
            f"Mock rollback completed: "
            f"{from_version} -> {to_version}"
        )
    }