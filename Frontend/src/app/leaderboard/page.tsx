"use client";

import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { LeaderboardList } from "@/components/leaderboard/LeaderboardList";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { getLeaderboard } from "@/lib/api";
import { LeaderboardEntry, LeaderboardScope } from "@/lib/types";

export default function LeaderboardPage() {
  const { profile } = useAuth();
  const [scope, setScope] = useState<LeaderboardScope>("global");
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadLeaderboard = async () => {
      setLoading(true);
      setError("");

      try {
        const results = await getLeaderboard(profile?.userId, scope, 10);
        setEntries(results);
      } catch (leaderboardError) {
        setError(
          leaderboardError instanceof Error
            ? leaderboardError.message
            : "Unable to load leaderboard."
        );
      } finally {
        setLoading(false);
      }
    };

    loadLeaderboard();
  }, [profile?.userId, scope]);

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/80 p-4 shadow-card">
          <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Leaderboard</p>
          <div className="mt-2 flex items-center justify-between gap-3">
            <h2 className="text-2xl font-semibold">See where you stand</h2>
            <div className="rounded-full bg-canvas p-1">
              {(["global", "local"] as LeaderboardScope[]).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setScope(value)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold capitalize ${
                    scope === value ? "bg-moss text-white" : "text-ink/70"
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
        </div>

        {loading ? <LoadingState label="Loading leaderboard..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error ? <LeaderboardList entries={entries} /> : null}
      </section>
    </AuthGuard>
  );
}
