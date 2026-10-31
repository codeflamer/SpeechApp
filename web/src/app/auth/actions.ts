"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { normalizeEmail } from "@/lib/email";
import { createClient } from "@/lib/supabase/server";

export async function sendSignInLink(formData: FormData) {
  const email = normalizeEmail(formData.get("email"));
  if (!email) redirect("/sign-in?error=email");

  const origin = (await headers()).get("origin") ?? "http://localhost:3000";
  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: `${origin}/auth/confirm` },
  });
  if (error) redirect("/sign-in?error=send");

  redirect(`/sign-in?sent=${encodeURIComponent(email)}`);
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/sign-in");
}
