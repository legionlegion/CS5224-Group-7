import { SubmissionHistoryItem, VerifyActivityResult } from "@/lib/types";

const successfulLogStorageKey = "ecobin-go:successful-logs";
const maxStoredLogs = 100;

function isValidSubmissionHistoryItem(item: unknown): item is SubmissionHistoryItem {
  const candidate = item as SubmissionHistoryItem;
  return (
    typeof candidate?.id === "string" &&
    typeof candidate?.datetime === "string" &&
    (candidate?.status === "approved" ||
      candidate?.status === "rejected" ||
      candidate?.status === "pending") &&
    typeof candidate?.pointsEarned === "number" &&
    Array.isArray(candidate?.detectedItems)
  );
}

export function getSuccessfulLogs(): SubmissionHistoryItem[] {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(successfulLogStorageKey);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(isValidSubmissionHistoryItem);
  } catch {
    return [];
  }
}

export function saveSuccessfulLog(result: VerifyActivityResult): void {
  if (typeof window === "undefined" || result.status !== "success") {
    return;
  }

  const detectedItems = Array.isArray(result.verification_details?.detected_items)
    ? result.verification_details.detected_items.filter(
        (item): item is string => typeof item === "string"
      )
    : [];
  const pointsEarned = result.rewards?.points_earned ?? 0;
  const datetime =
    typeof result.timestamp === "string" && !Number.isNaN(Date.parse(result.timestamp))
      ? result.timestamp
      : new Date().toISOString();
  const id = result.transaction_id || `log-${Date.now()}`;

  const nextItem: SubmissionHistoryItem = {
    id,
    datetime,
    status: "approved",
    pointsEarned,
    detectedItems
  };

  const existingLogs = getSuccessfulLogs();
  const deduped = existingLogs.filter((item) => item.id !== id);
  const nextLogs = [nextItem, ...deduped].slice(0, maxStoredLogs);
  window.localStorage.setItem(successfulLogStorageKey, JSON.stringify(nextLogs));
}
