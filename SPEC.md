# "Maple" (working name), a North American English accent app for West African newcomers to Canada

> **Strategy (decided 2026-10-29):** the MVP teaches **North American English**, scored with Azure's fully supported `en-US` models. US and Canadian English share almost every sound the MVP teaches. The MVP has the **4 modules Azure can judge reliably**. Everything that needs custom measurement is deferred to **Phase 6** (§14), which starts after the MVP is built. That covers the Canada-only features (the *cot = caught* merger and Canadian raising) plus *full/fool*, *cat/cut* and flapped t, which Azure misses (§13.1).

## 1. Product summary
A free progressive web app (PWA) that helps Nigerian and Ghanaian English speakers who are moving to or living in Canada **add a North American English accent to their toolkit**. The app runs a diagnostic first, then builds an adaptive plan. Learners practise with minimal-pair listening and scored read-aloud drills. Every recording is scored server-side, and feedback combines side-by-side playback, articulation illustrations and plain-language tips that take the learner's first language (L1) into account.

### Goals
- Measurable movement toward North American pronunciation on the 4 target sound patterns.
- Learners can pick an outcome mode: **Native-likeness** (built first), **Intelligibility**, or **Confidence** (the last two come after the MVP).
- Feedback must feel fair to the learner. The app never penalizes a learner for its own uncertainty.

### Non-goals (MVP)
- Patterns that need custom measurement (see §14): the low-back merger, Canadian raising, *full/fool*, *cat/cut* and flapped t.
- Custom vowel measurement and per-user vowel calibration (§14).
- Regional accents (US or Canadian), and Québec English.
- Francophone West African learners, and other L1 groups.
- Live, in-browser visuals while the learner speaks; scoring of free conversation or role-play; offline mode; payments.

## 2. Users
- **Primary:** adult Nigerian (Yoruba, Igbo, Hausa, Pidgin backgrounds) and Ghanaian (Twi, Ewe, Ga backgrounds) English speakers. They are typically fluent English users who want to sound North American for job interviews, the workplace and everyday life in Canada.
- The app assumes decent connectivity and a modern mobile or desktop browser (it uses a standard web-app design).

## 3. Tone and framing: "accent expansion"
- Copy never uses "reduce", "fix", "correct", "bad accent" or "error". Use "North American target", "try the North American way", "match" and "closer to the target".
- The accent is always called **"North American English"** in the product. Never call it "American" or "Canadian" until the Canadian iteration ships.
- L1 features are described as *different*, not *wrong*. For example: "In Nigerian English, 'ship' and 'sheep' often sound the same. North Americans keep them apart."
- The visual style is adult and professional, with minimal gamification.

## 4. Target sound patterns (MVP: 4 modules)
Every MVP module is a sound that US and Canadian English share, that Nigerian/Ghanaian English pronounces differently, **and** that Azure `en-US` scores reliably (§13.1):

| # | Module | North American target | Typical NG/GH pattern |
|---|---|---|---|
| 1 | Rhotic R | r-coloured vowels in *worker, bird, teacher, first* | non-rhotic, with /ɜ/ realized as [ɛ]/[a] |
| 2 | TH sounds | /θ ð/ in *think, this* | stopped to [t d] |
| 3 | *ship* vs *sheep* | /ɪ/ vs /i/ | merged |
| 4 | Schwa and word stress | reduced unstressed vowels, stress-timed rhythm | full vowels, syllable-timed, different stress placement |

Content rules:
- **Rhotic R** scores the r-coloured vowel (/ɝ ɚ/: *bird, worker*). Words where r only ends the syllable after another vowel (*car, park*) are never scored targets, because Azure misses a dropped r there (§13.1). They can still appear in sentences.
- **Schwa** prefers words where the full-vowel version is clearly different (*support, police, banana*), and uses generous "close" bands.
- Content avoids words where US and Canadian English differ (*cot/caught* pairs, and words that hinge on raising such as *about* and *ice*), so nothing taught now has to be unlearned later.

Later candidates: final consonant clusters, intonation; the custom-measurement patterns in §14.

## 5. Core user flows

### 5.1 Onboarding (an account is required upfront)
1. Sign up with Google or an email magic link, and accept the consent screens. Consent for storing recordings is required for the app to work; consent for training use is a separate, optional opt-in that is off by default.
2. Profile: L1 background (Nigerian or Ghanaian, plus an optional home language) and goal mode (only Native-likeness is enabled in the MVP; the other two show "coming soon").
3. **Mic check:** record 3 seconds of silence and 1 sentence to estimate the noise floor and signal-to-noise ratio (SNR), with guidance if the environment is noisy.
4. **Diagnostic (~5 min):**
   - About 10 diagnostic sentences that cover the 4 target patterns.
   - About 10 minimal-pair listening items, to test perception separately from production.
