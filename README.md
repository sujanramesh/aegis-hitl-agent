# Aegis

## Production-Grade Human-in-the-Loop AI Agent for Safe Autonomous Operations

Aegis is a production-oriented AI operations agent designed to investigate incidents, reason over operational evidence, propose remediation actions, and safely execute consequential changes under explicit human authorization.

The core principle is:

**The LLM can reason and propose. The application controls policy, authorization, execution, and verification.**

Aegis demonstrates how AI agents can assist with operational incident response while maintaining deterministic safety controls and human oversight.

---

## Overview

Traditional AI agents can combine reasoning and tool execution too closely. This creates a safety problem when an AI system is capable of proposing changes that could affect operational infrastructure.

Aegis separates reasoning from authorization and execution:

```text
Incident
    ↓
Evidence Gathering
    ↓
AI Reasoning
    ↓
Hypothesis
    ↓
Structured Remediation Proposal
    ↓
Deterministic Risk Classification
    ↓
 ┌──────────────────────────────┐
 │ Low Risk                     │
 │ → Automatic Execution        │
 └──────────────────────────────┘
               OR
 ┌──────────────────────────────┐
 │ Consequential / High Risk    │
 │ → Human Authorization        │
 └──────────────────────────────┘
               ↓
        Deterministic Execution
               ↓
        Recovery Verification
               ↓
          Audit Trail
```

---

## Key Features

### Human-in-the-Loop Safety
Consequential remediation actions pause for explicit human authorization before execution.

### Structured Remediation Actions
AI-generated remediation proposals are represented using typed Pydantic models rather than arbitrary free-form execution instructions.

### Deterministic Risk Policy
Risk classification is handled by application logic rather than delegated to the LLM.

### Safe Execution
The executor validates supported actions and checks execution preconditions against the current infrastructure state before performing a remediation.

### Recovery Verification
Successful command execution is not treated as successful incident remediation. Aegis separately verifies whether the affected service has recovered after execution.

### Durable Workflow State
LangGraph checkpointing allows interrupted workflows to resume from the same execution state after human approval.

### RAG-Based Operational Evidence
Relevant operational runbooks are retrieved semantically and supplied to the agent as evidence during incident investigation.

### Authentication and RBAC
JWT authentication and role-based authorization separate viewer, operator, and approver capabilities.

### Auditability
Important operational events are persisted to MySQL so that incident actions and authorization decisions can be reconstructed.

### Observability
Aegis provides structured logging and Prometheus-compatible metrics for operational visibility.

### Containerized Deployment
The backend and frontend can be run together using Docker Compose.

### Automated CI
GitHub Actions automatically validates backend tests, frontend builds, Docker builds, and deployment readiness.

---

## Architecture

```text
                          ┌─────────────────────┐
                          │      Operator       │
                          │   React Frontend    │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │       FastAPI       │
                          │ API + Auth + RBAC   │
                          └──────────┬──────────┘
                                     │
                                     ▼
                     ┌──────────────────────────────┐
                     │         Aegis Agent          │
                     │          LangGraph           │
                     └──────────────┬───────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       Evidence Tools          RAG Retrieval          LLM Reasoning
       Service Health          Runbooks                Gemini
       Deployments
       Logs
              │                     │                     │
              └─────────────────────┴─────────────────────┘
                                    │
                                    ▼
                          Structured Action
                                    │
                                    ▼
                         Deterministic Risk Policy
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                  Low Risk                     High Risk
                     │                             │
                     ▼                             ▼
                Auto Execute                 HITL Approval
                                                   │
                                            Approve / Reject
                                                   │
                                                   ▼
                                             Deterministic
                                               Executor
                                                   │
                                                   ▼
                                            Recovery Check
                                                   │
                                                   ▼
                                              Audit Event
```

---

## End-to-End Workflow

Aegis follows a controlled incident lifecycle.

### 1. Incident Creation
An operator creates an incident containing information such as:
- Affected service
- Incident title
- Incident description
- Operational context

### 2. Evidence Gathering
The agent gathers operational evidence through controlled tools.
Examples include:
- Service health
- Recent deployments
- Operational logs

The agent does not directly modify infrastructure during investigation.

### 3. AI Reasoning
The LLM analyzes the collected evidence and produces a structured hypothesis.

For example:
> Payment requests are experiencing elevated error rates following the latest deployment. A likely cause is an incorrectly configured payment gateway credential or an external credential change.

