"""Application entrypoint."""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import workflows

# Create tables on startup (Alembic handles this in production;
# this line makes local dev and tests work without running migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Workflow Approval Engine",
    description="State-machine-driven approval workflows with atomic audit logging.",
    version="1.0.0",
)

app.include_router(workflows.router)


@app.get("/health")
def health():
    return {"status": "ok"}
