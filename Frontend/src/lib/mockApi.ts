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
      ? "success"
      : mode === "failure"
        ? "fail"
        : Math.random() > 0.3
          ? "success"
          : "fail";

  return {
    transaction_id: `mock-${Date.now()}`,
    user_id: "mock-user-1",
    status,
    verification_details: {
      gps_match: status === "success",
      distance_metres: status === "success" ? 2.4 : 35.6,
      cv_confidence_score: status === "success" ? 0.91 : 0.38,
      detected_items: status === "success" ? ["plastic bottle", "metal can"] : []
    },
    rewards:
      status === "success"
        ? {
            points_earned: 35,
            new_total_balance: 420,
            bonus_applied: "First-of-the-Week"
          }
        : undefined,
    community_impact:
      status === "success"
        ? {
            district: "Bishan",
            district_rank: 14
          }
        : undefined,
    message:
      status === "success"
        ? "Recycling verified successfully."
        : "Verification failed. Try retaking the photo with the bin in frame.",
    timestamp: new Date().toISOString()
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
    username: userId,
    level: "Silver",
    totalPoints: 385,
    stats: {
      totalSubmissions: sampleHistory.length,
      lastRecycled: sampleHistory[0].datetime
    }
  };
}

export async function mockSubmissionHistory(): Promise<SubmissionHistoryItem[]> {
  await mockDelay();
  return sampleHistory;
}
