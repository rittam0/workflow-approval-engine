"use client";

import { WORKFLOW_STATES } from "@/lib/constants";
import type { WorkflowState } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StateFilterProps {
  value: WorkflowState | "ALL";
  onChange: (value: WorkflowState | "ALL") => void;
}

const filters: Array<{ value: WorkflowState | "ALL"; label: string }> = [
  { value: "ALL", label: "All" },
  ...WORKFLOW_STATES.map((state) => ({
    value: state,
    label: state.charAt(0) + state.slice(1).toLowerCase(),
  })),
];

export function StateFilter({ value, onChange }: StateFilterProps) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Filter workflows by state">
      {filters.map((filter) => (
        <button
          key={filter.value}
          type="button"
          role="tab"
          aria-selected={value === filter.value}
          onClick={() => onChange(filter.value)}
          className={cn(
            "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
            value === filter.value
              ? "bg-slate-900 text-white"
              : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"
          )}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}
