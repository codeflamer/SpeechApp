# "Maple" (working name), a Canadian accent app for West African newcomers

## 1. Product summary
A free progressive web app (PWA) that helps Nigerian and Ghanaian English speakers who are moving to or living in Canada **add a General Canadian English accent to their toolkit**. The app runs a diagnostic first, then builds an adaptive plan. Learners practise with minimal-pair listening and scored read-aloud drills. Every recording is scored server-side, and feedback combines side-by-side playback, articulation illustrations and plain-language tips that take the learner's first language (L1) into account.

### Goals
- Measurable movement toward General Canadian pronunciation on the 8 target sound patterns.
- Learners can pick an outcome mode: **Native-likeness** (built first), **Intelligibility**, or **Confidence** (the last two come after the MVP).
- Feedback must feel fair to the learner. The app never penalizes a learner for its own uncertainty.

### Non-goals (MVP)
- Regional Canadian accents (Newfoundland, Maritimes, Ottawa Valley), and Québec English.
- Francophone West African learners, and other L1 groups.
- Live, in-browser visuals while the learner speaks; scoring of free conversation or role-play; offline mode; payments.

## 2. Users
- **Primary:** adult Nigerian (Yoruba, Igbo, Hausa, Pidgin backgrounds) and Ghanaian (Twi, Ewe, Ga backgrounds) English speakers. They are typically fluent English users who want to sound Canadian for job interviews, the workplace and everyday life.
- The app assumes decent connectivity and a modern mobile or desktop browser (it uses a standard web-app design).

## 3. Tone and framing: "accent expansion"
- Copy never uses "reduce", "fix", "correct", "bad accent" or "error". Use "Canadian target", "try the Canadian way", "match" and "closer to Canadian".
- L1 features are described as *different*, not *wrong*. For example: "In Nigerian English, 'ship' and 'sheep' often sound the same. Canadians keep them apart."
- The visual style is adult and professional, with minimal gamification.

## 4. Target sound patterns (MVP: 8 modules)
The list is chosen where Nigerian/Ghanaian English and General Canadian differ most:

| # | Module | Canadian target | Typical NG/GH pattern |
|---|---|---|---|
| 1 | Rhotic R | r pronounced in *car, worker, bird* | non-rhotic, with /ɜ/ realized as [ɛ]/[a] |
| 2 | TH sounds | /θ ð/ in *think, this* | stopped to [t d] |
| 3 | *ship* vs *sheep* | /ɪ/ vs /i/ | merged |
| 4 | *full* vs *fool* | /ʊ/ vs /u/ | merged |
| 5 | Schwa and word stress | reduced unstressed vowels, stress-timed rhythm | full vowels, syllable-timed, different stress placement |
| 6 | *cat / cut / cot* | /æ/, /ʌ/, merged LOT/THOUGHT | /a/ for /æ/, /ɔ/ for /ʌ/ |
| 7 | Low-back merger | *cot* = *caught*, *don* = *dawn* | distinct /ɔ/ |
| 8 | Canadian raising and flapping | [ʌɪ ʌʊ] before voiceless consonants (*ice, about, writer*); flapped t (*water, better*) | unraised diphthongs, released [t] |

Later candidates: final consonant clusters, /æ/ raising before nasals and /g/, Canadian Shift, intonation.

## 5. Core user flows

### 5.1 Onboarding (an account is required upfront)
1. Sign up with Google or an email magic link, and accept the consent screens. Consent for storing recordings is required for the app to work; consent for training use is a separate, optional opt-in that is off by default.
2. Profile: L1 background (Nigerian or Ghanaian, plus an optional home language) and goal mode (only Native-likeness is enabled in the MVP; the other two show "coming soon").
3. **Mic check:** record 3 seconds of silence and 1 sentence to estimate the noise floor and signal-to-noise ratio (SNR), with guidance if the environment is noisy.
4. **Diagnostic (~6–8 min):**
   - Vowel calibration: about 15 single words that span the vowel space (*heed, hid, head, had, hod, hawed, hood, who'd, hud, hide, how'd, height, out, bird, the*). These give the learner's own **Lobanov normalization** baseline.
   - About 12 diagnostic sentences that load the 8 target patterns.
   - About 10 minimal-pair listening items, to test perception separately from production.
5. Results: a per-pattern score (perception and production) and the top 3 focus areas, shown with encouraging framing.

### 5.2 Daily session (~10 min)
The adaptive engine builds a queue:
- **Spaced-repetition (SRS) review** of weak words and sounds that are due.
- **The current focus module:** perception first (a minimal-pair listening drill must reach ≥80% before production drills unlock), then production (minimal-pair read-aloud, then read-aloud sentences).
- Sentences come from three content domains: **job interviews and workplace**, **everyday Canadian life** (coffee shop, transit, bank, doctor, small talk), and **the learner's own text**.

