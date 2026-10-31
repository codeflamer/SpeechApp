// Reads sign-in emails from the local Mailpit inbox that `supabase start` runs.
const MAILPIT = process.env.MAILPIT_URL ?? "http://127.0.0.1:54324";

type Summary = { ID: string; To: { Address: string }[] };

export async function waitForSignInLink(email: string, timeoutMs = 15_000): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const res = await fetch(`${MAILPIT}/api/v1/search?query=${encodeURIComponent(`to:"${email}"`)}`);
    const { messages } = (await res.json()) as { messages: Summary[] };
    if (messages.length > 0) {
      const message = await (await fetch(`${MAILPIT}/api/v1/message/${messages[0].ID}`)).json();
      const match = /href="([^"]*\/auth\/confirm[^"]*)"/.exec(message.HTML as string);
      if (!match) throw new Error("Sign-in email had no /auth/confirm link");
      return match[1].replaceAll("&amp;", "&");
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`No sign-in email for ${email} within ${timeoutMs} ms`);
}
