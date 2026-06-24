"""Application entrypoint."""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import workflows

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Workflow Approval Engine",
    description="State-machine-driven approval workflows with atomic audit logging.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(workflows.router)


@app.get("/health")
def health():
    return {"status": "ok"}
