"use client";

import { useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { CameraCapture } from "@/components/camera/CameraCapture";
import { RewardSummaryCard } from "@/components/rewards/RewardSummaryCard";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAuth } from "@/context/AuthContext";
import { verifyActivity } from "@/lib/api";
import { getCurrentPosition } from "@/lib/geolocation";
import { saveSuccessfulLog } from "@/lib/recyclingHistory";
import { VerifyActivityResult } from "@/lib/types";

export default function LogPage() {
  const { profile } = useAuth();
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [result, setResult] = useState<VerifyActivityResult | null>(null);
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

      const verifyResult = await verifyActivity(formData);
      saveSuccessfulLog(verifyResult);
      setResult(verifyResult);
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
          <h2 className="text-2xl font-semibold">
            {result ? "Verification result" : "Capture your recycling activity"}
          </h2>
          <p className="mt-2 text-sm text-ink/70">
            Take picture of your recyclable with the bin in the background!
            <br />
            Camera and location access are both required. File uploads are intentionally disabled.
          </p>
        </div>

        {result ? <RewardSummaryCard result={result} /> : <CameraCapture onCapture={setCapturedFile} />}

        {error ? <ErrorState message={error} /> : null}

        {result ? (
          <button
            type="button"
            onClick={() => {
              setResult(null);
              setCapturedFile(null);
              setError("");
            }}
            className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white"
          >
            Back to Log
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !capturedFile}
            className="w-full rounded-2xl bg-clay px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            {submitting ? "Verifying..." : "Submit for Verification"}
          </button>
        )}
      </section>
    </AuthGuard>
  );
}
