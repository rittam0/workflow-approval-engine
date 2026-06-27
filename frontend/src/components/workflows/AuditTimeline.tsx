import type { AuditEntry } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

interface AuditTimelineProps {
  entries: AuditEntry[];
}

export function AuditTimeline({ entries }: AuditTimelineProps) {
  if (entries.length === 0) {
    return (
      <p className="text-sm text-slate-500">No audit entries recorded yet.</p>
    );
  }

  return (
    <ol className="space-y-4">
      {entries.map((entry) => (
        <li
          key={entry.id}
          className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-slate-900">{entry.actor_id}</span>
            <span className="text-sm text-slate-500">/</span>
            <span className="text-sm text-slate-600">
              {entry.from_state} to {entry.to_state}
            </span>
          </div>
          {entry.reason && (
            <p className="mt-2 text-sm text-slate-600">{entry.reason}</p>
          )}
          <p className="mt-2 text-xs text-slate-500">{formatDateTime(entry.timestamp)}</p>
        </li>
      ))}
    </ol>
  );
}

interface WorkflowMetaProps {
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}

export function WorkflowMeta({ ownerId, createdAt, updatedAt }: WorkflowMetaProps) {
  return (
    <dl className="grid gap-4 sm:grid-cols-3">
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Owner</dt>
        <dd className="mt-1 text-sm text-slate-900">{ownerId}</dd>
      </div>
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Created</dt>
        <dd className="mt-1 text-sm text-slate-900">{formatDateTime(createdAt)}</dd>
      </div>
      <div>
        <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Updated</dt>
        <dd className="mt-1 text-sm text-slate-900">{formatDateTime(updatedAt)}</dd>
      </div>
    </dl>
  );
}
