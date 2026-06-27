"""
Workflow state machine.
 
States:   PENDING → APPROVED
          PENDING → REJECTED
 
All other transitions are illegal and raise ValueError.
This module has zero external dependencies — unit testable in isolation.
"""
 
from enum import Enum
 
 
class WorkflowState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
 
 
# Explicit transition table: (from_state, action) → to_state
# Adding a new transition = adding one line here. Nothing else changes.
TRANSITIONS: dict[tuple[WorkflowState, str], WorkflowState] = {
    (WorkflowState.PENDING, "approve"): WorkflowState.APPROVED,
    (WorkflowState.PENDING, "reject"):  WorkflowState.REJECTED,
}
 
 
def apply_transition(current_state: WorkflowState, action: str) -> WorkflowState:
    """
    Returns the next state if the transition is legal.
    Raises ValueError if the transition is illegal.
 
    Interview note: explicit table beats if-else because illegal transitions
    are unrepresentable — you cannot forget to handle a case.
    """
    key = (current_state, action)
    if key not in TRANSITIONS:
        raise ValueError(
            f"Illegal transition: cannot '{action}' a workflow in state '{current_state}'"
        )
    return TRANSITIONS[key]
