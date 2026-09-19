import { getApp, getApps, initializeApp } from "firebase/app";
import { type Auth, getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

export function getFirebaseAuth(): Auth {
  if (typeof window === "undefined") {
    throw new Error(
      "Firebase Authentication is only available in the browser.",
    );
  }

  if (Object.values(firebaseConfig).some((value) => !value)) {
    throw new Error("Firebase Authentication is not configured.");
  }

  const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
  return getAuth(app);
}