5. Results: a per-pattern score (perception and production) and the top 3 focus areas, shown with encouraging framing.

### 5.2 Daily session (~10 min)
The adaptive engine builds a queue:
- **Spaced-repetition (SRS) review** of weak words and sounds that are due.
- **The current focus module:** perception first (a minimal-pair listening drill must reach ≥80% before production drills unlock), then production (minimal-pair read-aloud, then read-aloud sentences).
- Sentences come from three content domains: **job interviews and workplace**, **everyday life in Canada** (coffee shop, transit, bank, doctor, small talk), and **the learner's own text**.

### 5.3 Drill interaction (read-aloud)
1. The learner sees the target text. Target sounds are subtly underlined.
2. They tap to hear the North American text-to-speech (TTS) reference, with 1.0× and 0.75× speed.
3. They record with tap-to-start and tap-to-stop, plus auto-stop after 1.5 s of silence. The maximum length is 15 s.
4. They upload and wait about 1–3 s for scoring (a spinner with "Listening…").
5. Results:
   - Word-level colouring (match / close / try again) for the words that carry the target sound.
   - **Side-by-side playback:** their clip and the reference, both aligned to the tapped word.
   - An **articulation illustration** for the target sound (static SVGs in the MVP; animation later).
   - **A coaching tip:** one or two sentences, aware of the learner's L1 and generated by an LLM from structured error data. Example: "Your 'th' in *think* sounded like 't'. Let your tongue tip rest lightly between your teeth and blow air."
6. Retry, or move to the next drill.

### 5.4 Your own text
The learner pastes up to 200 characters, for example an interview answer. The app generates TTS for it, splits it into sentences and scores it the same way. Feedback highlights any of the 4 patterns found in that text.

### 5.5 Progress
- A mastery chart per pattern over time.
- **"You, week 1 vs now":** replay a diagnostic recording beside the latest attempt on the same sentence.
- Re-diagnosis is offered every 3 weeks, using a shortened diagnostic.
- No streaks or badges. There is an optional daily reminder (web push or email), off by default.

## 6. Scoring architecture (all server-side)

### 6.1 Pipeline per attempt
1. **Ingest:** the browser records with MediaRecorder (Opus/WebM) and uploads to `POST /attempts`. The server converts the audio to 16 kHz mono WAV.
2. **Quality gate:** voice activity detection (VAD), SNR estimate, clipping check and duration check. If the recording fails, the result is **abstain** with a specific reason.
3. **Pronunciation API:** Azure Pronunciation Assessment with locale **`en-US`**, a scripted reference text, phoneme granularity and the SAPI phoneme alphabet. It returns phoneme, word and fluency accuracy, phoneme labels, the recognized words and timestamps.
4. **Pattern mapping:** each module defines which phonemes in which target words it checks (for example, module 2 checks /θ ð/ in the underlined words). The app takes Azure's accuracy scores for only those phonemes, found by label inside the target word, never by position.
5. **Labels:** a rules-based mapping turns those phoneme scores into a per-target-word label (match / close / try again) plus a 0–100 pattern score. Thresholds live in versioned config so they can be tuned.
6. **Coaching tip:** an LLM receives structured JSON (L1, pattern, observed vs target, word) and returns a short, constrained tip from a vetted tip template library. The LLM rephrases and personalizes the template; it does not invent phonetics.

### 6.2 Low confidence: abstain, never punish
Abstain (show no score) when any of these is true:
- The quality gate fails (noise, clipping, too quiet, too short).
- Recognized words differ from the reference (word error rate above 30%). The app says: "It sounded like you said '…'. Try reading the sentence as shown."
- The API's confidence or alignment on a target word is low. That word is shown as "unclear" and left out of mastery updates.
Abstained attempts never lower mastery.

### 6.3 Fairness safeguards
Known risk: commercial scorers under-score African-accented speakers. To counter it:
- Score only the target sounds of the current pattern. Other differences are not flagged.
- Use generous "close" bands at launch.
- Every result has a **"This doesn't seem right"** button, which logs the attempt (with consent) for review.

## 7. Adaptive engine
- **Mastery model:** each of the 4 patterns has a perception score and a production score (an exponentially weighted moving average of non-abstained attempts). Words carry SRS state using SM-2-style intervals.
- **Plan:** focus on the lowest-mastery pattern, weighted by how much it matters for native-likeness. A pattern is "mastered" at ≥80 production over the last 15 attempts, across at least 2 sessions.
- **Re-diagnosis:** every 3 weeks, or on demand. It recomputes priorities.
- **Outcome modes (post-MVP):** each mode is a different weight vector over the patterns and thresholds. For example, Intelligibility up-weights TH, stress and rhoticity. Design the engine so a mode is just config.
- **Accent targets are config too:** patterns carry an accent tag (`shared`, later `canadian`), so the Canadian iteration adds patterns without changing the engine.

