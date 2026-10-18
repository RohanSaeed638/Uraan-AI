import { NextResponse, type NextRequest } from "next/server";

import { createRouteClient } from "@/lib/supabase/route";

/** Only same-site paths: never let `?next=` send people to another site. */
function safePath(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard";
  }

  return value;
}

/**
 * Where Google/GitHub sign-in and email links (confirm signup, change email)
 * send people back. Swaps the one-time `code` for a session cookie.
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;
  const code = searchParams.get("code");

  if (!code) {
    return NextResponse.redirect(`${origin}/login`);
  }

  const response = NextResponse.redirect(
    `${origin}${safePath(searchParams.get("next"))}`
  );

  const { error } = await createRouteClient(request, response).auth.exchangeCodeForSession(code);

  if (error) {
    return NextResponse.redirect(`${origin}/login`);
  }

  return response;
}
