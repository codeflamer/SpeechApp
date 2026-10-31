# Maple: Phased Build Checklist

Derived from [SPEC.md](SPEC.md). Section references (§) point back to the spec. Each phase ends with an exit gate. Don't start the next phase until the gate passes.

**Strategy:** build the MVP for **North American English** using Azure `en-US`, with the 4 modules Azure scores reliably. Patterns that need custom measurement, including the Canada-only ones, come in Phase 6 (SPEC §14).

---

## Phase 0: Spike and setup (Week 1)

Goal: retire the biggest technical unknowns before building anything on them.

### Risk spikes
- [x] Azure Pronunciation Assessment `en-CA`: does it return phoneme-level data? → scores and timings only, no labels; behaves like `en-US` (SPEC §14)
  - [x] `en-US` returns phoneme scores, labels and timings for all clips
- [~] Record 5–10 test clips from Nigerian and Ghanaian speakers on phone mics (quiet room and noisy room). Partial: 10 clips from 1 Nigerian speaker; still need Ghanaian speakers and genuinely noisy rooms
- [x] Formant measurement on those clips (kept for the Canadian iteration, SPEC §14)
- [x] en-CA TTS check: raising and merger measured (`spike/tts_spike.py`); results recorded for the Canadian iteration (SPEC §14)
- [x] **Azure `en-US` sensitivity** (`spike/sensitivity_spike.py`, SPEC §13.1): reliable for TH, *ship/sheep* and r-coloured vowels; partly reliable for schwa; misses *full/fool*, *cat/cut*, flapped t and a dropped r at the end of a syllable → MVP cut to 4 modules
- [x] en-US TTS: pick 1 female and 1 male voice; listen-test sentences and Canadian place names (SPEC §8, §10)
  - [x] Scored 27 standard voices for clarity and pace (`spike/voice_pick_spike.py`); shortlist Ava, Nancy, Jane / Andrew, Roger, Kai
  - [x] Listen test: picked **Ava** (F) and **Andrew** (M); no place names reported as wrong yet. Revisit in the Phase 3 content review
- [x] MediaRecorder: confirm the format each browser records in (Chrome/Android Opus, iOS Safari `audio/mp4`) and that the server can convert it (SPEC §10)
  - [x] Server converts Chrome-style WebM (no duration header), Firefox Ogg and Safari-style fragmented MP4 to 16 kHz mono (`spike/format_spike.py`)
  - [x] Real Chromium recording: WebM/Opus, 48 kHz stereo, no duration header → converted correctly (test page `web/src/app/spike/recorder`)
  - [x] Real desktop browser with a real mic: several recordings uploaded and converted (all 200 OK)
  - Deferred: real iPhone Safari and Android Chrome recording. It needs HTTPS and is covered by Phase 5 cross-browser QA
- [x] Write up the spike results and adjust the scoring design if needed

### Project setup
- [x] Monorepo: `web/` (Next.js App Router, TypeScript, Tailwind) and `scoring/` (FastAPI, Python)
- [x] Hosting decided: Vercel (`yul1` Montréal) + Supabase (`ca-central-1`) + Azure Container Apps (Canada Central) for scoring (SPEC §8)
- [~] Postgres and storage via Supabase (SPEC §8)
  - [x] Local: `supabase/config.toml` (Postgres 17, 5 MiB file limit); CLI pinned in the root `package.json`
  - [x] Local stack running (`npm run db:start`): Postgres 17.11, Auth, Storage, REST and Studio all respond; `web/.env.local` filled with the local keys
  - [ ] Hosted Supabase projects for staging and prod in Canada (Central) *(you: needs your Supabase account)*
- [ ] Production Azure Speech resource in Canada Central; the spike used East US 2 *(you: Azure portal)*
- [x] CI: GitHub Actions runs web lint, type check and build, plus scoring ruff and pytest (`.github/workflows/ci.yml`). The first run failed at the scoring install (setuptools found both `app` and `spike`); fixed in `pyproject.toml`
- [~] Secrets management
  - [x] `.env.example` templates for `web/` and `scoring/`; real `.env` files are git-ignored
  - [ ] Hosted secrets in Vercel env vars, GitHub Actions secrets and Container Apps secrets, per environment
