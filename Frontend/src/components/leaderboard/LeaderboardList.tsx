import { LeaderboardEntry } from "@/lib/types";

export function LeaderboardList({ entries }: { entries: LeaderboardEntry[] }) {
  return (
    <div className="space-y-3">
      {entries.map((entry) => (
        <div
          key={`${entry.userId}-${entry.rank}`}
          className={`flex items-center justify-between rounded-3xl p-4 shadow-card ${
            entry.isCurrentUser ? "bg-moss text-white" : "bg-white/85"
          }`}
        >
          <div className="flex items-center gap-3">
            <span
              className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold ${
                entry.isCurrentUser ? "bg-white/20" : "bg-canvas"
              }`}
            >
              #{entry.rank}
            </span>
            <div>
              <p className="font-semibold">{entry.displayName}</p>
              <p className={`text-sm ${entry.isCurrentUser ? "text-white/80" : "text-ink/60"}`}>
                {entry.userId}
              </p>
            </div>
          </div>
          <p className="text-lg font-semibold">{entry.points}</p>
        </div>
      ))}
    </div>
  );
}
