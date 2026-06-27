"use client";

import { Input } from "@/components/ui/Input";
import { useUserIdentity } from "@/hooks/useUserIdentity";

export function UserIdentity() {
  const { userId, setUserId, isReady } = useUserIdentity();

  if (!isReady) {
    return (
      <div className="h-10 w-48 animate-pulse rounded-lg bg-slate-200" aria-hidden />
    );
  }

  return (
    <Input
      label="Acting as"
      name="user-id"
      value={userId}
      onChange={(event) => setUserId(event.target.value)}
      placeholder="Enter user ID"
      className="w-full sm:w-48"
    />
  );
}