The hypothesis is treated as reasoning output rather than authorization.

### 4. Remediation Proposal
The agent proposes a structured remediation action.

Example:
> Rollback deployment: `from_version = v2.14`, `to_version = v2.13`

The remediation is represented using typed application models.

### 5. Risk Classification
A deterministic application policy evaluates the proposed action.

For example:
```text
rollback_deployment
        ↓
    HIGH RISK
        ↓
Human authorization required
```

The LLM does not determine whether the action is allowed to execute.

### 6. Human Authorization
For consequential actions, the workflow pauses.

The approver can:
- Approve
- Reject

The decision is recorded with the approver identity and reason.

### 7. Workflow Resumption
After authorization, the LangGraph workflow resumes from its persisted checkpoint. The workflow continues from the existing execution state rather than starting a completely new workflow.

### 8. Deterministic Execution
The executor validates the requested action before making the change.

For a deployment rollback, the executor verifies that the current deployment matches the expected `from_version`. This prevents execution against an unexpected infrastructure state.

### 9. Recovery Verification
A successful rollback command does not automatically mean the incident is resolved.

Aegis performs a separate recovery verification step:

```text
Rollback executed
       ↓
Service health checked
       ↓
Service recovered
       ↓
Incident resolved
```

### 10. Audit
Important lifecycle events are persisted to the audit system.

This provides traceability for:
- Incident creation
- Agent actions
- Remediation proposals
- Approval decisions
- Execution
- Verification
- Resolution

---

## Safety Model

Aegis applies multiple independent safety boundaries:

1. **Structured Actions:** Remediation actions are represented as typed application data rather than arbitrary natural-language commands.
2. **Deterministic Risk Policy:** Risk classification is performed by application logic rather than relying on probabilistic model output.
3. **Explicit Authorization:** High-risk actions require an authenticated approver before execution.
4. **Executor Allowlisting:** The executor only supports explicitly implemented remediation actions.
5. **Precondition Validation:** Execution checks the current infrastructure state against the expected state before applying a change.
6. **Recovery Verification:** The system verifies the resulting service state after execution.
7. **Audit Trail:** Authorization and execution events are persisted for traceability.

---

## RAG and Operational Runbooks

Aegis uses Retrieval-Augmented Generation (RAG) to provide operational context during incident investigation.

The retrieval flow is:

```text
Incident
   ↓
Semantic Retrieval
   ↓
Relevant Runbook Chunks
   ↓
Agent Evidence
   ↓
Reasoning
```

Retrieved runbook information is used as operational evidence during investigation. It does not independently authorize an action. Aegis also provides a deterministic fallback path so that runbook retrieval does not become a single point of failure for the incident workflow.

---

## Workflow State and Checkpointing

Aegis uses LangGraph for workflow orchestration and durable checkpointing. Checkpoint state is stored separately from the MySQL audit database.

```text
LangGraph
   │
   └── SQLite checkpoint
         │
         └── Workflow state / resume

Application
   │
   └── MySQL
         │
         └── Audit events
```

This separation allows workflow execution state and business/audit records to serve different purposes. The HITL workflow can pause for approval and later resume from the persisted checkpoint.

---

## Authentication and RBAC

Aegis uses JWT-based authentication and role-based authorization.

Three primary roles are supported:

| Role | Capabilities |
| :--- | :--- |
| **Viewer** | Inspect operational information |
| **Operator** | Inspect information and create incidents |
| **Approver** | Inspect, create incidents, and approve/reject consequential actions |

The backend remains the authority for authorization decisions. Frontend visibility is not treated as a security boundary.

---

## Observability

Aegis provides operational visibility through:
- Structured logging
- Correlation IDs
- Prometheus-compatible metrics
- Observability summary endpoints
- Audit events
- Incident lifecycle tracking

The observability design intentionally avoids unnecessary high-cardinality metric labels.

---

## Technology Stack

### Backend
- Python 3.13
- FastAPI
- Pydantic
- LangGraph
- Google Gemini
- SQLAlchemy
- MySQL
- SQLite
- PyJWT
- Argon2 password hashing
- Prometheus client

### Frontend
- React
- Vite
- Nginx

### AI / Retrieval
- Gemini
- Gemini embeddings
- Pinecone
- Retrieval-Augmented Generation

### Infrastructure
- Docker
- Docker Compose
- GitHub Actions

---

## Project Structure

