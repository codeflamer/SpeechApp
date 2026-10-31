// Trims and lowercases an email address, or returns null if it doesn't look like one.
// Deliberately simple: Supabase does the real validation when it sends the link.
export function normalizeEmail(raw: unknown): string | null {
  if (typeof raw !== "string") return null;
  const email = raw.trim().toLowerCase();
  if (email.length > 254) return null;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? email : null;
}
