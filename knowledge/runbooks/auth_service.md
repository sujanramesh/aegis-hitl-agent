# Authentication Service Operational Runbook

## Service
auth-service

## Authentication Failure Investigation

### Symptoms
- Increased login failures.
- Elevated HTTP 401 or 403 responses.
- Token validation errors.
- Increased authentication latency.

### Investigation
1. Check auth-service health.
2. Review recent deployments.
3. Search logs for token, credential, and authorization errors.
4. Check whether failures correlate with a recent configuration or deployment change.

### Remediation
Potential remediation may include configuration correction, rollback to a known-good deployment, or credential investigation depending on the collected evidence.

### Safety
Consequential configuration changes, credential operations, service restarts, or deployment rollbacks require appropriate authorization.