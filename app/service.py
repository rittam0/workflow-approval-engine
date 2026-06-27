"""
Service layer: all business logic lives here.
Routes call service functions. Service functions call fsm + db.
Neither the FSM nor the DB layer knows about HTTP.
 
The critical pattern: state update + audit log write happen in ONE transaction.
If either fails, both roll back. This is what makes the audit log trustworthy
as a compliance artifact — it cannot diverge from the actual state history.
"""
 
import uuid
from sqlalchemy.orm import Session
 
from app.fsm import WorkflowState, apply_transition
from app.models import AuditLog, Workflow
 
 
# ── Read ──────────────────────────────────────────────────────────────────────
 
def get_workflow(db: Session, workflow_id: uuid.UUID) -> Workflow | None:
    return db.query(Workflow).filter(Workflow.id == workflow_id).first()
 
 
def list_workflows(db: Session, state: str | None = None) -> list[Workflow]:
    q = db.query(Workflow)
    if state:
        q = q.filter(Workflow.state == state.upper())
    return q.order_by(Workflow.created_at.desc()).all()
 
 
# ── Write ─────────────────────────────────────────────────────────────────────
 
def create_workflow(db: Session, title: str, description: str | None, owner_id: str) -> Workflow:
    workflow = Workflow(title=title, description=description, owner_id=owner_id)
    db.add(workflow)
    db.flush()  # get the UUID before commit
 
    _write_audit(db, workflow.id, from_state="—", to_state="PENDING",
                 actor_id=owner_id, reason="Workflow created")
    db.commit()
    db.refresh(workflow)
    return workflow
 
 
def transition_workflow(
    db: Session,
    workflow_id: uuid.UUID,
    action: str,          # "approve" | "reject"
    actor_id: str,
    reason: str | None = None,
) -> Workflow:
    """
    Applies a state transition.
    Raises ValueError for illegal transitions (caught by the route layer).
    State update and audit log are written in a single transaction.
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).with_for_update().first()
    if workflow is None:
        raise LookupError(f"Workflow {workflow_id} not found")
 
    current = WorkflowState(workflow.state)
    next_state = apply_transition(current, action)   # raises ValueError if illegal
 
    from_state = workflow.state
    workflow.state = next_state.value
 
    _write_audit(db, workflow.id, from_state=from_state, to_state=next_state.value,
                 actor_id=actor_id, reason=reason)
 
    db.commit()
    db.refresh(workflow)
    return workflow
 
 
# ── Internal ──────────────────────────────────────────────────────────────────
 
def _write_audit(
    db: Session,
    workflow_id: uuid.UUID,
    from_state: str,
    to_state: str,
    actor_id: str,
    reason: str | None,
) -> None:
    """Always called inside an open transaction — never commits itself."""
    entry = AuditLog(
        workflow_id=workflow_id,
        from_state=from_state,
        to_state=to_state,
        actor_id=actor_id,
        reason=reason,
    )
    db.add(entry)