- [~] Environments: local, staging, prod
  - [x] Local defined (Supabase CLI and `.claude/launch.json`)
  - [ ] Staging and prod: Vercel project linked to the GitHub repo *(you: needs your Vercel account)*
- [x] Security: upgraded to patched Next.js 15.5.28 and React 19.1.10 (CVE-2025-66478)

**Exit gate:** Azure `en-US` catches the target patterns, or SPEC.md has been revised (custom check or module cut) for any it misses. ✅ Met: SPEC revised to 4 modules.

---

## Phase 1: Foundations (Weeks 1–2)

### Auth and consent (SPEC §5.1, §9)
- [ ] Supabase Auth with Google and email magic link; an account is required before any app use
- [ ] Row-level security on every user table, so users only read their own rows
- [ ] Private Storage bucket for recordings; upload through signed upload URLs
- [ ] `Consent` table that is versioned and records when each consent was granted and revoked
- [ ] Required consent screen for recording storage
- [ ] Optional training-use consent, off by default and revocable in settings
- [ ] Draft the privacy policy: Azure processing, cross-border transfer, PIPEDA / Nigeria Data Protection Act 2023 / Ghana Data Protection Act

### Data model (SPEC §8)
- [ ] `User` (L1, goal_mode, voice_pref)
- [ ] `Pattern` with `accent_tag` (`shared` now, `canadian` later), target phonemes and thresholds
- [ ] `ContentItem`, `Attempt`, `PatternMastery`, `SrsCard`, `FeedbackReport`, `Entitlement`
- [ ] Migrations and seed script

### Paywall readiness (SPEC §8)
- [ ] `entitlements(user)` check wrapper; every user gets the `free_all` plan
- [ ] Per-user usage metering (attempts per day, TTS characters, API seconds)
- [ ] Soft rate limit of 300 attempts per user per day

### Recording pipeline (SPEC §6.1 steps 1–2)
- [ ] Recorder component: tap-to-start/stop, auto-stop after 1.5 s of silence, 15 s max, starts from a user gesture
- [ ] Mic permission flow, plus fallback when the mic is denied (listening-only mode) (SPEC §10)
- [ ] `POST /attempts` with an idempotency key; upload to object storage (SPEC §10)
- [ ] Server-side conversion to 16 kHz mono WAV; measure duration on the decoded WAV, never the upload header (SPEC §10)
- [ ] Quality gate: voice activity detection, signal-to-noise estimate, clipping and duration checks, each with a specific abstain reason
- [ ] Hint for Bluetooth headsets when the signal-to-noise check fails (SPEC §10)

**Exit gate:** a signed-in user can record, upload and get back either a pass or a specific abstain reason from the quality gate.

---

## Phase 2: Scoring engine (Weeks 3–4)

### Azure `en-US` integration (SPEC §6.1 step 3)
- [ ] Pronunciation Assessment call: scripted reference text, phoneme granularity, SAPI alphabet
- [ ] Credential check at service startup (reuse `check_credentials` from the spike)
- [ ] Persist the raw API response (`api_raw`) and `scoring_version`
- [ ] Word error rate check: abstain above 30% and show "It sounded like you said…" (SPEC §6.2)
- [ ] Mark low-confidence words as "unclear" and leave them out of mastery
- [ ] If the API is down or rate-limited: queue the attempt and show "We'll score this in a moment" (SPEC §10)

### Pattern mapping and labels (SPEC §6.1 steps 4–5, §6.3)
- [ ] Per-module target phonemes in versioned config
- [ ] Pick target phonemes by label inside the target words, never by position
- [ ] Rules mapping each target word to match / close / try again, plus a 0–100 pattern score
- [ ] Thresholds kept in versioned config, with generous "close" bands at launch
- [ ] Score only the target sounds of the current pattern
- [ ] Abstained attempts never lower mastery (SPEC §6.2)
- [ ] Unit tests on the recorded fixture clips from Phase 0

