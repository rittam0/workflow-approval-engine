import Link from "next/link";

export default function NotFound() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-6 py-12 text-center">
      <h1 className="text-xl font-semibold text-slate-900">Workflow not found</h1>
      <p className="mt-2 text-sm text-slate-500">
        The workflow you are looking for does not exist or was removed.
      </p>
      <Link href="/" className="mt-4 inline-block text-sm font-medium text-slate-900 underline">
        Return to dashboard
      </Link>
    </div>
  );
}
