"use client";

import { useCallback, useEffect, useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { StateFilter } from "@/components/workflows/StateFilter";
import { WorkflowTable } from "@/components/workflows/WorkflowTable";
import { ApiRequestError, listWorkflows } from "@/lib/api";
import type { Workflow, WorkflowState } from "@/lib/types";

export default function DashboardPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [filter, setFilter] = useState<WorkflowState | "ALL">("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWorkflows = useCallback(async (state: WorkflowState | "ALL") => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await listWorkflows(state === "ALL" ? undefined : state);
      setWorkflows(data);
    } catch (err) {
      const message =
        err instanceof ApiRequestError ? err.message : "Failed to load workflows";
      setError(message);
      setWorkflows([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWorkflows(filter);
  }, [filter, loadWorkflows]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Workflows</h1>
        <p className="mt-1 text-sm text-slate-500">
          Review pending requests and track finalized approvals.
        </p>
      </div>

      <StateFilter value={filter} onChange={setFilter} />

      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              key={index}
              className="h-16 animate-pulse rounded-xl bg-slate-200"
              aria-hidden
            />
          ))}
        </div>
      ) : (
        <WorkflowTable workflows={workflows} />
      )}
    </div>
  );
}
