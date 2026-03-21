import { UserProfile, UserStats } from "@/lib/types";

export function ProfileStatsCard({
  profile,
  stats
}: {
  profile: UserProfile;
  stats: UserStats;
}) {
  return (
    <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-card">
      <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Profile</p>
      <h2 className="mt-1 text-2xl font-semibold">{profile.userId}</h2>
      <p className="text-sm text-ink/70">{profile.email}</p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <ProfileStat label="Level" value={stats.level} />
        <ProfileStat label="Points" value={String(stats.totalPoints)} />
        <ProfileStat label="Submissions" value={String(stats.stats.totalSubmissions)} />
        <ProfileStat
          label="Last Recycled"
          value={new Date(stats.stats.lastRecycled).toLocaleDateString()}
        />
      </div>
    </div>
  );
}

function ProfileStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-canvas p-3">
      <p className="text-xs uppercase tracking-[0.15em] text-moss/70">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}
