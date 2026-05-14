import { auth } from "@/auth";
import { NextResponse } from "next/server";
import { defaultLocale, isLocale } from "@/lib/i18n/config";

const PROTECTED_SEGMENTS = [
  "dashboard", "agents", "tasks", "evolution",
  "skills", "billing", "settings", "onboarding",
];

function applyForwardedHost(url: URL, request: Request): void {
  const headers = new Headers(request.headers);
  const xfHost = headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const xfProto = headers.get("x-forwarded-proto")?.split(",")[0]?.trim();
  if (xfHost) url.host = xfHost;
  if (xfProto === "http" || xfProto === "https") url.protocol = `${xfProto}:`;
}

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isLoggedIn = !!req.auth;

  // Skip static assets and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api/") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Login page logic
  if (pathname === "/login") {
    if (isLoggedIn) {
      const url = req.nextUrl.clone();
      applyForwardedHost(url, req);
      url.pathname = `/${defaultLocale}/dashboard`;
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  // i18n: root "/" → "/{defaultLocale}"
  const segments = pathname.split("/").filter(Boolean);
  const firstSegment = segments[0];

  if (!firstSegment || !isLocale(firstSegment)) {
    const url = req.nextUrl.clone();
    applyForwardedHost(url, req);
    url.pathname = `/${defaultLocale}${pathname === "/" ? "" : pathname}`;
    return NextResponse.redirect(url);
  }

  // Auth protection for locale-prefixed routes
  const secondSegment = segments[1];
  const isProtected = secondSegment && PROTECTED_SEGMENTS.includes(secondSegment);

  if (isProtected && !isLoggedIn) {
    const url = req.nextUrl.clone();
    applyForwardedHost(url, req);
    url.pathname = "/login";
    url.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
