import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

import { supabaseEnv } from "./env";

// Supabase client for Server Components, Server Actions and Route Handlers.
// It acts as the signed-in learner, so row-level security applies to every query.
export async function createClient() {
  // Read cookies first: it marks the page as per-request, so Next.js never tries to
  // pre-render it at build time (where the Supabase env vars may not exist).
  const cookieStore = await cookies();
  const { url, key } = supabaseEnv();

  return createServerClient(url, key, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => cookieStore.set(name, value, options));
        } catch {
          // Called from a Server Component, where cookies are read-only. The middleware
          // refreshes the session instead, so this is safe to ignore.
        }
      },
    },
  });
}
