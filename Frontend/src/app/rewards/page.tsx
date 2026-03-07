"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { RewardSummaryCard } from "@/components/rewards/RewardSummaryCard";
import { ErrorState } from "@/components/ui/ErrorState";
import { VerifyActivityResult } from "@/lib/types";

const rewardSessionKey = "ecobin-go:latest-reward";

export default function RewardsPage() {
  const [result, setResult] = useState<VerifyActivityResult | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem(rewardSessionKey);
    if (stored) {
      setResult(JSON.parse(stored) as VerifyActivityResult);
    }
  }, []);

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/80 p-4 shadow-card">
          <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Rewards</p>
          <h2 className="text-2xl font-semibold">Your latest result</h2>
        </div>

        {result ? (
          <RewardSummaryCard result={result} />
        ) : (
          <ErrorState
            title="No reward result"
            message="Log a recycling activity first to see your reward summary."
            action={
              <Link
                href="/log"
                className="inline-flex rounded-full bg-moss px-4 py-2 text-sm font-semibold text-white"
              >
                Go to Log
              </Link>
            }
          />
        )}
      </section>
    </AuthGuard>
  );
}