### 5.3 Drill interaction (read-aloud)
1. The learner sees the target text. Target sounds are subtly underlined.
2. They tap to hear the Canadian text-to-speech (TTS) reference, with 1.0× and 0.75× speed.
3. They record with tap-to-start and tap-to-stop, plus auto-stop after 1.5 s of silence. The maximum length is 15 s.
4. They upload and wait about 1–3 s for scoring (a spinner with "Listening…").
5. Results:
   - Word-level colouring (match / close / try again) for the words that carry the target sound.
   - **Side-by-side playback:** their clip and the reference, both aligned to the tapped word.
   - An **articulation illustration** for the target sound (static SVGs in the MVP; animation later).
   - **A coaching tip:** one or two sentences, aware of the learner's L1 and generated by an LLM from structured error data. Example: "Your 'th' in *think* sounded like 't'. Let your tongue tip rest lightly between your teeth and blow air."
6. Retry, or move to the next drill.

### 5.4 Your own text
The learner pastes up to 200 characters, for example an interview answer. The app generates en-CA TTS for it, splits it into sentences and scores it the same way. Feedback highlights any of the 8 patterns found in that text.

### 5.5 Progress
- A mastery chart per pattern over time.
- **"You, week 1 vs now":** replay a diagnostic recording beside the latest attempt on the same sentence.
- Re-diagnosis is offered every 3 weeks, using a shortened diagnostic.
- No streaks or badges. There is an optional daily reminder (web push or email), off by default.

## 6. Scoring architecture (hybrid, all server-side)

### 6.1 Pipeline per attempt
1. **Ingest:** the browser records with MediaRecorder (Opus/WebM) and uploads to `POST /attempts`. The server converts the audio to 16 kHz mono WAV.
2. **Quality gate:** voice activity detection (VAD), SNR estimate, clipping check and duration check. If the recording fails, the result is **abstain** with a specific reason.
3. **Pronunciation API:** Azure Pronunciation Assessment with locale `en-CA` and a scripted reference text. It returns phoneme, word and fluency accuracy, the recognized words, timestamps and phoneme alignment.
   - *To verify in week 1:* that `en-CA` supports phoneme-level output. If it doesn't, use `en-US` for alignment only and rely on the custom layer for any Canadian-specific judgement.
