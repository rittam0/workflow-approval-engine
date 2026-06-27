export type WorkflowState = "PENDING" | "APPROVED" | "REJECTED";

export interface AuditEntry {
  id: string;
  from_state: string;
  to_state: string;
  actor_id: string;
  reason: string | null;
  timestamp: string;
}

export interface Workflow {
  id: string;
  title: string;
  description: string | null;
  owner_id: string;
  state: WorkflowState;
  created_at: string;
  updated_at: string;
}

export interface WorkflowDetail extends Workflow {
  audit_entries: AuditEntry[];
}

export interface WorkflowCreatePayload {
  title: string;
  description?: string;
  owner_id: string;
}

export interface TransitionPayload {
  actor_id: string;
  reason?: string;
}

export interface ApiError {
  detail: string;
}
