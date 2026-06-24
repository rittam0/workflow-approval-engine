import { API_BASE_URL } from "./constants";
import type {
  ApiError,
  TransitionPayload,
  Workflow,
  WorkflowCreatePayload,
  WorkflowDetail,
  WorkflowState,
} from "./types";

export class ApiRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as ApiError;
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiRequestError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function listWorkflows(state?: WorkflowState): Promise<Workflow[]> {
  const query = state ? `?state=${state}` : "";
  return request<Workflow[]>(`/workflows${query}`);
}

export function getWorkflow(id: string): Promise<WorkflowDetail> {
  return request<WorkflowDetail>(`/workflows/${id}`);
}

export function createWorkflow(payload: WorkflowCreatePayload): Promise<Workflow> {
  return request<Workflow>("/workflows", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function approveWorkflow(
  id: string,
  payload: TransitionPayload
): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}/approve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function rejectWorkflow(
  id: string,
  payload: TransitionPayload
): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}/reject`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
