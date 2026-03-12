"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Shared admin authentication guard.
 *
 * Checks localStorage for a valid admin user session on mount.
 * Redirects to /auth/login if no session, or / if non-admin.
 *
 * Usage: call `useAdminAuth()` at the top of every admin page component.
 */
export function useAdminAuth() {
  const router = useRouter();

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (!userStr) {
      router.push("/auth/login");
      return;
    }
    try {
      const userData = JSON.parse(userStr);
      if (userData.role !== "admin") {
        router.push("/");
      }
    } catch {
      router.push("/auth/login");
    }
  }, [router]);
}
