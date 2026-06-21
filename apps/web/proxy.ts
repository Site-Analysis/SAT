import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Two domains, one deployment (see deployment-plan.md "Domain Map").
//   qnit.in   = marketing landing only. All auth lives on qnit.site.
//   qnit.site = the tool: login + dashboard + analysis.
// `.in` and `.site` are different registrable domains, so a Supabase session
// cookie set on one is NOT readable on the other — every authenticated route
// must resolve on qnit.site. This middleware only branches on host; the actual
// auth gating stays client-side (localStorage session, see lib/supabase/client.ts).
const TOOL_HOST = "qnit.site";
const LANDING_HOST = "qnit.in";

export function proxy(request: NextRequest) {
  const host = (request.headers.get("host") ?? "").split(":")[0].toLowerCase();
  const { pathname, search } = request.nextUrl;

  // Landing domain: only the marketing page (`/`) belongs here. Anything else is
  // a deep link into the tool — bounce it to qnit.site so auth lands on the right domain.
  if (host === LANDING_HOST || host === `www.${LANDING_HOST}`) {
    if (pathname === "/") return NextResponse.next();
    return NextResponse.redirect(new URL(`https://${TOOL_HOST}${pathname}${search}`), 308);
  }

  // Tool domain: there's no landing here. Send root to /login; the login page
  // client-redirects to /dashboard if a session already exists.
  if (host === TOOL_HOST || host === `www.${TOOL_HOST}`) {
    if (pathname === "/") {
      const url = request.nextUrl.clone();
      url.pathname = "/login";
      return NextResponse.redirect(url, 307);
    }
  }

  // Unknown host (e.g. *.vercel.app preview before domains attach): serve as-is.
  return NextResponse.next();
}

export const config = {
  // Skip static assets and anything with a file extension; run on real page routes.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
