"""Pydantic schemas — request validation and response serialization."""
 
import uuid
from datetime import datetime
from enum import Enum
from typing import Any
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
    simulate_failure: bool = False


class AIActionType(str, Enum):
    SEND_EMAIL = "SEND_EMAIL"
    ISSUE_REFUND = "ISSUE_REFUND"
    UPDATE_RECORD = "UPDATE_RECORD"
    DEPLOY_CODE = "DEPLOY_CODE"
    DELETE_RECORD = "DELETE_RECORD"
    CUSTOM = "CUSTOM"


class AIActionCreate(BaseModel):
    summary: str = Field(..., min_length=1, max_length=200)
    action_type: AIActionType
    target: str = Field(..., min_length=1, max_length=500)
    payload: dict[str, Any] = Field(default_factory=dict)
    agent_name: str = Field(..., min_length=1, max_length=255)
    model_name: Optional[str] = Field(None, max_length=255)
    rationale: Optional[str] = None
    owner_id: str = Field(..., min_length=1, max_length=255)

    model_config = {"extra": "forbid", "protected_namespaces": ()}
 
 
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


class AIActionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    action_type: str
    target: str
    payload: dict[str, Any]
    risk_level: str
    agent_name: str
    model_name: Optional[str]
    rationale: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class AIActionDecision(BaseModel):
    action_id: uuid.UUID
    workflow_id: uuid.UUID
    workflow_state: str
    decision: str
    allowed: bool
 
 
class WorkflowDetail(WorkflowResponse):
    """Full detail view — includes audit history."""
    audit_entries: list[AuditEntry] = []
    ai_action: Optional[AIActionResponse] = None


class ExecutionJobResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    idempotency_key: str
    status: str
    attempt_count: int
    available_at: datetime
    last_error: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
