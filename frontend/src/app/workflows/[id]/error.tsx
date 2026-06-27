"use client";

import Link from "next/link";

import { Alert } from "@/components/ui/Alert";

export default function WorkflowDetailError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Alert variant="error">
        Failed to load this workflow. Check that the API is running and try again.
      </Alert>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800"
        >
          Try again
        </button>
        <Link
          href="/"
          className="inline-flex items-center justify-center rounded-lg bg-white px-4 py-2 text-sm font-medium text-slate-700 ring-1 ring-slate-200 transition-colors hover:bg-slate-50"
        >
          Back to workflows
        </Link>
      </div>
    </div>
  );
}
