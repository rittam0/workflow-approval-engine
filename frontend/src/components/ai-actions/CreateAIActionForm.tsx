"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { useUserIdentity } from "@/hooks/useUserIdentity";
import { ApiRequestError, createAIAction } from "@/lib/api";
import type { AIActionType } from "@/lib/types";

const ACTION_TYPES: Array<{ value: AIActionType; label: string }> = [
  { value: "SEND_EMAIL", label: "Send an email" },
  { value: "ISSUE_REFUND", label: "Issue a refund" },
  { value: "UPDATE_RECORD", label: "Change company data" },
  { value: "DEPLOY_CODE", label: "Publish a code change" },
  { value: "DELETE_RECORD", label: "Delete company data" },
  { value: "CUSTOM", label: "Something else" },
];

export function CreateAIActionForm() {
  const router = useRouter();
  const { userId, isReady } = useUserIdentity();
  const [summary, setSummary] = useState("");
  const [actionType, setActionType] = useState<AIActionType>("SEND_EMAIL");
  const [target, setTarget] = useState("");
  const [details, setDetails] = useState("");
  const [agentName, setAgentName] = useState("demo-agent");
  const [modelName, setModelName] = useState("");
  const [rationale, setRationale] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isReady) setOwnerId(userId);
  }, [isReady, userId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const action = await createAIAction({
        summary: summary.trim(),
        action_type: actionType,
        target: target.trim(),
        payload: { instructions: details.trim() },
        agent_name: agentName.trim(),
        model_name: modelName.trim() || undefined,
        rationale: rationale.trim() || undefined,
        owner_id: ownerId.trim(),
      });
      router.push(`/workflows/${action.workflow_id}`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Failed to submit AI action");
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-xl border border-slate-200 bg-white p-6">
      {error && <Alert variant="error">{error}</Alert>}

      <Input
        label="What does the AI want to do?"
        name="summary"
        value={summary}
        onChange={(event) => setSummary(event.target.value)}
        placeholder="Refund a customer after a duplicate payment"
        maxLength={200}
        required
      />

      <label className="block space-y-1.5">
        <span className="text-sm font-medium text-slate-700">Action</span>
        <select
          name="action_type"
          value={actionType}
          onChange={(event) => setActionType(event.target.value as AIActionType)}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200"
        >
          {ACTION_TYPES.map((action) => (
            <option key={action.value} value={action.value}>{action.label}</option>
          ))}
        </select>
      </label>

      <Input
        label="Target"
        name="target"
        value={target}
        onChange={(event) => setTarget(event.target.value)}
        placeholder="Order #1842 or customer@example.com"
        maxLength={500}
        required
      />

      <Textarea
        label="Exact action details"
        name="details"
        value={details}
        onChange={(event) => setDetails(event.target.value)}
        placeholder="Refund INR 2,499 because the payment was recorded twice"
        rows={4}
        required
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="AI tool name"
          name="agent_name"
          value={agentName}
          onChange={(event) => setAgentName(event.target.value)}
          placeholder="refund-agent"
          required
        />
        <Input
          label="Model name (optional)"
          name="model_name"
          value={modelName}
          onChange={(event) => setModelName(event.target.value)}
          placeholder="The model actually used"
        />
      </div>

      <Textarea
        label="Why did the AI propose this? (optional)"
        name="rationale"
        value={rationale}
        onChange={(event) => setRationale(event.target.value)}
        placeholder="It detected two successful payments for the same order"
        rows={3}
      />

      <Input
        label="Human reviewer"
        name="owner_id"
        value={ownerId}
        onChange={(event) => setOwnerId(event.target.value)}
        placeholder="alice"
        required
      />

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Submitting..." : "Request Human Approval"}
        </Button>
        <Button type="button" variant="secondary" onClick={() => router.push("/")}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