## 8. Technical architecture
- **Frontend:** Next.js (App Router, TypeScript) PWA, with installable manifest. Audio uses MediaRecorder (Opus), with an explicit permission flow and Safari fallbacks (`audio/mp4`). Styling is Tailwind, and the UI must be accessible (WCAG AA, captions or text for all audio prompts).
- **Backend API:** Next.js route handlers or a small Node BFF for auth and session data, plus a **Python FastAPI scoring service** (Azure Speech SDK, numpy and ffmpeg; Parselmouth comes in Phase 6).
- **Data:** Postgres (users, consents, attempts, scores, mastery, SRS state, content). Recordings and TTS cache live in S3-compatible object storage.
- **Hosting:** Canadian region (ca-central) for data residency. The production Azure Speech resource is created in **Canada Central**; the `en-US` locale works from any region.
- **Auth:** Auth.js with Google and email magic link.
- **TTS:** two Azure Neural TTS `en-US` voices, one female and one male, picked in Phase 0. The learner chooses which; responses are cached by text hash.
- **LLM:** Claude (latest Sonnet-class model) for tips, with strict JSON output and a template-constrained prompt.
- **Jobs:** a queue for TTS generation, account deletion and nightly aggregation.

### Key entities
`User` (L1, goal_mode, voice_pref), `Consent` (type, version, granted_at, revoked_at), `ContentItem` (text, domain, patterns, target_word_spans, tts_audio_key), `Pattern` (id, accent_tag, target_phonemes, thresholds), `Attempt` (item, audio_key, status = scored|abstained, abstain_reason, api_raw, labels, scoring_version), `PatternMastery`, `SrsCard`, `FeedbackReport`, `Entitlement`.

### Future paywall readiness
- Every feature checks `entitlements(user)`. In the MVP everyone gets the `free_all` plan.
- Usage metering: attempts per day, TTS characters and API seconds, recorded per user.
- A soft rate limit protects costs: 300 attempts per user per day.

## 9. Privacy and data
- **Recordings are kept**, so learners can play back their progress. Learners can delete a single recording, all recordings, or their account. A hard delete covers object storage within 30 days.
- **Training-use consent** is a separate opt-in, revocable at any time.
- **Compliance:** PIPEDA, Nigeria Data Protection Act 2023 and Ghana Data Protection Act. Cross-border transfer is disclosed. Audio is encrypted at rest. There is a data export feature.
- Audio is sent to Azure for scoring; this is disclosed in the privacy policy. Raw audio is never sent to the LLM; it receives text and structured data only.

## 10. Edge cases
- **Mic denied or unavailable:** listening drills are still usable, with an explainer on how to enable the mic.
- **iOS Safari:** the MediaRecorder MIME type differs. The browser may suspend the AudioContext, so recording must start from a user gesture.
- **Bluetooth headsets:** the low-quality HFP profile trips the SNR gate. The app suggests using the phone mic.
- **The learner reads the wrong sentence, code-switches into Pidgin, or laughs or coughs:** the attempt goes through the WER gate and abstains.
- **Learners who already produce North American features:** the diagnostic marks the pattern as mastered and skips it.
- **Own text with names, numbers or acronyms:** TTS normalization handles them, and target spans are computed only on dictionary words.
- **Own text that contains Canada-only words** (*about, caught*): those words are never marked as targets in the MVP.
- **US TTS mispronounces a Canadian place name:** keep an SSML phoneme override list (*Toronto, Saskatchewan, Etobicoke*).
- **The scoring API is down or rate limited:** the attempt is queued, with "We'll score this in a moment", and listening drills keep working.
- **Duplicate or rapid submissions:** idempotency key per attempt.

## 11. Analytics and success metrics
- **North star:** the change in production mastery on focus patterns after 4 weeks, for active learners.
- **Health metrics:** abstain rate (target under 15%), "this seems wrong" rate per pattern, D7 and D30 retention, and sessions per week.
- **Beta validation:** a closed beta with about 50 Nigerian and Ghanaian learners. Tune thresholds from the "seems wrong" reports and from spot-checks by a North American English rater on flagged attempts.

