import Link from "next/link";
import { notFound } from "next/navigation";

import { AuditTimeline, WorkflowMeta } from "@/components/workflows/AuditTimeline";
import { StatusBadge } from "@/components/workflows/StatusBadge";
import { WorkflowActions } from "@/components/workflows/WorkflowActions";
import { ApiRequestError, getWorkflow } from "@/lib/api";

export const dynamic = "force-dynamic";

interface WorkflowDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function WorkflowDetailPage({ params }: WorkflowDetailPageProps) {
  const { id } = await params;

  let workflow;
  try {
    workflow = await getWorkflow(id);
  } catch (err) {
    if (err instanceof ApiRequestError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  return (
    <div className="space-y-8">
      <div>
        <Link href="/" className="text-sm font-medium text-slate-600 hover:text-slate-900">
          Back to workflows
        </Link>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">{workflow.title}</h1>
            {workflow.description && (
              <p className="mt-2 max-w-2xl text-sm text-slate-600">{workflow.description}</p>
            )}
          </div>
          <StatusBadge state={workflow.state} />
        </div>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <WorkflowMeta
          ownerId={workflow.owner_id}
          createdAt={workflow.created_at}
          updatedAt={workflow.updated_at}
        />
      </section>

      <WorkflowActions workflowId={workflow.id} state={workflow.state} />

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Audit History</h2>
        <AuditTimeline entries={workflow.audit_entries} />
      </section>
    </div>
  );
}
