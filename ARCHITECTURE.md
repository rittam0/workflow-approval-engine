# Workflow Approval Engine — Architecture

## Objective

Automate enterprise approval workflows with auditability, role-based approvals, and workflow orchestration.

## Current Implementation

### API Layer
- FastAPI REST endpoints
- CORS support for browser clients
- Swagger documentation at `/docs`

### Workflow Engine
- Explicit state machine (`app/fsm.py`)
- Service layer with transactional audit logging
- Pessimistic locking on transitions (`SELECT FOR UPDATE`)

### Persistence Layer
- PostgreSQL via SQLAlchemy
- `workflows` table for current state
- `audit_log` table for immutable transition history

### Frontend Layer
- Next.js App Router dashboard
- Workflow list with state filtering and status badges
- Create, approve, and reject flows
- Audit timeline on workflow detail pages
- Typed API client mirroring backend schemas

### Infrastructure
- Docker Compose (`db`, `app`, `frontend`)
- GitHub Actions CI (backend pytest + frontend build)

## Architecture Diagram

```
User (Browser)
      |
      v
Next.js Frontend (:3000)
      |
      v
FastAPI API (:8000)
      |
      v
Workflow Service
      |
      +--> Approval State Machine
      |
      +--> PostgreSQL
      |
      +--> Audit Logs (same transaction)
```

## State Machine

| Current State | Action | Next State |
|---------------|--------|------------|
| PENDING | approve | APPROVED |
| PENDING | reject | REJECTED |

Illegal transitions raise `ValueError` and return HTTP 409.

## Planned Components

### Notification Service
Email / Slack notifications on approval events

### AI Routing Engine
Classifies requests and determines approval chains automatically

### Role-Based Access Control
Authenticated users with approval permissions

### Multi-Stage Approval Chains
Sequential approvers before final state
