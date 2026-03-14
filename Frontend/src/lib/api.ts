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
const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API === "false";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);

  // add Firebase signed JWT token for authentication, backend will decode this
  if (auth?.currentUser) {
    try {
      const idToken = await auth.currentUser.getIdToken();
      console.log("Id token: " + idToken)
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

  const response = await request<{
    status: string;
    count: number;
    data: NearbyBin[];
  }>(`/api/v1/nearby-bins?${params.toString()}`);
  
  return response.data;
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
  scope: LeaderboardScope,
  limit = 10
): Promise<LeaderboardEntry[]> {
  if (USE_MOCK_API) {
    return mockLeaderboard(scope, limit);
  }

  const params = new URLSearchParams({
    Scope: scope,
    Limit: String(limit)
  });

  const response = await request<{
    scope: string;
    user_current_rank: number;
    leaderboard: LeaderboardEntry[];
  }>(`/api/v1/leaderboard?${params.toString()}`);
  
  return response.leaderboard;
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

interface InitUserProfileResponse {
  status: string;
  message: string;
  user_id: string;
  data: Record<string, unknown>;
}

export async function initUserProfile(username: string): Promise<void> {
  if (USE_MOCK_API) {
    // Mock implementation - user already created in Firestore by AuthContext
    return;
  }

  await request<InitUserProfileResponse>("/api/v1/users/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username })
  });
}

export { USE_MOCK_API };
