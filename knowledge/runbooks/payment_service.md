# Payment Service Operational Runbook

## Service
payment-service

## Payment Gateway Authentication Failures

### Symptoms
- Increased payment failure rate.
- Logs contain "Payment gateway authentication failed".
- Logs contain "Invalid API credential for payment gateway".
- Service may enter a degraded state.
- Request latency may increase.

### Investigation
1. Check payment-service health metrics.
2. Review recent deployments.
3. Search logs for authentication and credential errors.
4. Determine whether failures began shortly after a deployment.
5. Verify whether payment gateway credentials or configuration changed.

### Remediation
If authentication failures began immediately after a deployment and the previous version was healthy, a rollback to the previously known-good version may be considered.

A deployment occurring before the incident does not by itself prove that the deployment caused the failure. Credential expiry, credential revocation, configuration errors, or external payment-provider issues should also be considered.

### Safety
Deployment rollback is a consequential operational action and requires human approval before execution.