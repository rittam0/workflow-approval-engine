import type { AIAction } from "@/lib/types";

const RISK_STYLES = {
  MEDIUM: "bg-amber-100 text-amber-800",
  HIGH: "bg-orange-100 text-orange-800",
  CRITICAL: "bg-rose-100 text-rose-800",
};

export function AIActionCard({ action }: { action: AIAction }) {
  return (
    <section className="space-y-4 rounded-xl border border-violet-200 bg-violet-50 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">AI-proposed action</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">
            {action.action_type.toLowerCase().replaceAll("_", " ")}
          </h2>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${RISK_STYLES[action.risk_level]}`}>
          {action.risk_level} RISK
        </span>
      </div>

      <dl className="grid gap-4 text-sm sm:grid-cols-2">
        <div>
          <dt className="font-medium text-slate-500">Target</dt>
          <dd className="mt-1 break-words text-slate-900">{action.target}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">Proposed by</dt>
          <dd className="mt-1 text-slate-900">
            {action.agent_name}{action.model_name ? ` using ${action.model_name}` : ""}
          </dd>
        </div>
      </dl>

      {action.rationale && (
        <div className="text-sm">
          <p className="font-medium text-slate-500">AI explanation</p>
          <p className="mt-1 text-slate-900">{action.rationale}</p>
        </div>
      )}

      <div className="text-sm">
        <p className="font-medium text-slate-500">Exact details</p>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-lg bg-white p-3 text-xs text-slate-800">
          {JSON.stringify(action.payload, null, 2)}
        </pre>
      </div>
    </section>
  );
}
