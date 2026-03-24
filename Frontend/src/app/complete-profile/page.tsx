"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAuth } from "@/context/AuthContext";
import { getRegions } from "@/lib/api";
import { Region } from "@/lib/types";

export default function CompleteProfilePage() {
  const { completeProfile, authUser } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("");
  const [regions, setRegions] = useState<Region[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingRegions, setLoadingRegions] = useState(true);

  useEffect(() => {
    const loadRegions = async () => {
      try {
        const fetchedRegions = await getRegions();
        setRegions(fetchedRegions);
      } catch (err) {
        console.error("Failed to load regions:", err);
        setError(
          err instanceof Error ? err.message : "Unable to load regions."
        );
      } finally {
        setLoadingRegions(false);
      }
    };

    loadRegions();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await completeProfile(username, selectedRegion || undefined);
      router.replace("/map");
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "Unable to complete profile."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <section className="space-y-6">
        <div className="rounded-[2rem] bg-white/85 p-6 shadow-card">
          <p className="text-sm uppercase tracking-[0.25em] text-moss/70">One more step</p>
          <h2 className="mt-2 text-3xl font-semibold">Choose your EcoBin ID</h2>
          <p className="mt-2 text-sm text-ink/70">
            Signed in as {authUser?.email}. Pick a unique username to finish setup.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium">Username</span>
              <input
                required
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-2xl border border-ink/10 bg-canvas px-4 py-3"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium">Select your region</span>
              <select
                value={selectedRegion}
                onChange={(event) => setSelectedRegion(event.target.value)}
                disabled={loadingRegions}
                className="w-full rounded-2xl border border-ink/10 bg-canvas px-4 py-3"
              >
                <option value="">
                  {loadingRegions ? "Loading regions..." : "Choose a region (optional)"}
                </option>
                {regions.map((region) => (
                  <option key={region.id} value={region.id}>
                    {region.name}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white disabled:opacity-70"
            >
              {loading ? "Saving..." : "Complete Profile"}
            </button>
          </form>
        </div>

        {error ? <ErrorState title="Profile update failed" message={error} /> : null}
      </section>
    </AuthGuard>
  );
}
