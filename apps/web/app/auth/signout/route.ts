import { NextResponse, type NextRequest } from "next/server";

import { createRouteClient } from "@/lib/supabase/route";

/**
 * Ends the session on the server: revokes it at Supabase and clears the auth
 * cookies on the response. Doing this server-side means the cookies the server
 * reads are cleared by the server, so a request that was already in flight
 * cannot quietly bring the login back.
 *
 *   POST /auth/signout               this device only
 *   POST /auth/signout?scope=global  every device
 */
export async function POST(request: NextRequest) {
  // Only our own pages may sign a user out (blocks cross-site requests).
  const origin = request.headers.get("origin");
  if (origin && origin !== request.nextUrl.origin) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const scope =
    request.nextUrl.searchParams.get("scope") === "global" ? "global" : "local";

  const response = NextResponse.json(
    { ok: true, scope },
    { headers: { "Cache-Control": "no-store" } }
  );

  const supabase = createRouteClient(request, response);

  try {
    await supabase.auth.signOut({ scope });
  } catch {
    // Offline or Supabase unreachable: the cookies are still cleared below,
    // so this browser is signed out either way.
  }

  // Whatever happened above, no auth cookie survives this response.
  for (const { name } of request.cookies.getAll()) {
    if (name.startsWith("sb-")) {
      response.cookies.set(name, "", { path: "/", maxAge: 0 });
    }
  }

  return response;
}
