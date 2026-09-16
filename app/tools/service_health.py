def get_service_health(service_name: str) -> dict:

    mock_services = {
        "payment-service": {
            "status": "degraded",
            "error_rate": 17.3,
            "latency_ms": 840
        },
        "auth-service": {
            "status": "healthy",
            "error_rate": 0.4,
            "latency_ms": 120
        },
        "order-service": {
            "status": "healthy",
            "error_rate": 0.8,
            "latency_ms": 180
        }
    }

    return mock_services.get(
        service_name,
        {
            "status": "unknown",
            "error_rate": None,
            "latency_ms": None
        }
    )