### Diagnostic (SPEC §5.1)
- [ ] Mic check: 3 s of silence plus 1 sentence, with noise guidance
- [ ] About 10 diagnostic sentences covering all 4 patterns
- [ ] About 10 minimal-pair perception items
- [ ] Results screen: per-pattern perception and production scores, top 3 focus areas, encouraging copy
- [ ] Profile step: L1 (Nigerian/Ghanaian plus optional home language) and goal mode (only Native-likeness enabled)

**Exit gate:** a new user can finish onboarding, the diagnostic produces per-pattern scores, and the abstain rate on the fixture clips is under 15%.

---

## Phase 3: Content and practice UI (Weeks 5–6)

### Content (SPEC §4, §5.2)
- [ ] For each of the 4 modules: about 30 minimal pairs and 25 sentences
  - [ ] 1 Rhotic R: score r-coloured vowels (*bird, worker*); never score a syllable-final r (*car*) (SPEC §4)
  - [ ] 2 TH sounds
  - [ ] 3 *ship* vs *sheep*
  - [ ] 4 Schwa and word stress: prefer clear cases (*support, police*)
- [ ] Spread the sentences across the job/workplace and everyday-life-in-Canada domains
- [ ] Tag target word spans for each item; never target Canada-only words (*about*, *caught*…)
- [ ] Pre-generate TTS for both en-US voices, cached by text hash
- [ ] SSML phoneme override list for Canadian place names (SPEC §10)
- [ ] Content review by a Nigerian/Ghanaian English speaker and a North American English phonetics reviewer (SPEC §13.3)

### Listening drills (SPEC §5.2)
- [ ] Minimal-pair perception drill
- [ ] Perception gate: production drills unlock at ≥80%

### Read-aloud drill (SPEC §5.3)
- [ ] Target text with target sounds underlined
- [ ] Reference playback at 1.0× and 0.75×
- [ ] "Listening…" state while scoring
- [ ] Word-level colouring of the result
- [ ] Side-by-side playback (learner vs reference) aligned to the tapped word
- [ ] Static articulation SVG for each target sound
- [ ] Retry and Next controls
- [ ] "This doesn't seem right" button that logs a `FeedbackReport` (SPEC §6.3)

### Coaching tips (SPEC §6.1 step 6)
- [ ] Vetted tip template library per pattern and L1
- [ ] LLM call (Claude, Sonnet-class) with structured JSON in and strict JSON out, constrained to the templates
- [ ] Confirm no audio ever goes to the LLM (SPEC §9)
- [ ] Fallback to the raw template when the LLM fails

### Copy and tone (SPEC §3)
- [ ] Copy audit: no "reduce", "fix", "correct", "error" or "bad accent"
- [ ] The accent is always called "North American English"; add a "Canadian features coming soon" note
- [ ] L1 features described as different, not wrong

**Exit gate:** all 4 modules can be played end to end, perception then production, with feedback.

---

## Phase 4: Adaptive engine and progress (Weeks 7–8)

### Adaptive engine (SPEC §7)
- [ ] Per-pattern perception and production mastery as an exponentially weighted moving average of non-abstained attempts
- [ ] SM-2-style spaced-repetition state per word
- [ ] Daily session builder (~10 min): review cards that are due, then the current focus module
- [ ] Focus selection: lowest mastery, weighted by importance for native-likeness
- [ ] Mastered rule: ≥80 production over the last 15 attempts, across at least 2 sessions
- [ ] Skip patterns already mastered in the diagnostic (SPEC §10)
- [ ] Outcome modes and accent targets stored as config (only Native-likeness and `shared` active)

### Re-diagnosis (SPEC §5.5, §7)
- [ ] Shortened diagnostic offered every 3 weeks or on demand

### Own text (SPEC §5.4)
- [ ] Paste up to 200 characters, split into sentences, generate TTS
- [ ] Detect which of the 4 patterns appear (dictionary words only; skip Canada-only words)
- [ ] Score with the same pipeline as other drills

