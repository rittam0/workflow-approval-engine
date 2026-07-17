# AI Action Approval Engine — Architecture

## Objective

Place a human decision between an AI-proposed action and the system that may carry it out. Manual approval requests remain supported through the same workflow engine.

## Current Implementation

### API Layer
- FastAPI REST endpoints
- CORS support for browser clients
- Swagger documentation at `/docs`

### Workflow Engine
- Explicit state machine (`app/fsm.py`)
- Service layer with transactional audit logging
- Pessimistic locking on transitions (`SELECT FOR UPDATE`)

### AI Action Guard
- AI tools submit a proposed action, target, exact payload, model identity, and rationale
- Server-owned policy assigns the risk level; the AI caller cannot lower it
- Every AI action is linked one-to-one with an ordinary approval workflow
- Decision endpoint returns `WAITING_FOR_HUMAN`, `ALLOWED`, or `DENIED`
- Approval and rejection continue to use the existing state machine and audit log

### Persistence Layer
- PostgreSQL via SQLAlchemy
- `workflows` table for current state
- `audit_log` table for immutable transition history
- `ai_actions` table for AI proposal evidence and its linked workflow

### Frontend Layer
- Next.js App Router dashboard
- Workflow list with state filtering and status badges
- Create, approve, and reject flows
- Audit timeline on workflow detail pages
- Typed API client mirroring backend schemas
- AI action submission form and evidence card on the existing workflow detail page

### Infrastructure
- Docker Compose (`db`, `app`, `frontend`)
- GitHub Actions CI (backend pytest + frontend build)

## Architecture Diagram

```
AI Tool ---- submits proposed action ----+
                                         |
Human Reviewer ---- Next.js UI ----------+--> FastAPI API
                                               |
                                               +--> Server-owned risk policy
                                               +--> Approval state machine
                                               +--> PostgreSQL + atomic audit log
                                         |
AI Tool <---- checks allow/deny decision-+
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

### Enforced Execution Permits
Issue short-lived, signed permits that an integrated downstream service validates before carrying out an approved action. The current decision endpoint is the control-plane MVP; callers must integrate it correctly.

### Role-Based Access Control
Authenticated users with approval permissions

### Multi-Stage Approval Chains
Sequential approvers before final state
