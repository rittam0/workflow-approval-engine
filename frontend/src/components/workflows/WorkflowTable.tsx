import Link from "next/link";

import { StatusBadge } from "@/components/workflows/StatusBadge";
import type { Workflow } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

interface WorkflowTableProps {
  workflows: Workflow[];
}

export function WorkflowTable({ workflows }: WorkflowTableProps) {
  if (workflows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
        <h2 className="text-lg font-medium text-slate-900">No workflows yet</h2>
        <p className="mt-2 text-sm text-slate-500">
          Create your first workflow to start the approval process.
        </p>
        <Link
          href="/workflows/new"
          className="mt-4 inline-block text-sm font-medium text-slate-900 underline"
        >
          Create workflow
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="hidden overflow-hidden rounded-xl border border-slate-200 bg-white md:block">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Title
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Owner
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {workflows.map((workflow) => (
              <tr key={workflow.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link
                    href={`/workflows/${workflow.id}`}
                    className="font-medium text-slate-900 hover:underline"
                  >
                    {workflow.title}
                  </Link>
                  {workflow.description && (
                    <p className="mt-1 line-clamp-1 text-sm text-slate-500">
                      {workflow.description}
                    </p>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-slate-600">{workflow.owner_id}</td>
                <td className="px-4 py-3">
                  <StatusBadge state={workflow.state} />
                </td>
                <td className="px-4 py-3 text-sm text-slate-600">
                  {formatDateTime(workflow.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="space-y-3 md:hidden">
        {workflows.map((workflow) => (
          <Link
            key={workflow.id}
            href={`/workflows/${workflow.id}`}
            className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-medium text-slate-900">{workflow.title}</h3>
                <p className="mt-1 text-sm text-slate-500">{workflow.owner_id}</p>
              </div>
              <StatusBadge state={workflow.state} />
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Created {formatDateTime(workflow.created_at)}
            </p>
          </Link>
        ))}
      </div>
    </>
  );
}
