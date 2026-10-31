# Maple: Kanban Board

From Phase 1 onward, Maple is built as **vertical slices**. Each card is one small feature that cuts through every layer it needs (database, scoring service, web server, UI), and it ends in something a learner can actually do. We never build a whole layer ahead of the features that use it.

[SPEC.md](SPEC.md) is the source of truth for behaviour. [CHECKLIST.md](CHECKLIST.md) holds Phase 0 (spikes and setup), which is done apart from the account steps listed under **Blocked** below.

## How the board works
- **Columns:** In progress → Ready → Backlog, plus **Blocked** (waiting on something outside the code) and **Later** (Phase 6 and post-MVP). Done cards are listed at the bottom, newest first.
- **WIP limit: 1.** Only one card is in progress at a time. Finish it (Definition of Done) before pulling the next one from the top of **Ready**.
- **Card size:** about 1–2 days. If a card grows bigger, split it into thinner vertical slices; never into layers.
- **Moving a card:** move the whole card block between columns, and add the commit hash(es) when it reaches Done.
- **Layers on a card:** `DB` = Supabase migration, RLS and storage · `SCORING` = Python service · `SERVER` = Next.js server code and route handlers · `UI` = pages and components · `TEST` = automated tests.

### Definition of Done (every card)
1. It works **end to end on the local stack** (`npm run db:start`, web and scoring running), and the "Demo" step on the card can be performed.
2. Every new user table has **row-level security**, with migrations in `supabase/migrations/`.
3. There are **tests** for the logic the card adds, plus the card's happy path in the Playwright end-to-end suite once S01 sets it up.
4. **CI is green.** Copy follows the tone rules (CLAUDE.md), and SPEC.md is updated if the card had to deviate from it.
5. The card is moved to **Done** with its commit hash(es). Commits follow the Bible-book rule.

---

