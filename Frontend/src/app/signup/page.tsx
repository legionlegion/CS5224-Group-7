"use client";

import Link from "next/link";
import { FormEvent, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAuth } from "@/context/AuthContext";
import { getRegions } from "@/lib/api";
import type { Region } from "@/lib/types";

export default function SignupPage() {
  const { signup } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [regions, setRegions] = useState<Region[]>([]);
  const [loadingRegions, setLoadingRegions] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadRegions = async () => {
      try {
        setLoadingRegions(true);
        const fetchedRegions = await getRegions();
        setRegions(fetchedRegions);
      } catch (err) {
        console.error("Failed to load regions:", err);
        setRegions([]);
      } finally {
        setLoadingRegions(false);
      }
    };

    loadRegions();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      await signup({ username, email, password, displayName: username, regionId: selectedRegion || undefined });
      router.replace("/map");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to sign up.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <section className="space-y-6">
        <div className="rounded-[2rem] bg-white/80 p-6 shadow-card">
          <p className="text-sm uppercase tracking-[0.25em] text-moss/70">Signup</p>
          <h2 className="mt-2 text-3xl font-semibold">Start earning</h2>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <Input label="Username" type="text" value={username} onChange={setUsername} />
            <label className="block">
              <span className="mb-2 block text-sm font-medium">Select your region</span>
              <select
                value={selectedRegion}
                onChange={(event) => setSelectedRegion(event.target.value)}
                disabled={loadingRegions}
                className="w-full rounded-2xl border border-ink/10 bg-canvas px-4 py-3 disabled:opacity-50"
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
            <Input label="Email" type="email" value={email} onChange={setEmail} />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
            />
            <Input
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={setConfirmPassword}
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white disabled:opacity-70"
            >
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>
        </div>

        {error ? <ErrorState title="Signup failed" message={error} /> : null}

        <p className="text-center text-sm text-ink/70">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-moss">
            Log in
          </Link>
        </p>
      </section>
    </AuthGuard>
  );
}

function Input({
  label,
  type,
  value,
  onChange
}: {
  label: string;
  type: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium">{label}</span>
      <input
        required
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-2xl border border-ink/10 bg-canvas px-4 py-3"
      />
    </label>
  );
}
