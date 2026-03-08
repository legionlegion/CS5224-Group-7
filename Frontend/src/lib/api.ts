import {
  LeaderboardEntry,
  LeaderboardScope,
  NearbyBin,
  UserStats,
  VerifyActivityResult
} from "@/lib/types";
import {
  mockLeaderboard,
  mockNearbyBins,
  mockUserStats,
  mockVerifyActivity
} from "@/lib/mockApi";
import { auth } from "@/lib/firebase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

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
    cache: "no-store"
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
    radius: String(radius)
  });

  return request<NearbyBin[]>(`/api/v1/nearby-bins?${params.toString()}`);
}

export async function verifyActivity(formData: FormData): Promise<VerifyActivityResult> {
  if (USE_MOCK_API) {
    return mockVerifyActivity();
  }

  return request<VerifyActivityResult>("/api/v1/verify-activity", {
    method: "POST",
    body: formData
  });
}

export async function getLeaderboard(
  userId: string | undefined,
  scope: LeaderboardScope,
  limit = 10
): Promise<LeaderboardEntry[]> {
  if (USE_MOCK_API) {
    return mockLeaderboard(userId, scope, limit);
  }

  const params = new URLSearchParams({
    userId: userId || "",
    scope,
    limit: String(limit)
  });

  return request<LeaderboardEntry[]>(`/api/v1/leaderboard?${params.toString()}`);
}

export async function getUserStats(userId: string): Promise<UserStats> {
  if (USE_MOCK_API) {
    return mockUserStats(userId);
  }

  return request<UserStats>(`/api/v1/users/${userId}/stats`);
}

export { USE_MOCK_API };
