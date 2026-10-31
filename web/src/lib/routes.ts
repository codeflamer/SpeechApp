// Paths a signed-out visitor may open. Everything else requires a session (SPEC §5.1).
const PUBLIC_SECTIONS = ["/sign-in", "/auth", "/spike"];

// Match whole path segments: "/auth/confirm" is public, "/authority" is not.
export function isPublicPath(pathname: string): boolean {
  return PUBLIC_SECTIONS.some((section) => pathname === section || pathname.startsWith(`${section}/`));
}

// Only allow same-site relative redirects after sign-in, so a crafted link can't
// bounce a learner to another website ("open redirect").
export function safeNextPath(next: string | null | undefined): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) return "/";
  return next;
}
