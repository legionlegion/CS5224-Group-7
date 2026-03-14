"use client";

import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ProfileStatsCard } from "@/components/profile/ProfileStatsCard";
import { SubmissionHistoryList } from "@/components/profile/SubmissionHistoryList";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { getUserStats } from "@/lib/api";
import { UserStats } from "@/lib/types";

export default function ProfilePage() {
  const { profile, logout } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadStats = async () => {
      if (!profile) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const data = await getUserStats();
        setStats(data);
      } catch (statsError) {
        setError(statsError instanceof Error ? statsError.message : "Unable to load profile.");
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [profile]);

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3 rounded-[2rem] bg-white/80 p-4 shadow-card">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Profile</p>
            <h2 className="text-2xl font-semibold">Your progress</h2>
          </div>
          <button
            type="button"
            onClick={() => void logout()}
            className="rounded-full border border-ink/10 px-4 py-2 text-sm font-semibold"
          >
            Logout
          </button>
        </div>

        {loading ? <LoadingState label="Loading profile..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && profile && stats ? (
          <>
            <ProfileStatsCard profile={profile} stats={stats} />
            <div className="space-y-3">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-moss/70">History</p>
                <h3 className="text-xl font-semibold">Submission history</h3>
              </div>
              <SubmissionHistoryList items={stats.submissionHistory} />
            </div>
          </>
        ) : null}
      </section>
    </AuthGuard>
  );
}
