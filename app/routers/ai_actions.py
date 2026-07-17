"""Routes used by AI tools to request and check human approval."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import service
from app.database import get_db
from app.schemas import AIActionCreate, AIActionDecision, AIActionResponse


router = APIRouter(prefix="/ai-actions", tags=["AI action approvals"])


@router.post("", response_model=AIActionResponse, status_code=201)
def create_ai_action(payload: AIActionCreate, db: Session = Depends(get_db)):
    return service.create_ai_action(
        db,
        summary=payload.summary,
        action_type=payload.action_type.value,
        target=payload.target,
        payload=payload.payload,
        agent_name=payload.agent_name,
        model_name=payload.model_name,
        rationale=payload.rationale,
        owner_id=payload.owner_id,
    )


@router.get("/{action_id}", response_model=AIActionResponse)
def get_ai_action(action_id: uuid.UUID, db: Session = Depends(get_db)):
    action = service.get_ai_action(db, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="AI action not found")
    return action


@router.get("/{action_id}/decision", response_model=AIActionDecision)
def get_ai_action_decision(action_id: uuid.UUID, db: Session = Depends(get_db)):
    decision = service.get_ai_action_decision(db, action_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="AI action not found")
    return decision
