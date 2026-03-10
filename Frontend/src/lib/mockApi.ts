import {
  LeaderboardEntry,
  LeaderboardScope,
  NearbyBin,
  SubmissionHistoryItem,
  UserStats,
  VerifyActivityResult
} from "@/lib/types";

const mockDelay = (ms = 900) =>
  new Promise((resolve) => setTimeout(resolve, ms + Math.random() * 500));

const sampleHistory: SubmissionHistoryItem[] = [
  {
    id: "sub-1",
    datetime: "2026-03-05T10:00:00.000Z",
    status: "approved",
    pointsEarned: 40,
    detectedItems: ["plastic bottle", "aluminium can"]
  },
  {
    id: "sub-2",
    datetime: "2026-03-03T07:35:00.000Z",
    status: "approved",
    pointsEarned: 25,
    detectedItems: ["paper packaging"]
  },
  {
    id: "sub-3",
    datetime: "2026-03-01T18:15:00.000Z",
    status: "rejected",
    pointsEarned: 0,
    detectedItems: []
  }
];

export async function mockNearbyBins(lat: number, lng: number): Promise<NearbyBin[]> {
  await mockDelay();
  return [
    {
      id: "nearby-1",
      address: "Bishan Community Club",
      coordinates: {
        lat: lat + 0.0018,
        lng: lng + 0.0012
      },
      distance_meters: 260
    },
    {
      id: "nearby-2",
      address: "Junction 8",
      coordinates: {
        lat: lat - 0.0015,
        lng: lng + 0.0009
      },
      distance_meters: 310
    }
  ];
}

export async function mockVerifyActivity(): Promise<VerifyActivityResult> {
  await mockDelay(1300);
  const mode = process.env.NEXT_PUBLIC_MOCK_VERIFY_RESULT || "random";
  const status =
    mode === "success"
      ? "approved"
      : mode === "failure"
        ? "rejected"
        : Math.random() > 0.3
          ? "approved"
          : "rejected";

  return {
    submissionId: `mock-${Date.now()}`,
    status,
    pointsEarned: status === "approved" ? 35 : 0,
    newTotalBalance: status === "approved" ? 420 : 385,
    bonusApplied: status === "approved",
    detectedItems: status === "approved" ? ["plastic bottle", "metal can"] : [],
    districtRank: status === "approved" ? 14 : 18,
    message:
      status === "approved"
        ? "Recycling verified successfully."
        : "Verification failed. Try retaking the photo with the bin in frame.",
    submittedAt: new Date().toISOString()
  };
}

export async function mockLeaderboard(
  scope: LeaderboardScope = "global",
  limit = 10
): Promise<LeaderboardEntry[]> {
  await mockDelay();
  return [
    {
      rank: 1,
      username: "EcoWarrior88",
      points: 1250
    },
    {
      rank: 2,
      username: "GreenMachine",
      points: 1100
    },
    {
      rank: 3,
      username: "NatureLover",
      points: 800
    }
  ];
}

export async function mockUserStats(userId = "guest"): Promise<UserStats> {
  await mockDelay();
  return {
    userId,
    email: `${userId}@example.com`,
    level: "Silver",
    totalPoints: 385,
    totalSubmissions: sampleHistory.length,
    lastRecycled: sampleHistory[0].datetime,
    submissionHistory: sampleHistory
  };
}

export async function mockSubmissionHistory(): Promise<SubmissionHistoryItem[]> {
  await mockDelay();
  return sampleHistory;
}
