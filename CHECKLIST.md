# Maple: Phased Build Checklist

Derived from [SPEC.md](SPEC.md). Section references (§) point back to the spec. Each phase ends with an exit gate. Don't start the next phase until the gate passes.

---

## Phase 0: Spike and setup (Week 1)

Goal: retire the biggest technical unknowns before building anything on them.

### Risk spikes
- [ ] Azure Pronunciation Assessment `en-CA`: confirm it returns phoneme-level accuracy and timestamps (§6.1, §13.1)
  - [ ] If not: confirm the `en-US` fallback gives usable alignment for Canadian target words
- [ ] Record 5–10 test clips from Nigerian and Ghanaian speakers on phone mics (quiet room and noisy room)
- [ ] Run Parselmouth formant extraction on those clips and judge measurement stability (§13.3)
- [ ] Azure Neural TTS `en-CA`: pick 1 male and 1 female voice; listen-test for Canadian raising and for *Toronto/Saskatchewan* (§8, §10)
- [ ] MediaRecorder: confirm the format each browser records in (Chrome/Android Opus, iOS Safari `audio/mp4`) and that the server can convert it (§10)
- [ ] Write up the spike results and adjust the scoring design if needed

### Project setup
- [x] Monorepo: `web/` (Next.js App Router, TypeScript, Tailwind) and `scoring/` (FastAPI, Python)
- [ ] Postgres and S3-compatible storage, hosted in ca-central (§8)
- [ ] Lint, format and test tooling in CI for both apps
- [ ] Secrets management for the Azure, LLM and auth keys
- [ ] Environments: local, staging, prod

**Exit gate:** the spike confirms the hybrid scoring approach is viable, or SPEC.md has been revised to fit what the spike found.

---

## Phase 1: Foundations (Weeks 1–2)

### Auth and consent (§5.1, §9)
- [ ] Auth.js with Google and email magic link; an account is required before any app use
- [ ] `Consent` table that is versioned and records when each consent was granted and revoked
- [ ] Required consent screen for recording storage
- [ ] Optional training-use consent, off by default and revocable in settings
- [ ] Draft the privacy policy: Azure processing, cross-border transfer, PIPEDA / Nigeria Data Protection Act 2023 / Ghana Data Protection Act

### Data model (§8)
- [ ] `User` (L1, goal_mode, voice_pref, lobanov_params)
- [ ] `ContentItem`, `Attempt`, `PatternMastery`, `SrsCard`, `FeedbackReport`, `Entitlement`
- [ ] Migrations and seed script

### Paywall readiness (§8)
- [ ] `entitlements(user)` check wrapper; every user gets the `free_all` plan
- [ ] Per-user usage metering (attempts per day, TTS characters, API seconds)
- [ ] Soft rate limit of 300 attempts per user per day

### Recording pipeline (§6.1 steps 1–2)
- [ ] Recorder component: tap-to-start/stop, auto-stop after 1.5 s of silence, 15 s max, starts from a user gesture
- [ ] Mic permission flow, plus fallback when the mic is denied (listening-only mode) (§10)
- [ ] `POST /attempts` with an idempotency key; upload to object storage (§10)
- [ ] Server-side conversion to 16 kHz mono WAV
- [ ] Quality gate: voice activity detection, signal-to-noise estimate, clipping and duration checks, each with a specific abstain reason
- [ ] Hint for Bluetooth headsets when the signal-to-noise check fails (§10)

**Exit gate:** a signed-in user can record, upload and get back either a pass or a specific abstain reason from the quality gate.

---

## Phase 2: Scoring engine (Weeks 3–5)

### Pronunciation API integration (§6.1 step 3)
- [ ] Azure Pronunciation Assessment call with a scripted reference text
- [ ] Persist the raw API response (`api_raw`) and `scoring_version`
- [ ] Word error rate check: abstain above 30% and show "It sounded like you said…" (§6.3)
- [ ] Mark low-confidence words as "unclear" and leave them out of mastery
- [ ] If the API is down or rate-limited: queue the attempt and show "We'll score this in a moment" (§10)

### Canadian reference distributions (§6.2)
- [ ] Gather published General Canadian vowel norms
- [ ] Measure formants from the en-CA TTS voices as a sanity check
- [ ] Store normalized target means and covariances in versioned config

### Canadian feature layer (§6.1 step 4)
- [ ] Locate target segments using the API's alignment
- [ ] Vowels: F1/F2 at the 20/50/80% points, Lobanov normalization, distance to the Canadian target
- [ ] Canadian raising: nucleus F1 before voiceless vs voiced consonants
- [ ] Low-back merger: overlap of the learner's own LOT and THOUGHT tokens
- [ ] Rhoticity: F3 lowering
- [ ] TH: frication vs stop-burst heuristic combined with the API's phoneme score
- [ ] Schwa and stress: duration, intensity and pitch ratios compared with the TTS reference
- [ ] Flapping: closure duration of /t/ between vowels
- [ ] Unit tests on the recorded fixture clips from Phase 0

### Fusion and fairness (§6.1 step 5, §6.4)
- [ ] Rules mapping each target word to match / close / try again, plus a 0–100 pattern score
- [ ] Thresholds kept in versioned config, with generous "close" bands at launch
- [ ] Score only the target sounds of the current pattern
- [ ] Abstained attempts never lower mastery (§6.3)

### Calibration and diagnostic (§5.1)
- [ ] Mic check: 3 s of silence plus 1 sentence, with noise guidance
- [ ] Vowel calibration: 15 words, compute and store the user's Lobanov parameters
- [ ] About 12 diagnostic sentences covering all 8 patterns
- [ ] About 10 minimal-pair perception items
- [ ] Results screen: per-pattern perception and production scores, top 3 focus areas, encouraging copy
- [ ] Profile step: L1 (Nigerian/Ghanaian plus optional home language) and goal mode (only Native-likeness enabled)

