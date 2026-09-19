from prometheus_client import Counter, Histogram


# =========================================================
# HTTP metrics
# =========================================================

HTTP_REQUESTS_TOTAL = Counter(
    "aegis_http_requests_total",
    "Total number of HTTP requests processed by Aegis.",
    [
        "method",
        "path",
        "status_code",
    ],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "aegis_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    [
        "method",
        "path",
    ],
)


# =========================================================
# Incident workflow metrics
# =========================================================

INCIDENTS_TOTAL = Counter(
    "aegis_incidents_total",
    "Total number of incident workflows created.",
    [
        "service",
    ],
)

APPROVAL_REQUESTS_TOTAL = Counter(
    "aegis_approval_requests_total",
    "Total number of incidents requiring human approval.",
    [
        "risk_level",
    ],
)

APPROVAL_DECISIONS_TOTAL = Counter(
    "aegis_approval_decisions_total",
    "Total number of human approval decisions.",
    [
        "decision",
    ],
)


# =========================================================
# Execution metrics
# =========================================================

ACTION_EXECUTIONS_TOTAL = Counter(
    "aegis_action_executions_total",
    "Total number of remediation action executions.",
    [
        "action_type",
        "outcome",
    ],
)

RECOVERY_VERIFICATIONS_TOTAL = Counter(
    "aegis_recovery_verifications_total",
    "Total number of recovery verification attempts.",
    [
        "outcome",
    ],
)


# =========================================================
# AI provider metrics
# =========================================================

LLM_FAILURES_TOTAL = Counter(
    "aegis_llm_failures_total",
    "Total number of LLM provider failures.",
    [
        "provider",
        "reason",
    ],
)


# =========================================================
# Workflow latency
# =========================================================

WORKFLOW_DURATION_SECONDS = Histogram(
    "aegis_workflow_duration_seconds",
    "Duration of Aegis workflow operations.",
    [
        "operation",
    ],
)