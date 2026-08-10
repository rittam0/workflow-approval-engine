import uuid

from sqlalchemy.orm import Session

from app.fsm import WorkflowState, apply_transition
from app.metrics import (
    ai_action_created_total,
    ai_action_decision_checks_total,
    workflow_created_total,
    workflow_invalid_transition_total,
    workflow_transition_total,
)
from app.models import AIAction, AuditLog, ExecutionJob, Workflow


AI_ACTION_RISK = {
    "SEND_EMAIL": "MEDIUM",
    "ISSUE_REFUND": "HIGH",
    "UPDATE_RECORD": "HIGH",
    "DEPLOY_CODE": "CRITICAL",
    "DELETE_RECORD": "CRITICAL",
    "CUSTOM": "HIGH",
}

def get_workflow(db: Session, workflow_id: uuid.UUID) -> Workflow | None:
    return db.query(Workflow).filter(Workflow.id == workflow_id).first()


def list_workflows(db: Session, state: str | None = None) -> list[Workflow]:
    q = db.query(Workflow)
    if state:
        q = q.filter(Workflow.state == state.upper())
    return q.order_by(Workflow.created_at.desc()).all()


def get_execution_job(db: Session, workflow_id: uuid.UUID) -> ExecutionJob | None:
    return db.query(ExecutionJob).filter(ExecutionJob.workflow_id == workflow_id).first()


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


def create_ai_action(
    db: Session,
    *,
    summary: str,
    action_type: str,
    target: str,
    payload: dict,
    agent_name: str,
    model_name: str | None,
    rationale: str | None,
    owner_id: str,
) -> AIAction:
    """Create an AI proposal and its human approval request atomically."""
    risk_level = AI_ACTION_RISK[action_type]
    workflow = Workflow(
        title=summary,
        description=f"{agent_name} proposes {action_type.lower().replace('_', ' ')} on {target}",
        owner_id=owner_id,
    )
    db.add(workflow)
    db.flush()

    action = AIAction(
        workflow_id=workflow.id,
        action_type=action_type,
        target=target,
        payload=payload,
        risk_level=risk_level,
        agent_name=agent_name,
        model_name=model_name,
        rationale=rationale,
    )
    db.add(action)

    _write_audit(
        db,
        workflow.id,
        from_state="—",
        to_state="PENDING",
        actor_id=agent_name,
        reason="AI-proposed action submitted for human approval",
    )

    db.commit()
    workflow_created_total.inc()
    ai_action_created_total.labels(
        action_type=action_type,
        risk_level=risk_level,
    ).inc()
    db.refresh(action)
    return action


def get_ai_action(db: Session, action_id: uuid.UUID) -> AIAction | None:
    return db.query(AIAction).filter(AIAction.id == action_id).first()


def get_ai_action_decision(db: Session, action_id: uuid.UUID) -> dict | None:
    action = get_ai_action(db, action_id)
    if action is None:
        return None

    decisions = {
        "PENDING": ("WAITING_FOR_HUMAN", False),
        "APPROVED": ("ALLOWED", True),
        "REJECTED": ("DENIED", False),
    }
    decision, allowed = decisions[action.workflow.state]
    ai_action_decision_checks_total.labels(decision=decision).inc()
    return {
        "action_id": action.id,
        "workflow_id": action.workflow_id,
        "workflow_state": action.workflow.state,
        "decision": decision,
        "allowed": allowed,
    }


def transition_workflow(
    db: Session,
    workflow_id: uuid.UUID,
    action: str,
    actor_id: str,
    reason: str | None = None,
    simulate_failure: bool = False,
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

    if next_state is WorkflowState.APPROVED:
        db.add(
            ExecutionJob(
                workflow_id=workflow.id,
                idempotency_key=f"workflow-execution:{workflow.id}",
                simulate_failure=simulate_failure,
            )
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
