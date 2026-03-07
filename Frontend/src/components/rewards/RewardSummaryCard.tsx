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
  const badge = getBadge(result.newTotalBalance);

  return (
    <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-moss/70">Verification</p>
          <h2 className="text-2xl font-semibold capitalize">{result.status}</h2>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${badgeTone[badge]}`}>
          {badge}
        </span>
      </div>
      <p className="mt-3 text-sm text-ink/70">{result.message}</p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <Stat label="Points Earned" value={String(result.pointsEarned)} />
        <Stat label="New Balance" value={String(result.newTotalBalance)} />
        <Stat label="Bonus" value={result.bonusApplied ? "Yes" : "No"} />
        <Stat label="District Rank" value={`#${result.districtRank}`} />
      </div>
      <div className="mt-5">
        <p className="text-sm font-semibold">Detected Items</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {result.detectedItems.length ? (
            result.detectedItems.map((item) => (
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
