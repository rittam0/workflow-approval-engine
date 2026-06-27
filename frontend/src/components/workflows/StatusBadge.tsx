import { STATE_BADGE_STYLES, STATE_LABELS } from "@/lib/constants";
import type { WorkflowState } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  state: WorkflowState;
  className?: string;
}

export function StatusBadge({ state, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset",
        STATE_BADGE_STYLES[state],
        className
      )}
    >
      {STATE_LABELS[state]}
    </span>
  );
}
