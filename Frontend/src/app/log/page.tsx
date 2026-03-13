"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { CameraCapture } from "@/components/camera/CameraCapture";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAuth } from "@/context/AuthContext";
import { verifyActivity } from "@/lib/api";
import { getCurrentPosition } from "@/lib/geolocation";

const rewardSessionKey = "ecobin-go:latest-reward";

export default function LogPage() {
  const router = useRouter();
  const { profile } = useAuth();
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setError("");

    if (!capturedFile) {
      setError("Capture a photo before submitting.");
      return;
    }

    if (!profile) {
      setError("Your profile is still loading.");
      return;
    }

    setSubmitting(true);

    try {
      const coords = await getCurrentPosition();
      const formData = new FormData();
      formData.append("Latitude", String(coords.lat));
      formData.append("Longitude", String(coords.lng));
      formData.append("Image", capturedFile);

      const result = await verifyActivity(formData);
      sessionStorage.setItem(rewardSessionKey, JSON.stringify(result));
      router.push("/rewards");
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to verify recycling activity."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/80 p-4 shadow-card">
          <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Camera Log</p>
          <h2 className="text-2xl font-semibold">Capture your recycling activity</h2>
          <p className="mt-2 text-sm text-ink/70">
            Camera and location access are both required. File uploads are intentionally disabled.
          </p>
        </div>

        <CameraCapture onCapture={setCapturedFile} />

        {error ? <ErrorState message={error} /> : null}

        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || !capturedFile}
          className="w-full rounded-2xl bg-clay px-4 py-3 font-semibold text-white disabled:opacity-60"
        >
          {submitting ? "Verifying..." : "Submit for Verification"}
        </button>
      </section>
    </AuthGuard>
  );
}
