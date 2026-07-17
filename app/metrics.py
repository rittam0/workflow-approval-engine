from prometheus_client import Counter

workflow_created_total = Counter(
    "workflow_created_total",
    "Total workflows created",
)

workflow_transition_total = Counter(
    "workflow_transition_total",
    "Total successful workflow transitions",
    ["action", "to_state"],
)

workflow_invalid_transition_total = Counter(
    "workflow_invalid_transition_total",
    "Total failed workflow transition attempts",
    ["action"],
)

ai_action_created_total = Counter(
    "ai_action_created_total",
    "Total actions proposed by AI tools",
    ["action_type", "risk_level"],
)

ai_action_decision_checks_total = Counter(
    "ai_action_decision_checks_total",
    "Total AI action decision checks",
    ["decision"],
)
