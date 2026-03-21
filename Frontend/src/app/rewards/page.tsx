"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { SubmissionHistoryList } from "@/components/profile/SubmissionHistoryList";
import { ErrorState } from "@/components/ui/ErrorState";
import { getSuccessfulLogs } from "@/lib/recyclingHistory";
import { SubmissionHistoryItem } from "@/lib/types";

export default function RewardsPage() {
  const [logs, setLogs] = useState<SubmissionHistoryItem[]>([]);

  useEffect(() => {
    setLogs(getSuccessfulLogs());
  }, []);

  const totalPoints = logs.reduce((sum, item) => sum + item.pointsEarned, 0);

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/80 p-4 shadow-card">
          <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Rewards</p>
          <h2 className="text-2xl font-semibold">Your successful recycling logs</h2>
          <p className="mt-2 text-sm text-ink/70">
            Placeholder summary from your successful submissions in this browser.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-card">
          <SummaryStat label="Total Points Earned" value={String(totalPoints)} />
          <SummaryStat label="Successful Logs" value={String(logs.length)} />
        </div>

        {logs.length ? (
          <SubmissionHistoryList items={logs} />
        ) : (
          <ErrorState
            title="No successful logs yet"
            message="Complete a successful verification on the Log tab to populate this placeholder."
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

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-canvas p-3">
      <p className="text-xs uppercase tracking-[0.15em] text-moss/70">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
