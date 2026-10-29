# CLAUDE.md

Maple (working name): a free PWA that helps Nigerian and Ghanaian English speakers add a General Canadian English accent. The project is pre-code. [SPEC.md](SPEC.md) is the source of truth for behaviour, and [CHECKLIST.md](CHECKLIST.md) tracks build progress.

## Working on this repo
- Read the relevant SPEC.md section before implementing a feature. If the code must deviate from it, update SPEC.md in the same change.
- When a checklist item is done, tick it in CHECKLIST.md. Respect each phase's exit gate and don't skip ahead.
- Phase 0 (the Azure `en-CA` spike) may change the scoring design. Don't build on scoring assumptions until it's resolved.

## Planned layout
- `web/`: Next.js (App Router, TypeScript, Tailwind) PWA, Auth.js, and the recording UI
- `scoring/`: Python FastAPI service (Parselmouth/Praat, numpy, Azure Speech SDK, ffmpeg)
- Postgres, plus S3-compatible storage for recordings and the TTS cache, hosted in ca-central only

## Commands
- Web (`web/`): `npm run dev`, `npm run build`, `npm run lint`
- Scoring (`scoring/`), using the venv at `scoring/.venv`:
  - Install: `.venv/Scripts/python -m pip install -e ".[dev]"`
  - Test: `.venv/Scripts/python -m pytest`
  - Lint: `.venv/Scripts/python -m ruff check .`
  - Dev server: `.venv/Scripts/python -m uvicorn app.main:app --reload`
- Phase 0 spike: `scoring/spike/azure_spike.py` (see `scoring/spike/README.md`)

## Git
- Never add Claude co-author or attribution trailers to commits or PRs.

## Non-negotiable rules

### Copy and tone ("accent expansion", SPEC §3)
- Never use "reduce", "fix", "correct", "error", "mistake" or "bad accent" in user-facing text. Use "Canadian target", "match", "close" and "try the Canadian way".
- Describe L1 features as *different*, not wrong.
- Minimal gamification: no streaks or badges.

### Scoring (SPEC §6)
- **Abstain, never punish.** Show no score when the quality gate fails, word error rate is above 30%, or confidence is low. Abstained attempts must never lower mastery.
- Score only the target sounds of the current pattern. Don't flag other differences.
- All thresholds and Canadian reference distributions live in versioned config. Bump `scoring_version` whenever scoring logic or thresholds change, and store it on every `Attempt`.
- Vowel measurements must use the learner's Lobanov calibration. Never compare raw formants.
- All scoring runs server-side. The client only records and uploads.

### LLM coaching tips
- The LLM rephrases vetted tip templates from structured JSON. It must not invent phonetic advice.
- Never send audio to the LLM: text and structured data only.
- Always fall back to the raw template if the LLM call fails.

### Privacy (SPEC §9)
- Recording-storage consent is required. Training-use consent is a separate opt-in, off by default. Check consent before any use of recordings beyond scoring and progress playback.
- User deletion must reach object storage, not just the database.
- Never log raw audio or transcripts with user identifiers outside the attempt record.

### Paywall readiness
- Gate features through `entitlements(user)`. Never hard-code "everything is free" checks.
- Meter usage per user: attempts, TTS characters and API seconds.

## Domain glossary
- **Pattern / module**: one of the 8 target sound patterns (SPEC §4)
- **Perception / production**: hearing a contrast (listening drills) vs saying it (read-aloud)
- **Abstain**: the attempt is not scored, and the learner is shown a specific reason
- **Lobanov normalization**: per-speaker z-scoring of formants, using the calibration words from the diagnostic
- **Canadian raising**: the diphthongs in *ice* and *about* start higher before voiceless consonants
- **Low-back merger**: *cot* and *caught* sound the same in Canadian English
