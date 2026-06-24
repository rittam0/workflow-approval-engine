"use client";

import { useCallback, useEffect, useState } from "react";

import { DEFAULT_USER_ID } from "@/lib/constants";

const STORAGE_KEY = "workflow-user-id";

export function useUserIdentity() {
  const [userId, setUserIdState] = useState(DEFAULT_USER_ID);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setUserIdState(stored);
    }
    setIsReady(true);
  }, []);

  const setUserId = useCallback((value: string) => {
    setUserIdState(value);
    window.localStorage.setItem(STORAGE_KEY, value);
  }, []);

  return { userId, setUserId, isReady };
}
