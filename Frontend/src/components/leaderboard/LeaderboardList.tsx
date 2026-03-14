import { LeaderboardEntry } from "@/lib/types";

export function LeaderboardList({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div
          key={`${entry.username}-${entry.rank}`}
          className="flex items-center justify-between rounded-3xl bg-white/85 p-4 shadow-card"
        >
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-canvas text-sm font-semibold">
              #{entry.rank}
            </span>
            <div>
              <p className="font-semibold">{entry.username}</p>
              <p className="text-sm text-ink/60">{entry.points} points</p>
            </div>
          </div>
          <p className="text-lg font-semibold">{entry.points}</p>
        </div>
      ))}
    </div>
  );
}
