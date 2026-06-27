"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import { useUserIdentity } from "@/hooks/useUserIdentity";
import { ApiRequestError, approveWorkflow, rejectWorkflow } from "@/lib/api";
import type { WorkflowState } from "@/lib/types";

interface WorkflowActionsProps {
  workflowId: string;
  state: WorkflowState;
}

export function WorkflowActions({ workflowId, state }: WorkflowActionsProps) {
  const router = useRouter();
  const { userId } = useUserIdentity();
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<"approve" | "reject" | null>(null);

  if (state !== "PENDING") {
    return (
      <Alert>
        This workflow is {state.toLowerCase()} and can no longer be changed.
      </Alert>
    );
  }

  async function handleAction(action: "approve" | "reject") {
    setError(null);
    setPendingAction(action);

    try {
      const payload = {
        actor_id: userId.trim() || "demo-user",
        reason: reason.trim() || undefined,
      };

      if (action === "approve") {
        await approveWorkflow(workflowId, payload);
      } else {
        await rejectWorkflow(workflowId, payload);
      }

      router.refresh();
      setReason("");
    } catch (err) {
      const message =
        err instanceof ApiRequestError ? err.message : "Failed to update workflow";
      setError(message);
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Actions</h2>
        <p className="mt-1 text-sm text-slate-500">
          Approve or reject this workflow. Actions are recorded in the audit log.
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <Textarea
        label="Reason (optional)"
        name="reason"
        value={reason}
        onChange={(event) => setReason(event.target.value)}
        placeholder="Add context for this decision"
        rows={3}
      />

      <div className="flex flex-wrap gap-3">
        <Button
          variant="success"
          disabled={pendingAction !== null}
          onClick={() => handleAction("approve")}
        >
          {pendingAction === "approve" ? "Approving..." : "Approve"}
        </Button>
        <Button
          variant="danger"
          disabled={pendingAction !== null}
          onClick={() => handleAction("reject")}
        >
          {pendingAction === "reject" ? "Rejecting..." : "Reject"}
        </Button>
      </div>
    </div>
  );
}
