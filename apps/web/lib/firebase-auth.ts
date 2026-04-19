import {
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  getIdToken,
  type User,
  type Unsubscribe,
} from "firebase/auth";
import { auth } from "./firebase";

const SESSION_ROLE_KEY   = "_signin_role";
const SESSION_INVITE_KEY = "_signin_invite";

function makeProvider(): GoogleAuthProvider {
  const p = new GoogleAuthProvider();
  p.addScope("email");
  p.addScope("profile");
  return p;
}

// Mutex: only one popup at a time across the dual-card layout.
let _popupInFlight = false;

export async function signInWithGoogle(): Promise<User> {
  if (!auth) throw new Error("Firebase is not configured. Add NEXT_PUBLIC_FIREBASE_* env vars.");
  if (_popupInFlight) {
    throw Object.assign(new Error("Sign-in already in progress — please wait."), { code: "auth/popup-in-flight" });
  }
  _popupInFlight = true;
  try {
    const result = await signInWithPopup(auth, makeProvider());
    return result.user;
  } finally {
    _popupInFlight = false;
  }
}

/**
 * Redirect fallback for browsers that block popups (third-party cookie restrictions).
 * Saves role + inviteCode to sessionStorage so they survive the page reload.
 */
export function startGoogleRedirect(role: "ngo_admin" | "volunteer", inviteCode: string): void {
  if (!auth) throw new Error("Firebase is not configured. Add NEXT_PUBLIC_FIREBASE_* env vars.");
  try {
    sessionStorage.setItem(SESSION_ROLE_KEY, role);
    sessionStorage.setItem(SESSION_INVITE_KEY, inviteCode);
  } catch { /* private browsing — proceed without storage */ }
  signInWithRedirect(auth, makeProvider());
}

/**
 * Call on page mount. Resolves with Firebase user + saved role/inviteCode
 * if the page was loaded after a redirect sign-in. Returns null otherwise.
 */
export async function getGoogleRedirectResult(): Promise<{
  user: User;
  role: "ngo_admin" | "volunteer";
  inviteCode: string;
} | null> {
  if (!auth) return null;
  try {
    const result = await getRedirectResult(auth);
    if (!result) return null;
    let role: "ngo_admin" | "volunteer" = "ngo_admin";
    let inviteCode = "";
    try {
      role = (sessionStorage.getItem(SESSION_ROLE_KEY) as typeof role) ?? "ngo_admin";
      inviteCode = sessionStorage.getItem(SESSION_INVITE_KEY) ?? "";
      sessionStorage.removeItem(SESSION_ROLE_KEY);
      sessionStorage.removeItem(SESSION_INVITE_KEY);
    } catch { /* ignore */ }
    return { user: result.user, role, inviteCode };
  } catch {
    return null;
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
