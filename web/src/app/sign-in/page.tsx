import { redirect } from "next/navigation";

import { sendSignInLink } from "@/app/auth/actions";
import { createClient } from "@/lib/supabase/server";

const MESSAGES: Record<string, string> = {
  email: "Enter a valid email address.",
  send: "We couldn't send the link. Wait a minute and try again.",
  link: "That link has expired or was already used. Request a new one below.",
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ sent?: string; error?: string }>;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (user) redirect("/");

  const { sent, error } = await searchParams;

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 px-4">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Sign in to Maple</h1>
        <p className="text-neutral-600 dark:text-neutral-300">
          Add a North American English accent to your toolkit.
        </p>
      </div>

      {sent ? (
        <p role="status" className="rounded border border-green-600/40 bg-green-50 p-3 text-green-900 dark:bg-green-950 dark:text-green-100">
          Check your email. We sent a sign-in link to <strong>{sent}</strong>.
        </p>
      ) : null}
      {error && MESSAGES[error] ? (
        <p role="alert" className="rounded border border-amber-600/40 bg-amber-50 p-3 text-amber-900 dark:bg-amber-950 dark:text-amber-100">
          {MESSAGES[error]}
        </p>
      ) : null}

      <form action={sendSignInLink} className="flex flex-col gap-3">
        <label htmlFor="email" className="text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          placeholder="ada@example.com"
          className="rounded border border-neutral-300 bg-white px-3 py-2 text-base dark:border-neutral-700 dark:bg-neutral-900"
        />
        <button type="submit" className="rounded bg-neutral-900 px-3 py-2 font-medium text-white dark:bg-white dark:text-neutral-900">
          Send sign-in link
        </button>
      </form>
    </main>
  );
}
