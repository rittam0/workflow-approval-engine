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
  ai_action: AIAction | null;
}

export type AIActionType =
  | "SEND_EMAIL"
  | "ISSUE_REFUND"
  | "UPDATE_RECORD"
  | "DEPLOY_CODE"
  | "DELETE_RECORD"
  | "CUSTOM";

export interface AIAction {
  id: string;
  workflow_id: string;
  action_type: AIActionType;
  target: string;
  payload: Record<string, unknown>;
  risk_level: "MEDIUM" | "HIGH" | "CRITICAL";
  agent_name: string;
  model_name: string | null;
  rationale: string | null;
  created_at: string;
}

export interface AIActionCreatePayload {
  summary: string;
  action_type: AIActionType;
  target: string;
  payload: Record<string, unknown>;
  agent_name: string;
  model_name?: string;
  rationale?: string;
  owner_id: string;
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
