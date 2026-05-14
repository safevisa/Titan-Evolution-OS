"use client";

import { useSession } from "next-auth/react";

export function useAuth() {
  const { data: session, status } = useSession();

  return {
    user: session?.user,
    tenantId: session?.tenantId ?? "",
    plan: session?.plan ?? "starter",
    industryPlugin: session?.industryPlugin ?? "payment_fintech",
    role: session?.user?.role ?? "tenant_user",
    isPlatformAdmin: session?.user?.role === "platform_admin",
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
  };
}
