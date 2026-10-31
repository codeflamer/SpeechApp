---
name: kanban
description: Maple's vertical-slice kanban workflow for KANBAN.md. Use whenever work on Maple starts, continues or finishes a feature. That includes "next item/card", "continue the project", picking or starting a card, adding a new feature request or bug to the board, splitting a card that grew too big, unblocking a Blocked card, and closing a card (Definition of Done, moving it to Done, committing). Also use when someone proposes building a whole layer at once (e.g. "all the tables", "the full scoring engine"), to reshape it into vertical slices.
---

# Maple kanban: vertical slices

Maple is built one **vertical slice** at a time. A slice is a thin feature that goes through every layer it needs (database → scoring service → Next.js server → UI → tests) and ends in something a learner can actually do. **Never build a layer ahead of the feature that needs it.** No "all the migrations first", no "finish the scoring engine, then the UI".

The board is `KANBAN.md` at the repo root. `SPEC.md` is the source of truth for behaviour. `CLAUDE.md` holds the non-negotiable rules (tone, scoring, privacy, Bible-book commits).

## 1. Starting work ("next item", "continue")
1. Read `KANBAN.md`. If a card is **In progress**, continue it. Never start a second one (**WIP limit: 1**).
2. Otherwise, pull the **top card of Ready** and move its whole block under **In progress**. Don't skip ahead in Ready unless the user asks. If the top card is blocked by something outside the code, say so, and offer the next one.
3. Read the SPEC sections the card cites before writing code.
4. Plan the card in **layer order, but within this card only**: `DB` → `SCORING` → `SERVER` → `UI` → `TEST`. Each layer does only what this card's outcome needs.
5. Tell the user, in one line, which card you're on and what its demo will be.

## 2. Building the card
- Keep the slice **thin**. If something isn't needed for the card's outcome or demo, it belongs on another card.
- Database changes go in a new file in `supabase/migrations/`. Every user table gets row-level security in the same migration.
- Reuse what earlier cards built. Don't fork or duplicate a component, table or endpoint.
- If the card turns out bigger than about 1–2 days, **split it vertically**. Keep the thinnest end-to-end path on this card (e.g. one sentence, one pattern, one happy path), and add a follow-up card right below it in Ready. Never split by layer ("S06a DB", "S06b UI").
- If the work has to deviate from SPEC.md, update SPEC.md in the same change.

## 3. Definition of Done (check every point before moving to Done)
1. The card's **Demo** step works end to end on the local stack: `npm run db:start`, plus the web and scoring dev servers.
2. Every new user table has RLS, and every migration is committed.
3. There are tests for the logic the card adds (pytest / Vitest), plus the card's happy path in the Playwright E2E suite (from S01 onward).
4. CI steps pass locally: web `npm run lint`, `npx tsc --noEmit`, `npm run build`; scoring `ruff check .`, `pytest`. CI is green after the push.
5. User-facing copy follows the tone rules in CLAUDE.md: no "fix/correct/error/mistake/reduce", always "North American English", L1 features described as different.
6. Move the card block to the **top of Done**, and add `Commits:` with the hash(es) and the date.
7. Commit with the next Bible book (see CLAUDE.md): `BOOK - S0X <card title>`. Commit or push only when the user asks, and never add Claude attribution.

Report the demo result to the user plainly. If a DoD point couldn't be met, say which one and why, and leave the card **In progress**.

## 4. Adding a new request to the board
When the user asks for a new feature or reports a bug, write it as a card **before** building it:

```markdown
### S<next number> · <short learner-facing title>
**Outcome:** <what a learner can do when this is done, in one or two sentences>
- `DB` <tables / storage / RLS it needs, or omit>
- `SCORING` <scoring service work, or omit>
- `SERVER` <Next.js server / route handlers, or omit>
- `UI` <screens / components>
- `TEST` <unit + E2E coverage>
- **Demo:** <the exact steps to show it working>
- SPEC §<sections>
```

- Number cards sequentially: `S` for slices, `B` for blocked-on-outside, `L` for later/Phase 6.
- Put it where the user wants it. By default, bugs go to the top of Ready and features to Backlog. Confirm the position in one line.
- If the request is really a layer ("set up all the tables"), reshape it into the first slice that needs that layer and explain why in one line.
- If it can't be done without the user's accounts or people, put it under **Blocked** (or flag it *(people)*), naming who needs to do what.

## 5. Blocked cards
A Blocked card says exactly what the user must do (e.g. "create a Supabase project in ca-central-1"). When the user says it's done, move the card into Ready at the position the card names, then continue from step 1.
