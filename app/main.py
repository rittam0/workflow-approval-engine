"""Application entrypoint."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import workflows

from prometheus_fastapi_instrumentator import Instrumentator

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows.router)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
).instrument(app).expose(app)

@app.get("/health")
def health():
    return {"status": "ok"}
