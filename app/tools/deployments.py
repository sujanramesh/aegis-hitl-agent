def get_recent_deployments(service_name: str) -> list[dict]:
    """
    Get recent deployments for a service.

    Args:
        service_name: Name of the service to inspect.

    Returns:
        Recent deployment versions, timestamps, and statuses.
    """

    mock_deployments = {
        "payment-service": [
            {
                "version": "v2.14",
                "deployed_at": "2026-09-16T08:30:00",
                "status": "completed"
            },
            {
                "version": "v2.13",
                "deployed_at": "2026-09-12T14:20:00",
                "status": "completed"
            }
        ],
        "auth-service": [
            {
                "version": "v1.8",
                "deployed_at": "2026-09-14T11:00:00",
                "status": "completed"
            }
        ],
        "order-service": []
    }

    return mock_deployments.get(service_name, [])