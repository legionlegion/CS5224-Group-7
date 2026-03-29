"use client";

import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { LeaderboardList } from "@/components/leaderboard/LeaderboardList";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { getLeaderboard, getUserGlobalRank, getUserRegion, getUserRegionRank } from "@/lib/api";
import { LeaderboardEntry, LeaderboardRegionId } from "@/lib/types";

const regionTabs: Array<{ id: LeaderboardRegionId; label: string }> = [
  { id: "all", label: "All" },
  { id: "central", label: "Central" },
  { id: "east", label: "East" },
  { id: "west", label: "West" },
  { id: "north", label: "North" },
  { id: "north-east", label: "North East" }
];

export default function LeaderboardPage() {
  const [userRegion, setUserRegion] = useState<LeaderboardRegionId>("all");
  const [region, setRegion] = useState<LeaderboardRegionId>("all");
  const [isRegionInitialized, setIsRegionInitialized] = useState(false);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [currentUserRank, setCurrentUserRank] = useState<number | null>(null);
  const [rankLoading, setRankLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isCancelled = false;

    const initializeRegion = async () => {
      try {
        const userRegion = await getUserRegion();
        if (!isCancelled) {
          setUserRegion(userRegion);
          setRegion(userRegion);
        }
      } catch {
        if (!isCancelled) {
          setUserRegion("all");
          setRegion("all");
        }
      } finally {
        if (!isCancelled) {
          setIsRegionInitialized(true);
        }
      }
    };

    initializeRegion();

    return () => {
      isCancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!isRegionInitialized) {
      return;
    }

    const loadLeaderboard = async () => {
      setLoading(true);
      setError("");

      try {
        const results = await getLeaderboard(region, 10);
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
  }, [region, isRegionInitialized]);

  const showUserRank = region === "all" || region === userRegion;

  useEffect(() => {
    if (!isRegionInitialized) {
      return;
    }

    if (!showUserRank) {
      setCurrentUserRank(null);
      setRankLoading(false);
      return;
    }

    let isCancelled = false;

    const loadCurrentUserRank = async () => {
      setRankLoading(true);
      try {
        const rank = region === "all" ? await getUserGlobalRank() : await getUserRegionRank();
        if (!isCancelled) {
          setCurrentUserRank(rank);
        }
      } catch {
        if (!isCancelled) {
          setCurrentUserRank(null);
        }
      } finally {
        if (!isCancelled) {
          setRankLoading(false);
        }
      }
    };

    loadCurrentUserRank();

    return () => {
      isCancelled = true;
    };
  }, [region, userRegion, isRegionInitialized, showUserRank]);

  const selectedRegionLabel = regionTabs.find((tab) => tab.id === region)?.label || "All";

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/80 p-4 shadow-card">
          <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Leaderboard</p>
          <div className="mt-2">
            <h2 className="text-2xl font-semibold">See where you stand</h2>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 rounded-2xl bg-canvas p-2 sm:grid-cols-3 lg:grid-cols-6">
              {regionTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setRegion(tab.id)}
                  className={`inline-flex w-full items-center justify-center rounded-full px-3 py-2 text-center text-sm font-semibold leading-none ${
                    region === tab.id ? "bg-moss text-white" : "text-ink/70"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
          </div>
        </div>

        {showUserRank ? (
          <div className="rounded-3xl bg-white/85 px-4 py-3 shadow-card">
            <p className="text-xs uppercase tracking-[0.16em] text-ink/60">Your rank</p>
            <p className="mt-1 text-lg font-semibold text-ink">
              {rankLoading ? "Loading..." : currentUserRank && currentUserRank > 0 ? `#${currentUserRank}` : "N/A"}
              <span className="ml-2 text-sm font-medium text-ink/60">in {selectedRegionLabel}</span>
            </p>
          </div>
        ) : null}

        {loading ? <LoadingState label="Loading leaderboard..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error ? <LeaderboardList entries={entries} /> : null}
      </section>
    </AuthGuard>
  );
}
