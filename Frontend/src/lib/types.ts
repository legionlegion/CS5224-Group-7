export type AuthProviderName = "password" | "google";

export interface UserProfile {
  firebaseUid: string;
  userId: string;
  email: string;
  displayName: string;
  provider: AuthProviderName;
  createdAt: string;
}

export interface BinProperties {
  id: string;
  name: string;
  block?: string;
  street?: string;
  postalCode?: string;
}

export interface BinFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: BinProperties;
}

export interface BinFeatureCollection {
  type: "FeatureCollection";
  features: BinFeature[];
}

export interface NearbyBin {
  id: string;
  address: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  distance_meters: number;
}

export interface VerifyActivityResult {
  status: "success" | "fail" | "error";
  transaction_id: string;
  user_id: string;
  verification_details: {
    gps_match: boolean;
    distance_metres: number;
    cv_confidence_score: number;
    detected_items: string[];
  };
  rewards?: {
    points_earned: number;
    bonus_applied: string;
    new_total_balance: number;
  };
  community_impact?: {
    district: string;
    district_rank: number;
  };
  timestamp: string;
  message?: string;
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  points: number;
}

export type LeaderboardScope = "global" | "local";

export interface SubmissionHistoryItem {
  id: string;
  datetime: string;
  status: "approved" | "rejected" | "pending";
  pointsEarned: number;
  detectedItems: string[];
}

export interface UserStats {
  userId: string;
  username: string;
  level: string;
  totalPoints: number;
  stats: {
    totalSubmissions: number;
    lastRecycled: string | null;
  };
}

export interface LocationCoordinates {
  lat: number;
  lng: number;
}

export interface Region {
  id: string;
  name: string;
  code: string;
}
