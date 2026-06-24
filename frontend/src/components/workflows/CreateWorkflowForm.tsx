"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { useUserIdentity } from "@/hooks/useUserIdentity";
import { ApiRequestError, createWorkflow } from "@/lib/api";

export function CreateWorkflowForm() {
  const router = useRouter();
  const { userId, isReady } = useUserIdentity();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isReady) {
      setOwnerId(userId);
    }
  }, [isReady, userId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const workflow = await createWorkflow({
        title: title.trim(),
        description: description.trim() || undefined,
        owner_id: ownerId.trim(),
      });
      router.push(`/workflows/${workflow.id}`);
    } catch (err) {
      const message =
        err instanceof ApiRequestError ? err.message : "Failed to create workflow";
      setError(message);
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-xl border border-slate-200 bg-white p-6">
      {error && <Alert variant="error">{error}</Alert>}

      <Input
        label="Title"
        name="title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Expense report approval"
        maxLength={200}
        required
      />

      <Textarea
        label="Description"
        name="description"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Optional details about this workflow"
        rows={4}
      />

      <Input
        label="Owner ID"
        name="owner_id"
        value={ownerId}
        onChange={(event) => setOwnerId(event.target.value)}
        placeholder="alice"
        required
      />

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create Workflow"}
        </Button>
        <Button type="button" variant="secondary" onClick={() => router.push("/")}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