## In progress
### S01 · Sign in with an email link (walking skeleton)
**Outcome:** a visitor signs in with a magic link and lands on a home page showing their email. Signed-out visitors are sent to sign-in.
- `DB` `profiles` table (one row per auth user, created by trigger) with an RLS rule: own row only
- `SERVER` Supabase SSR client; middleware that refreshes the session and protects app routes
- `UI` `/sign-in` (email field and "Send sign-in link"), `/auth/confirm` (verifies a one-time `token_hash` from the email, so the link works in **any** browser or device), a protected `/` showing the email, and sign out
- `TEST` Set up Vitest and Playwright, plus pgTAP database tests (`supabase/tests/`). E2E: sign in through Mailpit and sign out; the link works in a different browser; a bad link shows a friendly message. DB: a learner can't read another learner's profile. CI gets an `e2e` job that runs the local Supabase stack
- **Demo:** sign in locally using the link from Mailpit (http://127.0.0.1:54324)
- SPEC §5.1, §8
- **Started:** 2026-10-31
- **Status:** Definition of Done met locally (demo, 23 unit, 4 E2E, 5 DB tests, all CI steps). Waiting on commit and a green CI run, then it moves to Done.

---

## Ready
Ordered: the top card is next.

### S02 · Consent before anything else
**Outcome:** after their first sign-in, a learner must accept recording-storage consent before using the app. Training-use consent is a separate opt-in, off by default, that they can change later.
- `DB` `consents` table (type, version, granted_at, revoked_at), with RLS: own rows
- `SERVER` A "has the current consent version" check that guards every app route
- `UI` Consent screen; settings page with the training-use toggle; draft privacy policy page covering Azure processing, cross-border transfer, PIPEDA, the Nigeria Data Protection Act 2023 and the Ghana Data Protection Act
- `TEST` E2E: a new user is blocked until they consent; the training toggle saves and can be revoked
- **Demo:** new account → consent screen → app; turn training consent on and off in settings
- SPEC §5.1, §9

### S03 · Learner profile
**Outcome:** the learner tells us their background and preferences, and can change them later.
- `DB` Add to `profiles`: L1 (Nigerian or Ghanaian), optional home language, goal mode, voice preference (Ava or Andrew)
- `UI` Profile step after consent, editable in settings. Goal mode shows only Native-likeness enabled; Intelligibility and Confidence are marked "coming soon"
- `TEST` Unit test for profile validation; E2E: complete the profile, then edit it
- **Demo:** fill in the profile and see it saved in settings
- SPEC §5.1

### S04 · Record a sentence and keep it
**Outcome:** the learner records themselves reading a sentence, and the recording appears in "My recordings" where they can play it back. No scoring yet.
- `DB` Private `recordings` bucket with policies limited to the owner's folder; `attempts` table (id is a client-generated idempotency key, user, item text, audio_key, status = `uploaded`); `usage` table for per-user daily metering
- `SERVER` Route that checks `entitlements(user)` (everyone gets `free_all`), enforces the soft limit of 300 attempts per day, and returns a signed upload URL. Audio goes from the browser straight to Storage, never through Vercel
- `UI` Recorder component:
  - tap to start and stop, auto-stop after 1.5 s of silence, 15 s maximum, starts from a user gesture
  - picks the format in this order: WebM/Opus, then Ogg, then MP4
  - mic-permission flow, plus a listening-only message when the mic is denied
  
  Also a "My recordings" list with playback
- `TEST` Unit tests for format choice and the auto-stop timer; E2E records the test tone (built-in browser flow, as in the Phase 0 spike); a test that the RLS stops user B from reading user A's recording
- **Demo:** record two takes and play both back; a second account can't see them
- SPEC §5.3, §6.1 step 1, §8, §10

### S05 · "Was that recording usable?" (quality gate)
**Outcome:** after recording, the learner sees either "Got it" or a specific, friendly reason to try again: too quiet, too noisy, clipped, or too short.
- `SCORING`
  - Token-protected `POST /attempts/{id}/check`, plus an Azure credential check at startup
  - Fetches the audio from Storage and converts it to 16 kHz mono WAV. Duration is measured on the **decoded** WAV
  - Voice activity detection, signal-to-noise, clipping and duration checks, each returning a reason code
- `DB` `attempts.status` becomes `passed` or `abstained` (with `abstain_reason`)
- `SERVER` After the upload completes, call the scoring service with `SCORING_SERVICE_TOKEN`
- `UI` Result state with friendly copy for each reason, plus a Bluetooth-headset hint when the noise check fails
- `TEST` pytest on fixture clips (including the Phase 0 WebM/Ogg/MP4 cases) and generated silent, clipped and noisy audio; E2E: tone recording → reason shown
- **Demo:** record normally → "Got it"; record silence → "We couldn't hear you…"
- SPEC §6.1 step 2, §6.2, §10

### S06 · Hear the North American model
**Outcome:** on any sentence, the learner can play Ava or Andrew saying it, at normal or 0.75× speed.
- `DB` `tts` folder in Storage, cached by a hash of (voice, text, ssml version)
- `SERVER` Generates TTS with `<prosody rate="-15%">` and the place-name SSML override list, stores it once, returns a signed URL; meters TTS characters
- `UI` Play button with 1.0× / 0.75× speed; uses the voice preference from S03
- `TEST` Unit test for the cache key; a test that a second request doesn't call Azure
- **Demo:** play the TH sentence in both voices; switch the voice in settings
- SPEC §5.3, §8, §10

### S07 · First scored sentence (TH)
**Outcome:** the learner hears the TH sentence (S06), reads it, and sees each target word coloured match / close / try again.
- `DB`
  - `patterns` table (id, accent_tag = `shared`, target phonemes, thresholds) and a `content_items` table, seeded with the TH pattern and one sentence
  - Add `api_raw`, `labels` and `scoring_version` to `attempts`
- `SCORING`
  - Azure `en-US` Pronunciation Assessment with the reference text, phoneme granularity and the SAPI alphabet
  - Target phonemes are found **by label inside the target words**, and versioned thresholds give each word a label and the pattern a 0–100 score
  - Abstain when word error rate is over 30% ("It sounded like you said…"); low-confidence words are marked "unclear"
  - Meter API seconds
- `UI` "Listening…" state, then the sentence with target words coloured
- `TEST` pytest on Tolu's TH clips, plus a synthetic "tink" case from the sensitivity spike; a test that abstained attempts carry no labels
- **Demo:** say "I think this is the third thing" well and then as "I tink dis…", and see the difference
- SPEC §6.1 steps 3–5, §6.2, §6.3

---

## Backlog
Roughly in order. Each card is still a full vertical slice.

### S08 · TH module practice set
**Outcome:** a learner can work through the whole TH module: pick a sentence, hear it, record, see the result, then Retry or Next.
- `DB` Full TH content seeded: about 30 minimal pairs and 25 sentences across the workplace and everyday-life-in-Canada domains, with target word spans. Never target Canada-only words
- `UI` Module page, drill screen with target sounds underlined, and Retry / Next
- `TEST` A content lint that fails CI if a target is a Canada-only word or lacks a target phoneme; E2E through two drills
- SPEC §4, §5.2, §5.3

### S27 · Content review *(people)*
**Outcome:** the TH module content from S08 is reviewed by a Nigerian or Ghanaian English speaker and by a North American English phonetics reviewer, and place-name pronunciations are re-checked. Their feedback becomes a short content guide, and each later module (S12–S14) gets the same review before it's marked Done.
- Placed right after S08 so tone and accuracy problems are caught on the first module, before the pattern is copied to three more
- SPEC §13.3

### S09 · TH listening drill and perception gate
**Outcome:** the learner first trains their ear on TH minimal pairs ("thin" or "tin"?). Speaking drills unlock at 80% or above.
- `DB` `perception_results` table
- `UI` Listen-and-choose drill using TTS audio; the unlock rule on the module page
- `TEST` Unit test for the gate rule; E2E: score 80% and see speaking unlock
- SPEC §5.2

### S10 · Feedback panel
**Outcome:** after a scored attempt, the learner can tap a word to hear their own version beside the model, see a mouth diagram for the sound, and flag "This doesn't seem right".
- `DB` `feedback_reports` table, logged only with consent
- `UI` Side-by-side playback trimmed to the tapped word (using Azure word timings), a static articulation SVG for TH, and the report button
- `TEST` Unit test for word-timing trimming; E2E: report a result
- SPEC §5.3, §6.3

### S11 · Coaching tip (TH)
**Outcome:** each result shows a one- or two-sentence tip that takes the learner's L1 into account.
- `SERVER` Vetted tip template library for TH × L1. Claude (Sonnet-class) receives structured JSON only and returns strict JSON. The raw template is the fallback whenever the call fails. Audio is never sent
- `UI` Tip under the result
- `TEST` Unit tests for the fallback path and the JSON schema; a test that the request contains no audio fields
- SPEC §6.1 step 6, §9

### S12 · Module: *ship* vs *sheep*
**Outcome:** the full *ship/sheep* module works end to end, reusing S08–S11: content, listening drill, scoring config, SVG and tips.
- Content reviewed with the S27 guide and reviewers before Done
- SPEC §4

### S13 · Module: Rhotic R
**Outcome:** the full r module works end to end. **It scores only r-coloured vowels** (*bird, worker*), never a syllable-final r (*car*). The content lint enforces this.
- Content reviewed with the S27 guide and reviewers before Done
- SPEC §4, §13.1

### S14 · Module: Schwa and word stress
**Outcome:** the full schwa module works end to end, using clear cases (*support, police*) and generous "close" bands.
- Content reviewed with the S27 guide and reviewers before Done
- SPEC §4

### S15 · Diagnostic onboarding
**Outcome:** a new learner goes sign-up → consent → profile → mic check → diagnostic, and sees per-pattern results and their top 3 focus areas.
- `DB` `diagnostics` table
- `UI` Mic check (3 s of silence plus 1 sentence, with noise guidance), about 10 diagnostic sentences covering all 4 patterns, about 10 perception items, and an encouraging results screen
- `TEST` E2E through the full onboarding
- SPEC §5.1

### S16 · Today's session (mastery and focus)
**Outcome:** the home page offers a ~10-minute session built around the learner's weakest pattern.
- `DB` `pattern_mastery` table: perception and production as an exponentially weighted moving average of **non-abstained** attempts
- `SERVER`
  - Focus selection: lowest mastery, weighted for native-likeness
  - Mastered rule: ≥80 over the last 15 attempts, across at least 2 sessions
  - Skip patterns already mastered in the diagnostic
  - Outcome modes and accent tags stored as config
- `UI` "Today" screen
- `TEST` Unit tests for the EWMA, the mastered rule, and "abstained attempts never lower mastery"
- SPEC §5.2, §7

### S17 · Spaced review
**Outcome:** weak words come back on a spaced-repetition schedule at the start of each session.
- `DB` `srs_cards` table (SM-2 state per word)
- `TEST` Unit tests for SM-2 intervals
- SPEC §5.2, §7

### S18 · Progress page
**Outcome:** the learner sees a mastery-over-time chart for each pattern, and can play "You, week 1 vs now" on the same sentence. No streaks or badges.
- SPEC §5.5

### S19 · Re-diagnosis
**Outcome:** every 3 weeks, or on demand, a shortened diagnostic refreshes the learner's priorities.
- SPEC §5.5, §7

### S20 · Practise your own text
**Outcome:** the learner pastes up to 200 characters, such as an interview answer, and gets TTS, recording and scoring on any of the 4 patterns it contains. Canada-only words are never targeted.
- SPEC §5.4, §10

### S21 · When scoring is down
**Outcome:** if Azure is down or rate-limited, the attempt is queued with "We'll score this in a moment" and scored automatically later. Listening drills keep working.
- `DB` `attempts.status = queued`; `SCORING` retry worker
- SPEC §10

### S22 · Your data, your control
**Outcome:** the learner can delete one recording, all recordings, or their account, and can export their data.
- `DB` Hard delete reaches Storage within 30 days through a purge job. Confirm encryption at rest
- `TEST` A test that a deleted account leaves no objects in Storage
- SPEC §9

### S23 · Optional daily reminder
**Outcome:** an opt-in reminder by email or web push, off by default.
- SPEC §5.5

### S24 · Copy and tone pass
**Outcome:** an app-wide audit: no "reduce/fix/correct/error/mistake", the accent is always "North American English", L1 features are described as different, and there's a "Canadian features coming soon" note. *(The rules also apply to every card as it's built; this card is the final sweep.)*
- SPEC §3

