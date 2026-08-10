"""
ORM models for workflows and audit_log.
 
Design decision: audit_log is a separate table (not a jsonb column on workflows)
so that transition history is queryable without JSON parsing.
Every audit row is written in the same transaction as the state update —
this is the atomicity guarantee that makes the audit log trustworthy.
"""
 
from datetime import datetime, timezone
import uuid
 
from sqlalchemy import (
    Boolean,
    CHAR,
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
 
from app.database import Base
 
 
class GUID(TypeDecorator):
    """Store UUIDs as native PostgreSQL UUIDs, with CHAR fallback for tests."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value if isinstance(value, uuid.UUID) else uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


def utcnow():
    return datetime.now(timezone.utc)
 
 
class Workflow(Base):
    __tablename__ = "workflows"
 
    id          = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title       = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    owner_id    = Column(String(255), nullable=False)
    state       = Column(String(20), nullable=False, default="PENDING")
    created_at  = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
 
    audit_entries = relationship("AuditLog", back_populates="workflow",
                                 order_by="AuditLog.timestamp")
    ai_action = relationship(
        "AIAction",
        back_populates="workflow",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AIAction(Base):
    """An action proposed by an AI tool and guarded by a human workflow."""

    __tablename__ = "ai_actions"

    id           = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workflow_id  = Column(GUID(), ForeignKey("workflows.id"), nullable=False, unique=True)
    action_type  = Column(String(50), nullable=False)
    target       = Column(Text, nullable=False)
    payload      = Column(JSON, nullable=False, default=dict)
    risk_level   = Column(String(20), nullable=False)
    agent_name   = Column(String(255), nullable=False)
    model_name   = Column(String(255), nullable=True)
    rationale    = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    workflow = relationship("Workflow", back_populates="ai_action")

    __table_args__ = (
        Index("idx_ai_actions_workflow_id", "workflow_id"),
        Index("idx_ai_actions_risk_level", "risk_level"),
    )
 
 
class AuditLog(Base):
    __tablename__ = "audit_log"
 
    id          = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(GUID(), ForeignKey("workflows.id"), nullable=False)
    from_state  = Column(String(20), nullable=False)
    to_state    = Column(String(20), nullable=False)
    actor_id    = Column(String(255), nullable=False)
    reason      = Column(Text, nullable=True)
    timestamp   = Column(DateTime(timezone=True), default=utcnow, nullable=False)
 
    workflow = relationship("Workflow", back_populates="audit_entries")
 
    __table_args__ = (
        Index("idx_audit_workflow_id", "workflow_id"),
    )


class ExecutionJob(Base):
    """Transactional outbox row created when a workflow is approved."""

    __tablename__ = "execution_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(GUID(), ForeignKey("workflows.id"), nullable=False)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # A short lease makes PROCESSING jobs recoverable after worker termination.
    claim_token = Column(GUID(), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    simulate_failure = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_execution_jobs_claim", "status", "available_at"),
        Index("idx_execution_jobs_workflow", "workflow_id"),
    )


class ExecutionResult(Base):
    """The harmless downstream effect, deduplicated by idempotency key."""

    __tablename__ = "execution_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("execution_jobs.id"), nullable=False, unique=True)
    workflow_id = Column(GUID(), ForeignKey("workflows.id"), nullable=False)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class ExecutionEvent(Base):
    """Append-only execution history for retries, completion, and dead letters."""

    __tablename__ = "execution_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("execution_jobs.id"), nullable=False)
    workflow_id = Column(GUID(), ForeignKey("workflows.id"), nullable=False)
    event_type = Column(String(30), nullable=False)
    attempt = Column(Integer, nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("idx_execution_events_job", "job_id", "timestamp"),
        UniqueConstraint("job_id", "event_type", "attempt", name="uq_execution_event_attempt"),
    )
 
