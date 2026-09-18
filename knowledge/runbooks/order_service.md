# Order Service Operational Runbook

## Service
order-service

## Order Processing Failures

### Symptoms
- Failed order creation.
- Increased order-processing error rate.
- Elevated latency.
- Dependency or database errors in logs.

### Investigation
1. Check order-service health.
2. Review recent deployments.
3. Search application logs.
4. Identify failing downstream dependencies.
5. Determine whether failures correlate with a deployment or configuration change.

### Remediation
Remediation should be selected based on collected evidence. Potential actions include rollback of a faulty deployment or correction of an identified configuration problem.

### Safety
Consequential operational changes must pass the Aegis risk policy before execution.