# Workflow Approval Engine

Full-stack workflow orchestration application with a FastAPI backend, PostgreSQL persistence, and a Next.js dashboard.

## Features

- Create approval workflows
- Approve or reject pending workflows
- State-machine driven transitions (`PENDING` → `APPROVED` or `REJECTED`)
- Atomic audit logging for every state change
- Dashboard with status badges and audit history
- REST API with interactive Swagger docs
- Docker Compose for local full-stack development
- GitHub Actions CI for backend tests and frontend build

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python, FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Frontend | Next.js, TypeScript, Tailwind CSS |
| Infrastructure | Docker, Docker Compose, GitHub Actions |

## Architecture

```
Browser → Next.js (port 3000) → FastAPI (port 8000) → PostgreSQL (port 5432)
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for more detail.

## Workflow States

```
PENDING → APPROVED
PENDING → REJECTED
```

All other transitions are rejected by the state machine.

## Quick Start (Docker)

```bash
docker compose up --build
```

Services:

- Frontend dashboard: http://localhost:3000
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL 14+ (or use Docker for the database only)

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/workflows
export CORS_ORIGINS=http://localhost:3000

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

### Environment Variables

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `DATABASE_URL` | Backend | `postgresql://postgres:postgres@localhost:5432/workflows` | PostgreSQL connection string |
| `CORS_ORIGINS` | Backend | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://localhost:8000` | FastAPI base URL |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/workflows` | Create workflow |
| `GET` | `/workflows` | List workflows (optional `?state=PENDING`) |
| `GET` | `/workflows/{id}` | Workflow detail with audit log |
| `POST` | `/workflows/{id}/approve` | Approve pending workflow |
| `POST` | `/workflows/{id}/reject` | Reject pending workflow |

## Testing

### Backend

```bash
python -m pytest tests -v
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

## Frontend Usage

1. Set **Acting as** in the header to identify the current user (stored in browser local storage).
2. Create a workflow from **New Workflow**.
3. Open a workflow detail page to approve or reject it.
4. Review the audit timeline for a complete history of state changes.

Authentication is not implemented in this portfolio version. The UI sends `owner_id` and `actor_id` values to the API as plain strings.

## Roadmap

- Multi-stage approval chains
- Role-based access control
- Email / Slack notifications
- AI-powered approval routing
