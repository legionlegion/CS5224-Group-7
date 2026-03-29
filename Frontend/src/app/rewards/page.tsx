"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { SubmissionHistoryList } from "@/components/profile/SubmissionHistoryList";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { getUserStats, getUserTransactions } from "@/lib/api";
import { SubmissionHistoryItem } from "@/lib/types";

export default function RewardsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [logs, setLogs] = useState<SubmissionHistoryItem[]>([]);
  const [totalPoints, setTotalPoints] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    const loadRewardsData = async () => {
      setLoading(true);
      setError("");

      try {
        const [stats, transactions] = await Promise.all([
          getUserStats(),
          getUserTransactions()
        ]);

        // Rewards page is explicitly successful logs only.
        const successfulLogs = transactions.filter((item) => item.pointsEarned > 0);
        setLogs(successfulLogs);
        setTotalPoints(stats.totalPoints);
      } catch (loadError) {
        setError(
          loadError instanceof Error ? loadError.message : "Unable to load rewards data."
        );
      } finally {
        setLoading(false);
      }
    };

    void loadRewardsData();
  }, [authLoading, isAuthenticated]);

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/80 p-4 shadow-card">
          <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Rewards</p>
          <h2 className="text-2xl font-semibold">Your successful recycling logs</h2>
          <p className="mt-2 text-sm text-ink/70">
            Summary based on your account transactions and current points balance.
          </p>
        </div>

        {loading ? <LoadingState label="Loading rewards..." /> : null}
        {error ? <ErrorState title="Unable to load rewards" message={error} /> : null}

        {!loading && !error ? (
          <div className="grid grid-cols-2 gap-3 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-card">
            <SummaryStat label="Total Points" value={String(totalPoints)} />
            <SummaryStat label="Successful Logs" value={String(logs.length)} />
          </div>
        ) : null}

        {!loading && !error && logs.length ? (
          <SubmissionHistoryList items={logs} />
        ) : null}

        {!loading && !error && !logs.length ? (
          <ErrorState
            title="No successful logs yet"
            message="Complete a successful verification on the Log tab to start earning points."
            action={
              <Link
                href="/log"
                className="inline-flex rounded-full bg-moss px-4 py-2 text-sm font-semibold text-white"
              >
                Go to Log
              </Link>
            }
          />
        ) : null}
      </section>
    </AuthGuard>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-canvas p-3">
      <p className="text-xs uppercase tracking-[0.15em] text-moss/70">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
