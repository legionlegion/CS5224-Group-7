"use client";

import { FormEvent, useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ProfileStatsCard } from "@/components/profile/ProfileStatsCard";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { getUserStats } from "@/lib/api";
import { UserStats } from "@/lib/types";

export default function ProfilePage() {
  const { profile, logout, updateUsername } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingProfile, setEditingProfile] = useState(false);
  const [usernameInput, setUsernameInput] = useState("");
  const [savingUsername, setSavingUsername] = useState(false);
  const [usernameError, setUsernameError] = useState("");
  const [usernameSuccess, setUsernameSuccess] = useState("");

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

  useEffect(() => {
    if (!profile) {
      return;
    }
    setUsernameInput(profile.userId);
  }, [profile]);

  const handleUsernameUpdate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUsernameError("");
    setUsernameSuccess("");
    setSavingUsername(true);

    try {
      await updateUsername(usernameInput);
      setUsernameSuccess("Username updated.");
      setEditingProfile(false);
    } catch (updateError) {
      setUsernameError(
        updateError instanceof Error ? updateError.message : "Unable to update username."
      );
    } finally {
      setSavingUsername(false);
    }
  };

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3 rounded-[2rem] bg-white/80 p-4 shadow-card">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Profile</p>
            <h2 className="text-2xl font-semibold">Your progress</h2>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setEditingProfile((current) => !current);
                setUsernameError("");
                setUsernameSuccess("");
                if (profile) {
                  setUsernameInput(profile.userId);
                }
              }}
              className="rounded-full border border-ink/10 px-4 py-2 text-sm font-semibold"
            >
              {editingProfile ? "Cancel" : "Edit Profile"}
            </button>
            <button
              type="button"
              onClick={() => void logout()}
              className="rounded-full border border-ink/10 px-4 py-2 text-sm font-semibold"
            >
              Logout
            </button>
          </div>
        </div>

        {editingProfile ? (
          <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-card">
            <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Edit Username</p>
            <form onSubmit={handleUsernameUpdate} className="mt-4 space-y-3">
              <label className="block">
                <span className="mb-2 block text-sm font-medium">Username</span>
                <input
                  required
                  type="text"
                  value={usernameInput}
                  onChange={(event) => setUsernameInput(event.target.value)}
                  className="w-full rounded-2xl border border-ink/10 bg-canvas px-4 py-3"
                />
              </label>
              <button
                type="submit"
                disabled={savingUsername}
                className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white disabled:opacity-70"
              >
                {savingUsername ? "Saving..." : "Save Username"}
              </button>
            </form>
            {usernameError ? <p className="mt-3 text-sm text-clay">{usernameError}</p> : null}
          </div>
        ) : null}

        {usernameSuccess ? (
          <div className="rounded-3xl border border-moss/20 bg-white/80 p-4 shadow-card">
            <p className="text-sm text-moss">{usernameSuccess}</p>
          </div>
        ) : null}

        {loading ? <LoadingState label="Loading profile..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && profile && stats ? (
          <ProfileStatsCard profile={profile} stats={stats} />
        ) : null}
      </section>
    </AuthGuard>
  );
}
