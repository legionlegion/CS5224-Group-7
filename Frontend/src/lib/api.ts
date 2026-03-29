import {
  LeaderboardEntry,
  LeaderboardRegionId,
  NearbyBin,
  Region,
  SubmissionHistoryItem,
  UserStats,
  VerifyActivityResult,
} from "@/lib/types";
import {
  mockLeaderboard,
  mockNearbyBins,
  mockSubmissionHistory,
  mockUserStats,
  mockVerifyActivity,
} from "@/lib/mockApi";
import { auth } from "@/lib/firebase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080";
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API?.toLowerCase() === "true";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);

  // add Firebase signed JWT token for authentication, backend will decode this
  if (auth?.currentUser) {
    try {
      const idToken = await auth.currentUser.getIdToken();
      headers.set("Authorization", `Bearer ${idToken}`);
    } catch (error) {
      console.error("Failed to get Firebase ID token:", error);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getNearbyBins(
  lat: number,
  lng: number,
  radius = 500
): Promise<NearbyBin[]> {
  if (USE_MOCK_API) {
    return mockNearbyBins(lat, lng);
  }

  const params = new URLSearchParams({
    lat: String(lat),
    lng: String(lng),
    radius: String(radius),
  });

  const response = await request<{
    status: string;
    count: number;
    data: NearbyBin[];
  }>(`/api/v1/nearby-bins?${params.toString()}`);

  return response.data;
}

export async function verifyActivity(
  formData: FormData
): Promise<VerifyActivityResult> {
  if (USE_MOCK_API) {
    return mockVerifyActivity();
  }

  return request<VerifyActivityResult>("/api/v1/verify-activity", {
    method: "POST",
    body: formData,
  });
}

export async function getLeaderboard(
  region: LeaderboardRegionId,
  limit = 10
): Promise<LeaderboardEntry[]> {
  if (USE_MOCK_API) {
    return mockLeaderboard(region, limit);
  }

  const params = new URLSearchParams({
    Region: region,
    Limit: String(limit)
  });

  const response = await request<{
    region: string;
    user_current_rank: number | null;
    leaderboard: LeaderboardEntry[];
  }>(`/api/v1/leaderboard?${params.toString()}`);

  return response.leaderboard;
}

const validLeaderboardRegions = new Set<LeaderboardRegionId>([
  "all",
  "central",
  "east",
  "west",
  "north",
  "north-east"
]);

export async function getUserRegion(): Promise<LeaderboardRegionId> {
  if (USE_MOCK_API) {
    return "central";
  }

  const response = await request<{
    status: string;
    region_id: string | null;
  }>("/api/v1/users/region");

  const normalized = (response.region_id || "").toLowerCase();
  return validLeaderboardRegions.has(normalized as LeaderboardRegionId)
    ? (normalized as LeaderboardRegionId)
    : "all";
}

export async function getUserGlobalRank(): Promise<number> {
  if (USE_MOCK_API) {
    return 12;
  }

  const response = await request<{
    status: string;
    rank: number;
  }>("/api/v1/users/rank/global");

  return response.rank;
}

export async function getUserRegionRank(): Promise<number> {
  if (USE_MOCK_API) {
    return 4;
  }

  const response = await request<{
    status: string;
    rank: number;
  }>("/api/v1/users/rank/region");

  return response.rank;
}

export async function getUserStats(): Promise<UserStats> {
  if (USE_MOCK_API) {
    return mockUserStats();
  }
  return request<UserStats>(`/api/v1/users/stats`);
}

export async function testAuth(): Promise<{
  status: string;
  message: string;
  user: {
    uid: string;
    email: string;
    email_verified: boolean;
  };
  timestamp: string;
}> {
  return request("/api/v1/test-auth");
}

export async function testModel(): Promise<VerifyActivityResult> {
  const response = await fetch("/test.jpg");
  const blob = await response.blob();
  const imageFile = new File([blob], "test.jpg", { type: "image/jpeg" });

  const formData = new FormData();
  formData.append("Image", imageFile);
  formData.append("Latitude", "1.3015");
  formData.append("Longitude", "103.8378");

  return request<VerifyActivityResult>("/api/v1/test-model", {
    method: "POST",
    body: formData,
  });
}

export async function getUserTransactions(): Promise<SubmissionHistoryItem[]> {
  if (USE_MOCK_API) {
    return mockSubmissionHistory();
  }

  const response = await request<{ status: string; data: SubmissionHistoryItem[] }>(
    "/api/v1/users/transactions"
  );

  return response.data;
}

interface UpdateUserProfilePayload {
  username?: string;
  region_id?: string;
}

export async function updateUserProfile(payload: UpdateUserProfilePayload): Promise<void> {
  if (USE_MOCK_API) {
    return;
  }

  await request<{ status: string; message: string }>("/api/v1/users/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}




interface InitUserProfileResponse {
  status: string;
  message: string;
  user_id: string;
  data: Record<string, unknown>;
}

export async function getRegions(): Promise<Region[]> {
  if (USE_MOCK_API) {
    // Mock regions
    return [
      { id: "central", name: "Central", code: "CT" },
      { id: "north", name: "North", code: "N" },
      { id: "north-east", name: "North-East", code: "NE" },
      { id: "east", name: "East", code: "E" },
      { id: "west", name: "West", code: "W" }
    ];
  }

  const response = await request<{ status: string; data: Region[] }>("/api/v1/regions");
  return response.data;
}

export async function initUserProfile(username: string, regionId?: string): Promise<void> {
  if (USE_MOCK_API) {
    // Mock implementation - user already created in Firestore by AuthContext
    return;
  }

  const body: { username: string; region_id?: string } = { username };
  if (regionId) {
    body.region_id = regionId;
  }

  await request<InitUserProfileResponse>("/api/v1/users/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export { USE_MOCK_API };