### S25 · Metrics and cost
**Outcome:** a dashboard showing the north star (focus-pattern mastery change after 4 weeks), abstain rate, "seems wrong" rate per pattern, D7/D30 retention, sessions per week, and cost per user (Azure, TTS, LLM).
- SPEC §11

### S26 · Launch hardening
**Outcome:** the app is ready for real users:
- WCAG AA pass, with text alternatives for all audio
- PWA manifest and install flow
- Upgrade to Next.js 16 (the PostCSS advisory)
- Load test of the scoring service
- SPEC §8, §11

### S28 · Closed beta
**Outcome:** about 50 Nigerian and Ghanaian learners use the app. Each week we review the "seems wrong" reports with spot-checks by a North American English rater, then tune thresholds and bump `scoring_version`.
- **Exit:** abstain rate under 15%, no pattern with a high "seems wrong" rate, privacy policy reviewed
- SPEC §11

### P0 · More test speakers *(people, carried over from Phase 0)*
**Outcome:** fixture clips from Ghanaian speakers, and from genuinely noisy rooms, are added to the scoring tests.

---

## Blocked
Waiting on your accounts. Once unblocked, a card moves to **Ready** at the position shown.

### B1 · Deploy the walking skeleton to staging *(you: Supabase, Vercel, Azure accounts)*
**Outcome:** S01–S05 run on a real HTTPS staging URL.
- Supabase staging project in `ca-central-1`
- Vercel project linked to GitHub (functions in `yul1`)
- Scoring service on Azure Container Apps (Canada Central)
- Hosted secrets in Vercel, GitHub Actions and Container Apps

