import { redirect } from "next/navigation";

import { signOut } from "@/app/auth/actions";
import { createClient } from "@/lib/supabase/server";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/sign-in");

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center gap-4 px-4">
      <h1 className="text-3xl font-semibold">Maple</h1>
      <p className="text-lg text-neutral-600 dark:text-neutral-300">Add a North American English accent to your toolkit.</p>
      <p data-testid="signed-in-as">
        Signed in as <strong>{user.email}</strong>
      </p>
      <form action={signOut}>
        <button type="submit" className="rounded border px-3 py-1">
          Sign out
        </button>
      </form>
    </main>
  );
}
