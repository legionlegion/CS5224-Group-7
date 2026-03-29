import { VerifyActivityResult } from "@/lib/types";

const badgeTone = {
  Bronze: "bg-[#8e5a3c] text-white",
  Silver: "bg-slate-300 text-slate-900",
  Gold: "bg-yellow-300 text-yellow-950"
} as const;

function getBadge(points: number) {
  if (points >= 600) {
    return "Gold";
  }
  if (points >= 250) {
    return "Silver";
  }
  return "Bronze";
}

export function RewardSummaryCard({ result }: { result: VerifyActivityResult }) {
  const newBalance = result.rewards?.new_total_balance ?? 0;
  const pointsEarned = result.rewards?.points_earned ?? 0;
  const detectedItems = result.verification_details?.detected_items ?? [];
  const badge = getBadge(newBalance);
  const statusLabel = result.status === "success" ? "Approved" : "Rejected";
  const message =
    result.message ??
    (result.status === "success"
      ? "Recycling verified successfully."
      : "Verification failed. Try retaking the photo with the bin in frame.");

  return (
    <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-moss/70">Verification</p>
          <h2 className="text-2xl font-semibold">{statusLabel}</h2>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${badgeTone[badge]}`}>
          {badge}
        </span>
      </div>
      <p className="mt-3 text-sm text-ink/70">{message}</p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <Stat label="Points Earned" value={String(pointsEarned)} />
        <Stat label="New Balance" value={String(newBalance)} />
      </div>
      <div className="mt-5">
        <p className="text-sm font-semibold">Detected Items</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {detectedItems.length ? (
            detectedItems.map((item) => (
              <span key={item} className="rounded-full bg-leaf/20 px-3 py-1 text-sm text-ink">
                {item}
              </span>
            ))
          ) : (
            <span className="text-sm text-ink/60">No items detected.</span>
          )}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-canvas p-3">
      <p className="text-xs uppercase tracking-[0.15em] text-moss/70">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  );
}