This also unblocks the **real iPhone Safari and Android Chrome recording test** deferred from Phase 0. **Slot it in right after S05**, so that every later card is demoed on staging too.
- SPEC §8, §10

### B2 · Sign in with Google *(you: Google Cloud OAuth client)*
**Outcome:** a "Continue with Google" button next to the email link. Small once the OAuth client ID and secret exist.
- SPEC §5.1

### B3 · Azure Speech in Canada Central *(you: Azure portal)*
**Outcome:** scoring and TTS use a Canada Central resource instead of the spike's East US 2 one. Needed before staging handles real learners.
- SPEC §8, §13

### B4 · Production environment *(you: accounts, after B1)*
**Outcome:** a production Supabase project, Vercel production environment and Container App, plus production secrets.
- SPEC §8

---

## Later
Phase 6 and post-MVP. Same vertical-slice rules when they start.

### L1 · Vowel measurement and calibration
**Outcome:** the scoring service measures F1/F2 in aligned vowels, picked by label, using several tokens per vowel, dropping impossible values and abstaining when unsure. The diagnostic adds about 15 calibration words (Lobanov parameters per learner), and settings get a "recalibrate" option. Ships together with L2, the first module that uses it.
- SPEC §14

### L2 · Module: *full* vs *fool*
Same-speaker /ʊ/ vs /u/ comparison. · SPEC §14

### L3 · Module: *cat* vs *cut*
Same-speaker /æ/ vs /ʌ/ comparison. · SPEC §14

### L4 · Module: Flapped t
/t/ closure duration and release burst in *water, better*. · SPEC §14

### L5 · Module: Low-back merger (Canadian)
*cot = caught*: same-speaker overlap **and** position near published Canadian norms. Reference audio from en-CA TTS (Clara/Liam). · SPEC §14

### L6 · Module: Canadian raising
Matched pairs (*ice/eyes*, *write/ride*). en-CA TTS works for /aɪ/; **/aʊ/ (*about*) needs human Canadian recordings.** · SPEC §14

### L7 · "Canadian" accent option
Accent label and copy updates; the beta is extended to the new modules. **Exit:** all Phase 6 modules score fairly, with an abstain rate under 15%. · SPEC §14

### Post-MVP ideas
- Intelligibility and Confidence outcome modes
- Animated articulation
- Shadowing drills
- LLM role-play conversations
- Francophone West African L1 track
- Regional packs
- Paywall (entitlements are already in place from S04)
- Final consonant clusters
- Intonation

---

## Done
*(Phase 0 is recorded in [CHECKLIST.md](CHECKLIST.md).)*
