import uuid

from sqlalchemy.orm import Session

from app.fsm import WorkflowState, apply_transition
from app.metrics import (
    workflow_created_total,
    workflow_invalid_transition_total,
    workflow_transition_total,
)
from app.models import AuditLog, Workflow


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Workflow | None:
    return db.query(Workflow).filter(Workflow.id == workflow_id).first()


def list_workflows(db: Session, state: str | None = None) -> list[Workflow]:
    q = db.query(Workflow)
    if state:
        q = q.filter(Workflow.state == state.upper())
    return q.order_by(Workflow.created_at.desc()).all()


def create_workflow(db: Session, title: str, description: str | None, owner_id: str) -> Workflow:
    workflow = Workflow(title=title, description=description, owner_id=owner_id)
    db.add(workflow)
    db.flush()

    _write_audit(
        db,
        workflow.id,
        from_state="—",
        to_state="PENDING",
        actor_id=owner_id,
        reason="Workflow created",
    )

    db.commit()
    workflow_created_total.inc()

    db.refresh(workflow)
    return workflow


def transition_workflow(
    db: Session,
    workflow_id: uuid.UUID,
    action: str,
    actor_id: str,
    reason: str | None = None,
) -> Workflow:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).with_for_update().first()

    if workflow is None:
        raise LookupError(f"Workflow {workflow_id} not found")

    current = WorkflowState(workflow.state)

    try:
        next_state = apply_transition(current, action)
    except ValueError:
        workflow_invalid_transition_total.labels(action=action).inc()
        raise

    from_state = workflow.state
    workflow.state = next_state.value

    _write_audit(
        db,
        workflow.id,
        from_state=from_state,
        to_state=next_state.value,
        actor_id=actor_id,
        reason=reason,
    )

    db.commit()

    workflow_transition_total.labels(
        action=action,
        to_state=next_state.value,
    ).inc()

    db.refresh(workflow)
    return workflow


def _write_audit(
    db: Session,
    workflow_id: uuid.UUID,
    from_state: str,
    to_state: str,
    actor_id: str,
    reason: str | None,
) -> None:
    entry = AuditLog(
        workflow_id=workflow_id,
        from_state=from_state,
        to_state=to_state,
        actor_id=actor_id,
        reason=reason,
    )
    db.add(entry)