**Exit gate:** a new user can finish onboarding, the diagnostic produces per-pattern scores, and the abstain rate on the fixture clips is under 15%.

---

## Phase 3: Content and practice UI (Weeks 6–8)

### Content (§4, §5.2)
- [ ] For each of the 8 modules: about 30 minimal pairs and 25 sentences
  - [ ] 1 Rhotic R
  - [ ] 2 TH sounds
  - [ ] 3 *ship* vs *sheep*
  - [ ] 4 *full* vs *fool*
  - [ ] 5 Schwa and word stress
  - [ ] 6 *cat / cut / cot*
  - [ ] 7 Low-back merger
  - [ ] 8 Canadian raising and flapping
- [ ] Spread the sentences across the job/workplace and everyday-life domains
- [ ] Tag target word spans for each item
- [ ] Pre-generate TTS for both voices, cached by text hash
- [ ] SSML phoneme override list for place names (§10)
- [ ] Content review by a Nigerian/Ghanaian English speaker and a Canadian English phonetics reviewer (§13.5)

### Listening drills (§5.2)
- [ ] Minimal-pair perception drill
- [ ] Perception gate: production drills unlock at ≥80%

### Read-aloud drill (§5.3)
- [ ] Target text with target sounds underlined
- [ ] Reference playback at 1.0× and 0.75×
- [ ] "Listening…" state while scoring
- [ ] Word-level colouring of the result
- [ ] Side-by-side playback (learner vs reference) aligned to the tapped word
- [ ] Static articulation SVG for each target sound
- [ ] Retry and Next controls
- [ ] "This doesn't seem right" button that logs a `FeedbackReport` (§6.4)

### Coaching tips (§6.1 step 6)
- [ ] Vetted tip template library per pattern and L1
- [ ] LLM call (Claude, Sonnet-class) with structured JSON in and strict JSON out, constrained to the templates
- [ ] Confirm no audio ever goes to the LLM (§9)
- [ ] Fallback to the raw template when the LLM fails

### Copy and tone (§3)
- [ ] Copy audit: no "reduce", "fix", "correct", "error" or "bad accent"
- [ ] L1 features described as different, not wrong

**Exit gate:** all 8 modules can be played end to end, perception then production, with feedback.

---

## Phase 4: Adaptive engine and progress (Weeks 9–10)

### Adaptive engine (§7)
- [ ] Per-pattern perception and production mastery as an exponentially weighted moving average of non-abstained attempts
- [ ] SM-2-style spaced-repetition state per word
- [ ] Daily session builder (~10 min): review cards that are due, then the current focus module
- [ ] Focus selection: lowest mastery, weighted by importance for native-likeness
- [ ] Mastered rule: ≥80 production over the last 15 attempts, across at least 2 sessions
- [ ] Skip patterns already mastered in the diagnostic (§10)
- [ ] Outcome modes stored as config weight vectors (only Native-likeness active)

### Re-diagnosis (§5.5, §7)
- [ ] Shortened diagnostic offered every 3 weeks or on demand
- [ ] Refresh calibration, plus a manual "recalibrate" option (§10)

### Own text (§5.4)
- [ ] Paste up to 200 characters, split into sentences, generate TTS
- [ ] Detect which of the 8 patterns appear (dictionary words only)
- [ ] Score with the same pipeline as other drills

### Progress (§5.5)
- [ ] Mastery-over-time chart per pattern
- [ ] "You, week 1 vs now" playback
- [ ] Optional daily reminder (web push or email), off by default
- [ ] No streaks or badges

### Data rights (§9)
- [ ] Delete one recording, all recordings, or the account
- [ ] Hard delete from object storage within 30 days (background job)
- [ ] Data export
- [ ] Audio encrypted at rest

**Exit gate:** a full learner loop works: diagnostic, then daily sessions, progress tracking, re-diagnosis and deletion.

---

## Phase 5: Beta and launch prep (Weeks 11–12)

### Quality
- [ ] Accessibility pass to WCAG AA, with text alternatives for all audio prompts
- [ ] Cross-browser QA (iOS Safari, Android Chrome, desktop Chrome, Firefox, Edge)
- [ ] PWA manifest and install flow
- [ ] Load test the scoring service

### Analytics (§11)
- [ ] North star: change in focus-pattern mastery after 4 weeks
- [ ] Abstain rate (target under 15%) and "seems wrong" rate per pattern
- [ ] D7/D30 retention and sessions per week
- [ ] Per-user cost dashboard (Azure, TTS, LLM)

### Closed beta (§11)
- [ ] Recruit about 50 Nigerian and Ghanaian learners
- [ ] Weekly review of "seems wrong" reports, plus spot-checks by a Canadian English rater
- [ ] Tune fusion thresholds, bump `scoring_version`, and re-check
- [ ] Decide on the human-recorded diagnostic sentences (§13.2)

**Exit gate:** abstain rate under 15%, no pattern with a high "seems wrong" rate, privacy policy reviewed, ready for public launch.

---

## Post-MVP backlog (§12)
- [ ] Intelligibility and Confidence outcome modes
- [ ] Animated articulation visuals
- [ ] Shadowing drills
- [ ] LLM role-play conversations
- [ ] Francophone West African L1 track
- [ ] Regional Canadian packs
- [ ] Paywall (entitlements are already in place)
- [ ] Extra sound patterns: final consonant clusters, /æ/ before nasals and /g/, Canadian Shift, intonation
