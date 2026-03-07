"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import {
  User,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut
} from "firebase/auth";
import {
  doc,
  getDoc,
  runTransaction,
  serverTimestamp
} from "firebase/firestore";
import { auth, db, googleProvider, hasFirebaseConfig } from "@/lib/firebase";
import { USE_MOCK_API } from "@/lib/api";
import { AuthProviderName, UserProfile } from "@/lib/types";

interface SignupInput {
  username: string;
  email: string;
  password: string;
  displayName?: string;
}

interface AuthContextValue {
  authUser: User | null;
  profile: UserProfile | null;
  loading: boolean;
  isAuthenticated: boolean;
  isDevSession: boolean;
  needsProfileCompletion: boolean;
  signup: (input: SignupInput) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<boolean>;
  completeProfile: (username: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const devSessionKey = "ecobin-go:dev-session";

const devProfile: UserProfile = {
  firebaseUid: "dev-local-user",
  userId: "dev",
  email: "dev@local.ecobin",
  displayName: "Developer",
  provider: "password",
  createdAt: new Date("2026-03-06T00:00:00.000Z").toISOString()
};

function normalizeUsername(userId: string) {
  return userId.trim().toLowerCase();
}

async function getProfile(uid: string): Promise<UserProfile | null> {
  if (!db) {
    return null;
  }

  const profileRef = doc(db, "profiles", uid);
  const snapshot = await getDoc(profileRef);
  return snapshot.exists() ? (snapshot.data() as UserProfile) : null;
}

async function reserveAndCreateProfile(params: {
  uid: string;
  email: string;
  displayName: string;
  provider: AuthProviderName;
  userId: string;
}) {
  if (!db) {
    throw new Error("Firebase is not configured.");
  }

  const normalizedUserId = normalizeUsername(params.userId);
  const usernameRef = doc(db, "usernames", normalizedUserId);
  const profileRef = doc(db, "profiles", params.uid);

  await runTransaction(db, async (transaction) => {
    const usernameSnapshot = await transaction.get(usernameRef);
    if (usernameSnapshot.exists()) {
      throw new Error("Username is already taken.");
    }

    transaction.set(usernameRef, {
      firebaseUid: params.uid,
      createdAt: serverTimestamp()
    });
    transaction.set(profileRef, {
      firebaseUid: params.uid,
      userId: normalizedUserId,
      email: params.email,
      displayName: params.displayName,
      provider: params.provider,
      createdAt: new Date().toISOString()
    });
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDevSession, setIsDevSession] = useState(false);

  useEffect(() => {
    if (USE_MOCK_API && typeof window !== "undefined") {
      const hasDevSession = window.localStorage.getItem(devSessionKey) === "true";
      if (hasDevSession) {
        setProfile(devProfile);
        setIsDevSession(true);
        setLoading(false);
        return;
      }
    }

    if (!auth) {
      setLoading(false);
      return;
    }

    return onAuthStateChanged(auth, async (user) => {
      setAuthUser(user);

      if (!user) {
        setProfile(null);
        setLoading(false);
        return;
      }

      const existingProfile = await getProfile(user.uid);
      setProfile(existingProfile);
      setLoading(false);
    });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      authUser,
      profile,
      loading,
      isAuthenticated: Boolean(authUser || isDevSession),
      isDevSession,
      needsProfileCompletion: Boolean(authUser && !isDevSession && !profile),
      signup: async ({ username, email, password, displayName }) => {
        if (!auth || !hasFirebaseConfig) {
          throw new Error("Firebase is not configured.");
        }

        const credential = await createUserWithEmailAndPassword(auth, email, password);
        await reserveAndCreateProfile({
          uid: credential.user.uid,
          email,
          userId: username,
          displayName: displayName || username,
          provider: "password"
        });

        const createdProfile = await getProfile(credential.user.uid);
        setProfile(createdProfile);
      },
      login: async (email, password) => {
        if (USE_MOCK_API && email.trim().toLowerCase() === "dev" && password === "dev") {
          if (typeof window !== "undefined") {
            window.localStorage.setItem(devSessionKey, "true");
          }
          setProfile(devProfile);
          setIsDevSession(true);
          return;
        }

        if (!auth || !hasFirebaseConfig) {
          throw new Error("Firebase is not configured.");
        }

        await signInWithEmailAndPassword(auth, email, password);
      },
      loginWithGoogle: async () => {
        if (!auth || !hasFirebaseConfig) {
          throw new Error("Firebase is not configured.");
        }

        const credential = await signInWithPopup(auth, googleProvider);
        const existingProfile = await getProfile(credential.user.uid);
        setProfile(existingProfile);
        return !existingProfile;
      },
      completeProfile: async (username) => {
        if (!authUser) {
          throw new Error("User is not signed in.");
        }

        await reserveAndCreateProfile({
          uid: authUser.uid,
          email: authUser.email || "",
          userId: username,
          displayName: authUser.displayName || username,
          provider: "google"
        });

        const createdProfile = await getProfile(authUser.uid);
        setProfile(createdProfile);
      },
      logout: async () => {
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(devSessionKey);
        }
        setIsDevSession(false);

        if (!auth) {
          setProfile(null);
          return;
        }

        await signOut(auth);
        setProfile(null);
      }
    }),
    [authUser, isDevSession, loading, profile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
