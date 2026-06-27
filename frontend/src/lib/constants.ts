export const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.API_INTERNAL_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const DEFAULT_USER_ID = "demo-user";

export const WORKFLOW_STATES = ["PENDING", "APPROVED", "REJECTED"] as const;

export const STATE_LABELS: Record<(typeof WORKFLOW_STATES)[number], string> = {
  PENDING: "Pending",
  APPROVED: "Approved",
  REJECTED: "Rejected",
};

export const STATE_BADGE_STYLES: Record<(typeof WORKFLOW_STATES)[number], string> = {
  PENDING: "bg-amber-100 text-amber-800 ring-amber-200",
  APPROVED: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  REJECTED: "bg-rose-100 text-rose-800 ring-rose-200",
};
