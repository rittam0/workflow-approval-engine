"""
FSM unit tests.
These run with no database, no FastAPI — pure logic.
This is what interviewers mean by "unit testable in isolation."
"""

import pytest
from app.fsm import WorkflowState, apply_transition


# ── Legal transitions ─────────────────────────────────────────────────────────

def test_approve_pending():
    result = apply_transition(WorkflowState.PENDING, "approve")
    assert result == WorkflowState.APPROVED


def test_reject_pending():
    result = apply_transition(WorkflowState.PENDING, "reject")
    assert result == WorkflowState.REJECTED


# ── Illegal transitions ───────────────────────────────────────────────────────

def test_cannot_approve_approved():
    with pytest.raises(ValueError, match="Illegal transition"):
        apply_transition(WorkflowState.APPROVED, "approve")


def test_cannot_reject_approved():
    with pytest.raises(ValueError, match="Illegal transition"):
        apply_transition(WorkflowState.APPROVED, "reject")


def test_cannot_approve_rejected():
    with pytest.raises(ValueError, match="Illegal transition"):
        apply_transition(WorkflowState.REJECTED, "approve")


def test_unknown_action_raises():
    with pytest.raises(ValueError):
        apply_transition(WorkflowState.PENDING, "delete")