### Progress (SPEC §5.5)
- [ ] Mastery-over-time chart per pattern
- [ ] "You, week 1 vs now" playback
- [ ] Optional daily reminder (web push or email), off by default
- [ ] No streaks or badges

### Data rights (SPEC §9)
- [ ] Delete one recording, all recordings, or the account
- [ ] Hard delete from object storage within 30 days (background job)
- [ ] Data export
- [ ] Audio encrypted at rest

**Exit gate:** a full learner loop works: diagnostic, then daily sessions, progress tracking, re-diagnosis and deletion.

---

## Phase 5: Beta and launch prep (Week 9)

### Quality
- [ ] Accessibility pass to WCAG AA, with text alternatives for all audio prompts
- [ ] Cross-browser QA (iOS Safari, Android Chrome, desktop Chrome, Firefox, Edge), including real-phone recording and upload (deferred from Phase 0; use `/spike/recorder` on staging)
- [ ] PWA manifest and install flow
- [ ] Upgrade to Next.js 16. `npm audit` flags the PostCSS bundled in Next 15 (build-time only, low real risk), and it's only fixable in 16
- [ ] Load test the scoring service

### Analytics (SPEC §11)
- [ ] North star: change in focus-pattern mastery after 4 weeks
- [ ] Abstain rate (target under 15%) and "seems wrong" rate per pattern
- [ ] D7/D30 retention and sessions per week
- [ ] Per-user cost dashboard (Azure, TTS, LLM)

### Closed beta (SPEC §11)
- [ ] Recruit about 50 Nigerian and Ghanaian learners
- [ ] Weekly review of "seems wrong" reports, plus spot-checks by a North American English rater
- [ ] Tune thresholds, bump `scoring_version`, and re-check

**Exit gate:** abstain rate under 15%, no pattern with a high "seems wrong" rate, privacy policy reviewed, ready for public launch.

---

## Phase 6: Custom measurement and the Canadian iteration (after the MVP; SPEC §14)

### Vowel measurement layer
- [ ] Turn the spike's formant code into a scoring module: F1/F2 at fixed points in each aligned vowel, picked by label
- [ ] Several tokens per vowel, impossible values dropped, abstain when unsure
- [ ] Gather published General Canadian vowel norms; store target means and covariances in versioned config

### Calibration
- [ ] About 15 calibration words added to the diagnostic; store each user's Lobanov parameters (`User.lobanov_params`)
- [ ] Refresh calibration at re-diagnosis, plus a manual "recalibrate" option

### North American modules Azure misses
- [ ] *full* vs *fool*: same-speaker /ʊ/ vs /u/ comparison
- [ ] *cat* vs *cut*: same-speaker /æ/ vs /ʌ/ comparison
- [ ] Flapped t: /t/ closure duration and release burst in *water, better*
- [ ] Content and reference audio for all three (`accent_tag = shared`)

### Canada-only modules
- [ ] Low-back merger (*cot = caught*): same-speaker overlap **and** position near the Canadian target
- [ ] Canadian raising: onset F1 of the same diphthong before voiceless vs voiced consonants, using matched pairs (*ice/eyes*, *write/ride*)
- [ ] Content for both modules (`accent_tag = canadian`)
- [ ] Reference audio: en-CA TTS (Clara/Liam) for the merger and /aɪ/ raising; **human Canadian recordings** for /aʊ/ (*about*)

### Product
- [ ] "Canadian" accent option and label; update copy
- [ ] Unit tests on fixture clips; extend the beta to the new modules

**Exit gate:** all five new modules score fairly in a beta, with an abstain rate under 15%.

---

## Post-MVP backlog
- [ ] Intelligibility and Confidence outcome modes
- [ ] Animated articulation visuals
- [ ] Shadowing drills
- [ ] LLM role-play conversations
- [ ] Francophone West African L1 track
- [ ] Regional packs
- [ ] Paywall (entitlements are already in place)
- [ ] Extra sound patterns: final consonant clusters, intonation