4. **Canadian feature layer (custom, Python + Parselmouth/Praat):** uses the API's alignments to locate target segments, then:
   - Vowels: F1 and F2 at the 20/50/80% points, normalized with the learner's Lobanov parameters, then the distance to Canadian target distributions for that vowel.
   - Canadian raising: the F1 of the diphthong nucleus before voiceless versus voiced consonants (*write* vs *ride*).
   - Low-back merger: the learner's own LOT/THOUGHT tokens are expected to overlap.
   - Rhoticity: F3 lowering in the r-colouring window.
   - TH: frication energy and duration versus stop burst (a heuristic plus the API's phoneme accuracy).
   - Schwa and stress: vowel duration, intensity and F0 ratios across syllables, compared with the TTS reference's ratios.
   - Flapping: the closure duration of intervocalic /t/.
5. **Fusion:** a rules-based mapping turns the API scores and feature distances into a per-target-word label (match / close / try again) plus a 0–100 pattern score. Thresholds live in versioned config so they can be tuned.
6. **Coaching tip:** an LLM receives structured JSON (L1, pattern, observed vs target, word) and returns a short, constrained tip from a vetted tip template library. The LLM rephrases and personalizes the template; it does not invent phonetics.

### 6.2 Canadian reference distributions
Built from published General Canadian vowel norms in the sociophonetic literature, together with formants measured from the en-CA TTS voices. Both are stored in config as normalized target means and covariances.
*Risk:* TTS vowels may not match natural Canadian speech. Mitigate by preferring the published norms and using the TTS measurements only as a sanity check.

### 6.3 Low confidence: abstain, never punish
Abstain (show no score) when any of these is true:
- The quality gate fails (noise, clipping, too quiet, too short).
- Recognized words differ from the reference (word error rate above 30%). The app says: "It sounded like you said '…'. Try reading the sentence as shown."
- The API's confidence or alignment on a target word is low. That word is shown as "unclear" and left out of mastery updates.
Abstained attempts never lower mastery.

### 6.4 Fairness safeguards
Known risk: commercial scorers under-score African-accented speakers. To counter it:
- Score only the target sounds of the current pattern. Other differences are not flagged.
- Use generous "close" bands at launch.
- Every result has a **"This doesn't seem right"** button, which logs the attempt (with consent) for review.

## 7. Adaptive engine
- **Mastery model:** each of the 8 patterns has a perception score and a production score (an exponentially weighted moving average of non-abstained attempts). Words carry SRS state using SM-2-style intervals.
- **Plan:** focus on the lowest-mastery pattern, weighted by how much it matters for native-likeness. A pattern is "mastered" at ≥80 production over the last 15 attempts, across at least 2 sessions.
- **Re-diagnosis:** every 3 weeks, or on demand. It recomputes priorities and also refreshes Lobanov calibration.
- **Outcome modes (post-MVP):** each mode is a different weight vector over the patterns and thresholds. For example, Intelligibility down-weights low-back merger and raising and up-weights TH, stress and rhoticity. Design the engine so a mode is just config.

## 8. Technical architecture
- **Frontend:** Next.js (App Router, TypeScript) PWA, with installable manifest. Audio uses MediaRecorder (Opus), with an explicit permission flow and Safari fallbacks (`audio/mp4`). Styling is Tailwind, and the UI must be accessible (WCAG AA, captions or text for all audio prompts).
- **Backend API:** Next.js route handlers or a small Node BFF for auth and session data, plus a **Python FastAPI scoring service** (Parselmouth, numpy, the Azure Speech SDK and ffmpeg).
- **Data:** Postgres (users, consents, attempts, scores, mastery, SRS state, content). Recordings and TTS cache live in S3-compatible object storage.
- **Hosting:** Canadian region (ca-central) for data residency.
- **Auth:** Auth.js with Google and email magic link.
- **TTS:** Azure Neural TTS `en-CA` voices, one male and one female. The learner chooses which; responses are cached by text hash.
- **LLM:** Claude (latest Sonnet-class model) for tips, with strict JSON output and a template-constrained prompt.
- **Jobs:** a queue for TTS generation, account deletion and nightly aggregation.

### Key entities
`User` (L1, goal_mode, voice_pref, lobanov_params), `Consent` (type, version, granted_at, revoked_at), `ContentItem` (text, domain, patterns, target_word_spans, tts_audio_key), `Attempt` (item, audio_key, status = scored|abstained, abstain_reason, api_raw, features, labels, scoring_version), `PatternMastery`, `SrsCard`, `FeedbackReport`, `Entitlement`.

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
- **Very high or low voices, or voices that change between sessions:** calibration is refreshed at re-diagnosis, with a manual "recalibrate" option.
- **Learners who already produce Canadian-like features:** the diagnostic marks the pattern as mastered and skips it.
- **Own text with names, numbers or acronyms:** TTS normalization handles them, and target spans are computed only on dictionary words.
- **TTS mispronounces a Canadian place name:** keep an SSML phoneme override list (*Toronto, Saskatchewan, Ontario*).
- **The scoring API is down or rate limited:** the attempt is queued, with "We'll score this in a moment", and listening drills keep working.
- **Duplicate or rapid submissions:** idempotency key per attempt.

## 11. Analytics and success metrics
- **North star:** the change in production mastery on focus patterns after 4 weeks, for active learners.
- **Health metrics:** abstain rate (target under 15%), "this seems wrong" rate per pattern, D7 and D30 retention, and sessions per week.
- **Beta validation:** a closed beta with about 50 Nigerian and Ghanaian learners. Tune thresholds from the "seems wrong" reports and from spot-checks by a Canadian English rater on flagged attempts.

## 12. MVP scope (~8–12 weeks)
- **Weeks 1–2:** Azure en-CA capability spike, recording pipeline, quality gate, auth and consent, data model.
- **Weeks 3–5:** Canadian feature layer (vowels, raising, rhoticity, TH, stress, flap), fusion and abstain logic, and the diagnostic flow with calibration.
- **Weeks 6–8:** 8 modules of content (about 30 minimal pairs and 25 sentences per module across the 3 domains), listening drills, read-aloud UI, feedback panel, static articulation SVGs and LLM tips.
- **Weeks 9–10:** adaptive engine and SRS, progress page with week-1-vs-now, own-text mode, deletion and export.
- **Weeks 11–12:** closed beta, threshold tuning, accessibility pass.

### Post-MVP
- Intelligibility and Confidence modes, animated articulation, shadowing, LLM role-play conversations, more L1 groups (Francophone West African first), regional packs, paywall.

## 13. Open questions and risks
1. Does Azure `en-CA` return phoneme-level data? This must be checked in the week-1 spike.
2. TTS as the only reference model limits prosody authenticity. Consider recording a human for the diagnostic sentences only.
3. The accuracy of formant measurement on phone mics in real rooms needs measuring during the spike.
4. Validation relies only on beta feedback; there is no human-rated benchmark before launch. That increases the risk of unfair scores at launch, which is only partly mitigated by abstaining and generous bands.
5. Content needs review by a Nigerian or Ghanaian English speaker and by a Canadian English phonetics reviewer, for accuracy and tone.

