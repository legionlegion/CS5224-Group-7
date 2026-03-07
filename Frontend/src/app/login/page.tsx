"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAuth } from "@/context/AuthContext";
import { USE_MOCK_API } from "@/lib/api";

export default function LoginPage() {
  const { login, loginWithGoogle } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      router.replace("/map");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to log in.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setLoading(true);

    try {
      const firstTime = await loginWithGoogle();
      router.replace(firstTime ? "/complete-profile" : "/map");
    } catch (googleError) {
      setError(
        googleError instanceof Error ? googleError.message : "Google sign-in failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthGuard>
      <section className="space-y-6">
        <div className="rounded-[2rem] bg-white/80 p-6 shadow-card">
          <p className="text-sm uppercase tracking-[0.25em] text-moss/70">Login</p>
          <h2 className="mt-2 text-3xl font-semibold">Welcome back</h2>
          <p className="mt-2 text-sm text-ink/70">
            Continue your recycling streak and earn more points.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <Input label="Email or dev" type="text" value={email} onChange={setEmail} />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white disabled:opacity-70"
            >
              {loading ? "Signing in..." : "Log In"}
            </button>
          </form>

          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={loading}
            className="mt-3 w-full rounded-2xl border border-ink/15 bg-white px-4 py-3 font-semibold"
          >
            Continue with Google
          </button>
        </div>

        {error ? <ErrorState title="Login failed" message={error} /> : null}

        <p className="text-center text-sm text-ink/70">
          New here?{" "}
          <Link href="/signup" className="font-semibold text-moss">
            Create an account
          </Link>
        </p>

        {USE_MOCK_API ? (
          <aside className="rounded-[2rem] border border-clay/20 bg-clay p-5 text-white shadow-card">
            <p className="text-xs uppercase tracking-[0.25em] text-white/75">Dev Panel</p>
            <h3 className="mt-2 text-xl font-semibold">Bypass login</h3>
            <p className="mt-2 text-sm text-white/85">
              Mock mode is enabled. Use `dev` / `dev` or jump straight in.
            </p>
            <button
              type="button"
              disabled={loading}
              onClick={async () => {
                setEmail("dev");
                setPassword("dev");
                setError("");
                setLoading(true);
                try {
                  await login("dev", "dev");
                  router.replace("/map");
                } catch (devError) {
                  setError(
                    devError instanceof Error ? devError.message : "Unable to start dev session."
                  );
                } finally {
                  setLoading(false);
                }
              }}
              className="mt-4 w-full rounded-2xl bg-white px-4 py-3 font-semibold text-clay"
            >
              Enter as Dev User
            </button>
          </aside>
        ) : null}
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
