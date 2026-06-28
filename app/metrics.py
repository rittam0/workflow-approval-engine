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
