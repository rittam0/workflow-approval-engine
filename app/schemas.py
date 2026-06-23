"""Pydantic schemas — request validation and response serialization."""
 
import uuid
from datetime import datetime
from typing import Optional
 
from pydantic import BaseModel, Field
 
 
# ── Requests ──────────────────────────────────────────────────────────────────
 
class WorkflowCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    owner_id: str = Field(..., min_length=1)
 
 
class TransitionRequest(BaseModel):
    actor_id: str = Field(..., min_length=1)
    reason: Optional[str] = None
 
 
# ── Responses ─────────────────────────────────────────────────────────────────
 
class AuditEntry(BaseModel):
    id: uuid.UUID
    from_state: str
    to_state: str
    actor_id: str
    reason: Optional[str]
    timestamp: datetime
 
    model_config = {"from_attributes": True}
 
 
class WorkflowResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    owner_id: str
    state: str
    created_at: datetime
    updated_at: datetime
 
    model_config = {"from_attributes": True}
 
 
class WorkflowDetail(WorkflowResponse):
    """Full detail view — includes audit history."""
    audit_entries: list[AuditEntry] = []
