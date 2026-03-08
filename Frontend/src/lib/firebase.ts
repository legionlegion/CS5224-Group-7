import { initializeApp, getApps, getApp } from "firebase/app";
import {
  browserLocalPersistence,
  getAuth,
  GoogleAuthProvider,
  setPersistence
} from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyDOxgeiNSsG9QiYMORzP5N6LJi6-ndJ0QQ",
  authDomain: "cs5224-grp7.firebaseapp.com",
  projectId: "cs5224-grp7",
  storageBucket: "cs5224-grp7.firebasestorage.app",
  messagingSenderId: "396135942191",
  appId: "1:396135942191:web:30371acc65d7c7ac411eda",
  measurementId: "G-VQHD6PBFCS"
};

const hasFirebaseConfig = Object.values(firebaseConfig).every(Boolean);

export const firebaseApp = hasFirebaseConfig
  ? getApps().length
    ? getApp()
    : initializeApp(firebaseConfig)
  : null;

export const auth = firebaseApp ? getAuth(firebaseApp) : null;
export const db = firebaseApp ? getFirestore(firebaseApp) : null;
export const googleProvider = new GoogleAuthProvider();

googleProvider.setCustomParameters({ prompt: "select_account" });

if (auth) {
  setPersistence(auth, browserLocalPersistence).catch(() => {
    return undefined;
  });
}

export { hasFirebaseConfig };
