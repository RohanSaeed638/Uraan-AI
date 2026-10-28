/**
 * "Remember me". Supabase keeps people signed in for a long time. When
 * someone unticks it, we sign them out once the browser has been closed.
 *
 * Two markers do this:
 *  - a flag in localStorage: "this login should not outlive the browser";
 *  - a cookie with no expiry (a session cookie), which the browser itself
 *    deletes when it closes. It is shared by all tabs, so opening another
 *    tab does not sign anyone out.
 * If the flag is set but the cookie is gone, the browser was closed.
 */
const FLAG = "uraan-session-only";
const ALIVE = "uraan-alive";

export function setRememberMe(remember: boolean) {
  try {
    if (remember) localStorage.removeItem(FLAG);
    else localStorage.setItem(FLAG, "1");
  } catch {
    // Private mode: nothing to remember either way.
  }

  document.cookie = remember
    ? `${ALIVE}=; Path=/; Max-Age=0; SameSite=Lax`
    : `${ALIVE}=1; Path=/; SameSite=Lax`;
}

/** True when a "don't remember me" login has outlived its browser session. */
export function sessionEndedWithBrowser(): boolean {
  try {
    if (localStorage.getItem(FLAG) !== "1") return false;
  } catch {
    return false;
  }

  return !document.cookie.split("; ").includes(`${ALIVE}=1`);
}

export function clearRememberPreference() {
  try {
    localStorage.removeItem(FLAG);
  } catch {
    // Nothing to clear.
  }

  document.cookie = `${ALIVE}=; Path=/; Max-Age=0; SameSite=Lax`;
}
