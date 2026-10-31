# Maple: Phase 0 Checklist

Derived from [SPEC.md](SPEC.md). Section references (§) point back to the spec.

> **From Phase 1 onward, work is tracked as vertical slices on [KANBAN.md](KANBAN.md).** Every former Phase 1–6 item now lives on a card there. Phase 0's remaining account steps are cards B1–B4 under Blocked.

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

## Phase 1 onward
See **[KANBAN.md](KANBAN.md)**.
