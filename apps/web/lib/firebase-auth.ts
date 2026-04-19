import {
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  getIdToken,
  type User,
  type Unsubscribe,
} from "firebase/auth";
import { auth } from "./firebase";

// Mutex: Firebase cancels any in-flight popup if signInWithPopup is called again.
// One global flag prevents concurrent calls from the dual-card layout.
let _popupInFlight = false;

export async function signInWithGoogle(): Promise<User> {
  if (!auth) throw new Error("Firebase is not configured. Add NEXT_PUBLIC_FIREBASE_* env vars.");
  if (_popupInFlight) {
    throw Object.assign(new Error("Sign-in already in progress — please wait."), { code: "auth/popup-in-flight" });
  }

  const provider = new GoogleAuthProvider();
  // Force account-picker every time; prevents popup closing silently when a
  // Google session is already active in the browser.
  provider.setCustomParameters({ prompt: "select_account" });
  provider.addScope("email");
  provider.addScope("profile");

  _popupInFlight = true;
  try {
    const result = await signInWithPopup(auth, provider);
    return result.user;
  } finally {
    _popupInFlight = false;
  }
}

export async function logoutUser(): Promise<void> {
  if (auth) await signOut(auth);
  try {
    localStorage.removeItem("ngo_token");
    document.cookie = "ngo_token=; path=/; max-age=0";
  } catch {
    // SSR — no localStorage
  }
}

export function observeAuthState(cb: (user: User | null) => void): Unsubscribe {
  if (!auth) return () => {};
  return onAuthStateChanged(auth, cb);
}

export async function getCurrentIdToken(): Promise<string | null> {
  if (!auth?.currentUser) return null;
  try {
    return await getIdToken(auth.currentUser);
  } catch {
    return null;
  }
}