```text
aegis-hitl-agent/
│
├── app/
│   ├── agent/
│   ├── api/
│   ├── auth/
│   ├── db/
│   ├── models/
│   ├── observability/
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── knowledge/
│   └── operational runbooks
│
├── tests/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Running Aegis Locally

### Prerequisites

Install:
- Python 3.13+
- Node.js 20+
- Docker Desktop
- MySQL
- Git

You will also need credentials for the configured AI and database services.

### 1. Clone the Repository

```bash
git clone https://github.com/sujanramesh/aegis-hitl-agent.git
cd aegis-hitl-agent
```

### 2. Configure Environment Variables

Create a local `.env` file based on `.env.example`.

The `.env` file contains local configuration and secrets and should not be committed to Git.

### 3. Backend Setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## Running with Docker Compose

Aegis can also be run as a containerized stack:

```bash
docker compose up --build
```

The architecture is:

```text
Browser
   │
   ▼
Frontend / Nginx
   │
   │ /api/*
   ▼
FastAPI Backend
   │
   ├── MySQL
   └── LangGraph SQLite Checkpoint
```

The frontend is exposed through Nginx while backend API requests are reverse-proxied internally.

---

## Testing

Backend tests can be run with:

```bash
python -m pytest
```

The project includes automated tests covering the core backend behavior.

The repository also contains a semantic retrieval integration test that requires a valid external Gemini API credential and is therefore kept separate from the deterministic CI test suite.

---

## Continuous Integration

Aegis uses GitHub Actions for continuous integration.

The CI workflow validates:

```text
Backend Tests
      ↓
Frontend Build
      ↓
Docker Builds
      ↓
Deployment Readiness Gate
```

The pipeline currently includes:
- Backend automated tests
- Frontend production build
- Backend Docker image build
- Frontend Docker image build
- Deployment-readiness validation

This provides an automated quality gate before deployment.

Aegis v1.0.0 currently implements CI and deployment-readiness validation. Cloud deployment/CD is intentionally deferred.

---

## Example Incident

A representative Aegis workflow uses a payment-service incident.

### Incident
Payment Service Error Spike After Deployment

### Investigation
The agent gathers:
- Service health
- Recent deployment information
- Operational logs
- Relevant runbook evidence

### Hypothesis
The latest deployment may have introduced a payment gateway credential/configuration problem.

### Proposed Action
Rollback v2.14 → v2.13

### Risk
HIGH RISK

### HITL
The workflow pauses until an authorized approver explicitly reviews and approves the remediation.

### Execution
The rollback is executed only after authorization and after validating the expected deployment precondition.

### Verification
The service health is checked after the rollback.

### Result
```text
Service recovered
        ↓
Incident resolved
        ↓
Audit trail recorded
```

---

## Engineering Principles

- **AI Proposes, Applications Enforce:** The LLM is responsible for reasoning, not authority.
- **Policy Is Deterministic:** Safety-critical decisions should not depend solely on probabilistic model output.
- **Authorization Is Separate from Reasoning:** A model's recommendation is not equivalent to permission.
- **Execution Is Validated:** The system checks infrastructure state before performing consequential changes.
- **Execution Success Is Not Recovery Success:** A successful command does not automatically mean the underlying incident has been resolved.
- **Human Oversight Is Explicit:** High-risk actions require a deliberate authorization decision.
- **Important Actions Should Be Traceable:** Operational actions and authorization decisions should leave an audit trail.

---

## Current Status

### Aegis v1.0.0

The v1.0.0 release includes:
- Human-in-the-Loop workflow
- LangGraph orchestration
- Durable workflow checkpointing
- Structured remediation actions
- Deterministic risk classification
- Safe remediation execution
- Recovery verification
- RAG-based runbook retrieval
- JWT authentication
- Role-based access control
- MySQL audit trail
- Observability
- React operational dashboard
- Docker and Docker Compose support
- GitHub Actions CI
- Deployment-readiness gate

The complete containerized HITL workflow has been verified from incident creation through human authorization, remediation execution, recovery verification, and incident resolution.

---

## Future Work

Potential future extensions include:
- Cloud deployment
- Continuous delivery
- Additional infrastructure providers
- More remediation action types
- Expanded operational runbooks
- Additional integration tests
- Advanced incident correlation
- Multi-service dependency analysis

Cloud deployment is intentionally outside the scope of the v1.0.0 release.

---

## Version

**Aegis v1.0.0** — Released as a Git tag and GitHub release.

---

## License

This project is currently provided for educational, portfolio, and demonstration purposes.
