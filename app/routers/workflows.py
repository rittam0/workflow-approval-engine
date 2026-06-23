"""
Workflow routes.
Routes do three things only: validate input, call service, return response.
No business logic here — that lives in service.py.
"""
 
import uuid
from typing import Optional
 
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
 
from app import service
from app.database import get_db
from app.schemas import TransitionRequest, WorkflowCreate, WorkflowDetail, WorkflowResponse
 
router = APIRouter(prefix="/workflows", tags=["workflows"])
 
 
@router.post("", response_model=WorkflowResponse, status_code=201)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    return service.create_workflow(
        db, title=payload.title, description=payload.description, owner_id=payload.owner_id
    )
 
 
@router.get("", response_model=list[WorkflowResponse])
def list_workflows(
    state: Optional[str] = Query(None, description="Filter by state: PENDING, APPROVED, REJECTED"),
    db: Session = Depends(get_db),
):
    return service.list_workflows(db, state=state)
 
 
@router.get("/{workflow_id}", response_model=WorkflowDetail)
def get_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    workflow = service.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
 
 
@router.post("/{workflow_id}/approve", response_model=WorkflowResponse)
def approve_workflow(
    workflow_id: uuid.UUID, payload: TransitionRequest, db: Session = Depends(get_db)
):
    return _transition(db, workflow_id, "approve", payload)
 
 
@router.post("/{workflow_id}/reject", response_model=WorkflowResponse)
def reject_workflow(
    workflow_id: uuid.UUID, payload: TransitionRequest, db: Session = Depends(get_db)
):
    return _transition(db, workflow_id, "reject", payload)
 
 
# ── Internal ──────────────────────────────────────────────────────────────────
 
def _transition(db, workflow_id, action, payload):
    try:
        return service.transition_workflow(
            db, workflow_id=workflow_id, action=action,
            actor_id=payload.actor_id, reason=payload.reason,
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
