import { CreateAIActionForm } from "@/components/ai-actions/CreateAIActionForm";

export default function NewAIActionPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Propose an AI action</h1>
        <p className="mt-1 text-sm text-slate-500">
          The action remains blocked until a human approves it.
        </p>
      </div>
      <CreateAIActionForm />
    </div>
  );
}
