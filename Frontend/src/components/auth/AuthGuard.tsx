"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { LoadingState } from "@/components/ui/LoadingState";

const publicRoutes = new Set(["/login", "/signup"]);

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { authUser, isAuthenticated, loading, needsProfileCompletion } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!isAuthenticated && !publicRoutes.has(pathname)) {
      router.replace("/login");
      return;
    }

    if (authUser && needsProfileCompletion && pathname !== "/complete-profile") {
      router.replace("/complete-profile");
      return;
    }

    if (isAuthenticated && !needsProfileCompletion && (pathname === "/login" || pathname === "/signup")) {
      router.replace("/map");
    }
  }, [authUser, isAuthenticated, loading, needsProfileCompletion, pathname, router]);

  if (loading) {
    return <LoadingState label="Checking your session..." />;
  }

  if (!isAuthenticated && !publicRoutes.has(pathname)) {
    return <LoadingState label="Redirecting to login..." />;
  }

  if (authUser && needsProfileCompletion && pathname !== "/complete-profile") {
    return <LoadingState label="Completing your profile..." />;
  }

  return <>{children}</>;
}