## 12. MVP scope (~8–9 weeks)
- **Weeks 1–2:** finish Phase 0 checks, recording pipeline, quality gate, auth and consent, data model.
- **Weeks 3–4:** Azure en-US integration, pattern mapping, labels and abstain logic, and the diagnostic flow.
- **Weeks 5–6:** 4 modules of content (about 30 minimal pairs and 25 sentences per module across the 3 domains), listening drills, read-aloud UI, feedback panel, static articulation SVGs and LLM tips.
- **Weeks 7–8:** adaptive engine and SRS, progress page with week-1-vs-now, own-text mode, deletion and export.
- **Week 9:** closed beta, threshold tuning, accessibility pass.

### Post-MVP
- **The Canadian iteration (§14) comes first.** After it: Intelligibility and Confidence modes, animated articulation, shadowing, LLM role-play conversations, more L1 groups (Francophone West African first), regional packs, paywall.

## 13. Open questions and risks
1. ~~Does Azure `en-US` catch the errors we teach?~~ **Resolved (2026-10-29, `scoring/spike/sensitivity_spike.py`).**
   - **Method:** two en-US TTS voices said each test word twice, normally and with the typical NG/GH sound forced through SSML. We then checked the measured audio, to rule out cases where the TTS ignored the override, and cross-checked against Tolu's real recordings.
   - **Reliable:** TH (*think* as "tink" → 19–25), *ship/sheep* (→ 27–36), and r in r-coloured vowels (*worker* without r → 0).
   - **Partly reliable:** schwa (*support* with a full vowel drops ~45; *today* barely changes).
   - **Misses:**
     - A dropped r after a vowel at the end of a syllable (*car* → 69/97).
     - *full/fool*: Tolu's merged *full* scored 100.
     - *cat/cut*: partial at best (Tolu's back *cat* → 63–84; *cut* said "cawt" → 79–100).
     - Flapped t: Tolu's fully released t in *water* scored 100.
   - **Decision:** the MVP keeps the 4 reliable modules. *full/fool*, *cat/cut* and flapped t move to Phase 6, where custom same-speaker checks can judge them (§14).
2. **Validation relies only on beta feedback;** there is no human-rated benchmark before launch. That increases the risk of unfair scores at launch, which is only partly mitigated by abstaining and generous bands.
3. **Content needs review** by a Nigerian or Ghanaian English speaker and by a North American English phonetics reviewer, for accuracy and tone.
4. **Learner expectations:** users are moving to Canada and may expect a Canadian accent. The "North American English" label and a "Canadian features coming soon" note set expectations honestly.

## 14. Phase 6: custom measurement and the Canadian iteration (deferred)
After the MVP is built, add our own acoustic measurements. They unlock the patterns Azure can't judge, then a Canadian layer on top of the North American base.

**What it adds:**
- **Three North American modules Azure misses:**
  - *full* vs *fool*: compare the learner's own /ʊ/ and /u/ vowels.
  - *cat* vs *cut*: compare /æ/ and /ʌ/ positions.
  - Flapped t: the /t/ closure in *water* and *better* should be a short tap, under about 30 ms, with no release burst.
- **Two Canada-only modules:** the low-back merger (*cot = caught*, *Don = dawn*) and Canadian raising (*ice*, *about*, *writer*).
- **A custom vowel-measurement layer** (Python + Parselmouth): F1/F2 at fixed points in each Azure-aligned vowel, distance to published General Canadian norms, and same-speaker comparisons (*ice* vs *eyes*, *Don* vs *caught*).
- **Per-user vowel calibration:** about 15 words in the diagnostic, used to Lobanov-normalize each learner's vowels.
- **Canadian reference audio** for the new modules, plus a "Canadian" option in the accent label.

**What Phase 0 already found (2026-10-29), to reuse then:**
- **Azure `en-CA`** returns phoneme scores and timings but **no phoneme labels**, and it scores like `en-US`: it treats *caught* as /ɔ/ and *ice* as plain /aɪ/. Canadian features must be judged by the custom layer, with `en-US` used only for alignment.
- **Formant measurement** worked on 100% of aligned vowels (157 vowels, 1 speaker). Single measurements vary a lot between takes, so use several tokens per vowel, drop impossible values, and abstain when unsure.
- **Pick the target vowel by phoneme label, never by position.** In *about*, the first vowel is the schwa, not /aʊ/.
- **en-CA TTS:** only `en-CA-ClaraNeural` (F) and `en-CA-LiamNeural` (M) exist.
  - Both merge *cot/caught* and clearly raise /aɪ/: the onset F1 drops 84–254 Hz before voiceless consonants.
  - **Neither reliably raises /aʊ/** (*about, out, house*). The *about* drills need a human Canadian recording.
  - Scoring targets come from published norms, never from TTS.
- **Content rule:** every raising drill needs matched pairs (*ice/eyes*, *write/ride*, *price/prize*).
- The spike scripts are kept in `scoring/spike/` (`azure_spike.py`, `tts_spike.py`).
