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
  submissionId: string;
  status: "approved" | "rejected" | "pending";
  pointsEarned: number;
  newTotalBalance: number;
  bonusApplied: boolean;
  detectedItems: string[];
  districtRank: number;
  message: string;
  submittedAt: string;
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
  email: string;
  level: string;
  totalPoints: number;
  totalSubmissions: number;
  lastRecycled: string;
  submissionHistory: SubmissionHistoryItem[];
}

export interface LocationCoordinates {
  lat: number;
  lng: number;
}
