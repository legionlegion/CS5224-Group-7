import { USE_MOCK_API } from "@/lib/api";

export function MockModeBadge() {
  if (!USE_MOCK_API) {
    return null;
  }

  return (
    <span className="rounded-full bg-clay px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white">
      Mock Mode
    </span>
  );
}
