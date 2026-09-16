def search_logs(service_name: str, query: str) -> list[dict]:
    """
    Search operational logs for a service.

    Args:
        service_name: Name of the service whose logs should be searched.
        query: Text or log level to search for.

    Returns:
        Matching log entries.
    """

    mock_logs = {
        "payment-service": [
            {
                "timestamp": "2026-09-16T08:32:14",
                "level": "ERROR",
                "message": "Payment gateway authentication failed"
            },
            {
                "timestamp": "2026-09-16T08:33:02",
                "level": "ERROR",
                "message": "Invalid API credential for payment gateway"
            },
            {
                "timestamp": "2026-09-16T08:35:41",
                "level": "WARN",
                "message": "Payment request retry limit reached"
            }
        ],
        "auth-service": [
            {
                "timestamp": "2026-09-16T08:31:00",
                "level": "INFO",
                "message": "Authentication request completed successfully"
            }
        ]
    }

    logs = mock_logs.get(service_name, [])

    query = query.lower()

    return [
        log
        for log in logs
        if query in log["message"].lower()
        or query == log["level"].lower()
    ]