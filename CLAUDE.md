# CLAUDE.md

Maple (working name): a free PWA that helps Nigerian and Ghanaian English speakers who are moving to Canada add a **North American English** accent. The MVP has 4 modules scored with Azure `en-US`. Anything needing custom acoustic measurement, including Canada-only features, comes later in Phase 6 (SPEC §14). [SPEC.md](SPEC.md) is the source of truth for behaviour. **[KANBAN.md](KANBAN.md) tracks all work from Phase 1 onward**, and [CHECKLIST.md](CHECKLIST.md) records Phase 0.

## Working on this repo: vertical slices on the kanban board
- **Always use the `kanban` skill** (`.claude/skills/kanban/SKILL.md`) when starting, continuing or finishing a feature, picking the "next item", or adding a request to the board.
- Build **one vertical slice at a time**: a card cuts through DB → scoring → server → UI → tests and ends in a demo a learner could do. **Never build a whole layer ahead of the features that use it** (no "all tables first", no "finish scoring, then UI").
- **WIP limit 1:** finish the card in progress (its Definition of Done in KANBAN.md) before pulling the next card from the top of Ready. Split oversized cards vertically, never by layer.
- New features and bugs become cards on the board (the template is in the skill) before they're built.
- Read the SPEC.md sections a card cites before implementing it. If the code must deviate from SPEC, update SPEC.md in the same change.
- Don't build Phase 6 work early: custom vowel or timing measurement, Lobanov calibration, and the *full/fool*, *cat/cut*, flapped t, low-back merger and Canadian raising modules. Content must never target Canada-only words such as *about* or *caught*.
- Rhotic R scores only r-coloured vowels (*bird, worker*). Never score a syllable-final r (*car*): Azure misses it (SPEC §4, §13.1).

## Planned layout
- `web/`: Next.js (App Router, TypeScript, Tailwind) PWA, Supabase Auth, and the recording UI. Deployed on Vercel, with functions pinned to `yul1` (Montréal) in `web/vercel.json`
- `scoring/`: Python FastAPI service (Azure Speech SDK `en-US`, numpy, ffmpeg; Parselmouth only in Phase 6)
- `scoring/spike/`: Phase 0 experiments. Their Canadian findings are recorded in SPEC §14.
- `supabase/`: Supabase config and (from Phase 1) SQL migrations. Hosted in `ca-central-1` only. Every user table has row-level security
- Recordings upload from the browser straight to Supabase Storage through signed URLs. Never route audio through Vercel functions
- The scoring service runs on Azure Container Apps in Canada Central

## Commands
- Local Supabase (repo root, needs Docker Desktop running): `npm run db:start`, `db:status` (prints local keys), `db:stop`, `db:reset`. Studio (database UI): http://127.0.0.1:54323
- Copy `web/.env.example` → `web/.env.local` and `scoring/.env.example` → `scoring/.env`
- Web (`web/`): `npm run dev`, `npm run build`, `npm run lint`, `npm test` (Vitest), `npm run test:e2e` (Playwright; needs the local Supabase stack)
- Database tests (repo root): `npx supabase test db` (pgTAP files in `supabase/tests/`). Every RLS policy gets one
- Scoring (`scoring/`), using the venv at `scoring/.venv`:
  - Install: `.venv/Scripts/python -m pip install -e ".[dev]"`
  - Test: `.venv/Scripts/python -m pytest`
  - Lint: `.venv/Scripts/python -m ruff check .`
  - Dev server: `.venv/Scripts/python -m uvicorn app.main:app --reload`
- Phase 0 spikes: `scoring/spike/azure_spike.py`, `tts_spike.py` and `sensitivity_spike.py` (see `scoring/spike/README.md`)

## Git
- Never add Claude co-author or attribution trailers to commits or PRs.
- **Every commit subject starts with the next book of the Bible, in order, then the change summary:**
  ```
  EXODUS - Add recording pipeline and quality gate
  ```
  - The book is set by the commit's position in history. Commit *n* uses book *n* from the list below, where *n* = `git rev-list --count HEAD` + 1 at commit time.
  - Commit 1 (`20eafd2`, the Phase 0 scaffold) counts as GENESIS even though its subject has no prefix, so the next commit is EXODUS.
  - Write the book name in uppercase, followed by ` - ` and a short summary. The commit body can list details as usual.
  - After REVELATION (commit 66), ask the user how to continue before committing.
  - Books, in order: GENESIS, EXODUS, LEVITICUS, NUMBERS, DEUTERONOMY, JOSHUA, JUDGES, RUTH, 1 SAMUEL, 2 SAMUEL, 1 KINGS, 2 KINGS, 1 CHRONICLES, 2 CHRONICLES, EZRA, NEHEMIAH, ESTHER, JOB, PSALMS, PROVERBS, ECCLESIASTES, SONG OF SOLOMON, ISAIAH, JEREMIAH, LAMENTATIONS, EZEKIEL, DANIEL, HOSEA, JOEL, AMOS, OBADIAH, JONAH, MICAH, NAHUM, HABAKKUK, ZEPHANIAH, HAGGAI, ZECHARIAH, MALACHI, MATTHEW, MARK, LUKE, JOHN, ACTS, ROMANS, 1 CORINTHIANS, 2 CORINTHIANS, GALATIANS, EPHESIANS, PHILIPPIANS, COLOSSIANS, 1 THESSALONIANS, 2 THESSALONIANS, 1 TIMOTHY, 2 TIMOTHY, TITUS, PHILEMON, HEBREWS, JAMES, 1 PETER, 2 PETER, 1 JOHN, 2 JOHN, 3 JOHN, JUDE, REVELATION

## Non-negotiable rules

### Copy and tone ("accent expansion", SPEC §3)
- Never use "reduce", "fix", "correct", "error", "mistake" or "bad accent" in user-facing text. Use "North American target", "match", "close" and "try the North American way".
- Always call the accent **"North American English"**. Never call it "American" or "Canadian" in the MVP.
- Describe L1 features as *different*, not wrong.
- Minimal gamification: no streaks or badges.

### Scoring (SPEC §6)
- **Abstain, never punish.** Show no score when the quality gate fails, word error rate is above 30%, or confidence is low. Abstained attempts must never lower mastery.
- Score only the target sounds of the current pattern. Don't flag other differences.
- Pick target phonemes by their Azure label inside the target word, never by position (the first vowel of *about* is a schwa).
- All thresholds live in versioned config. Bump `scoring_version` whenever scoring logic or thresholds change, and store it on every `Attempt`.
- (Phase 6) Vowel measurements must use the learner's Lobanov calibration or same-speaker comparisons. Never compare raw formants across speakers.
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
- **North American English**: the MVP target accent; sounds shared by US and Canadian English
- **Pattern / module**: one of the 4 MVP target sound patterns (SPEC §4); each has an `accent_tag` (`shared` now, `canadian` in Phase 6)
- **Perception / production**: hearing a contrast (listening drills) vs saying it (read-aloud)
- **Abstain**: the attempt is not scored, and the learner is shown a specific reason
- **Lobanov normalization** (Phase 6): per-speaker z-scoring of formants, using the calibration words from the diagnostic
- **Canadian raising** (Phase 6): the diphthongs in *ice* and *about* start higher before voiceless consonants
- **Low-back merger** (Phase 6): *cot* and *caught* sound the same in Canadian English
