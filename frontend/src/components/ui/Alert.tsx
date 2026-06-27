import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface AlertProps {
  variant?: "error" | "info";
  children: ReactNode;
  className?: string;
}

const variantStyles = {
  error: "border-rose-200 bg-rose-50 text-rose-800",
  info: "border-slate-200 bg-slate-50 text-slate-700",
};

export function Alert({ variant = "info", children, className }: AlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        "rounded-lg border px-4 py-3 text-sm",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </div>
  );
}
