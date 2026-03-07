import { SubmissionHistoryItem } from "@/lib/types";

export function SubmissionHistoryList({
  items
}: {
  items: SubmissionHistoryItem[];
}) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} className="rounded-3xl bg-white/85 p-4 shadow-card">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold">
                {new Date(item.datetime).toLocaleString(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short"
                })}
              </p>
              <p className="text-sm capitalize text-ink/60">{item.status}</p>
            </div>
            <span className="rounded-full bg-leaf/20 px-3 py-1 text-sm font-semibold">
              +{item.pointsEarned}
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {item.detectedItems.length ? (
              item.detectedItems.map((detectedItem) => (
                <span key={detectedItem} className="rounded-full bg-canvas px-3 py-1 text-sm">
                  {detectedItem}
                </span>
              ))
            ) : (
              <span className="text-sm text-ink/60">No detected items</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
