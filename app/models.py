"""
ORM models for workflows and audit_log.
 
Design decision: audit_log is a separate table (not a jsonb column on workflows)
so that transition history is queryable without JSON parsing.
Every audit row is written in the same transaction as the state update —
this is the atomicity guarantee that makes the audit log trustworthy.
"""
 
from datetime import datetime, timezone
import uuid
 
from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Index, String, Text
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
 
