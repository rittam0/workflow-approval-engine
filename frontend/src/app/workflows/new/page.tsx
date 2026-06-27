import { CreateWorkflowForm } from "@/components/workflows/CreateWorkflowForm";

export default function NewWorkflowPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Create Workflow</h1>
        <p className="mt-1 text-sm text-slate-500">
          Submit a new item for approval. It will start in the pending state.
        </p>
      </div>
      <CreateWorkflowForm />
    </div>
  );
}
