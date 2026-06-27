import Link from "next/link";

import { UserIdentity } from "@/components/layout/UserIdentity";
import { Button } from "@/components/ui/Button";

export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:px-6 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <Link href="/" className="text-lg font-semibold text-slate-900">
            Workflow Approval Engine
          </Link>
          <p className="text-sm text-slate-500">
            Manage approval requests and audit history
          </p>
        </div>
        <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-end md:w-auto">
          <UserIdentity />
          <Link href="/workflows/new">
            <Button className="w-full sm:w-auto">New Workflow</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
