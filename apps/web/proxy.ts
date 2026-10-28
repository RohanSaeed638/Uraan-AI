import type { NextRequest } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

// Next.js 16 renamed "Middleware" to "Proxy" (same mechanism, new file
// name/export). This used to be middleware.ts and did nothing
// (`return NextResponse.next()`), which meant the Supabase session was
// never refreshed/synced on the server, letting auth state drift
// between client and server — a root cause of logout "not working
// correctly" until a hard refresh or cache clear.
export default async function proxy(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  matcher: ["/((?!_next|favicon.ico|sw.js|auth/signout).*)"],
};
