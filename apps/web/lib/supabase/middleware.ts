import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Refreshes the Supabase session on every request and keeps the
 * browser's auth cookies in sync with what the server thinks is true.
 *
 * This is required by @supabase/ssr — without it, server components
 * read whatever cookies happened to be sent with the request, which
 * can go stale (expired/refreshed tokens, or a sign-out that hasn't
 * fully propagated), making auth state ("am I logged in?") drift
 * between client and server. That drift is what made logout look like
 * it "sometimes doesn't work" — the server-rendered layout could still
 * see an old session depending on timing.
 */
export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Re-validates the session (and refreshes it if needed) on every
  // request, writing any updated cookies onto the response above.
  await supabase.auth.getUser();

  return response;
}
