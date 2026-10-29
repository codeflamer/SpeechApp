# Phase 0 spike: Azure en-CA + formant stability

This spike answers SPEC §13.1 (does `en-CA` return phoneme-level data?) and §13.3 (are phone-mic formants measurable?).

## Setup
1. Create an Azure Speech resource in **Canada Central**.
2. Copy `scoring/.env.example` to `scoring/.env` and fill in the key.
3. Put 5–10 recordings in `spike/clips/`. They should be Nigerian or Ghanaian speakers on phone mics, with some recorded in a quiet room and some in a noisy one. Any format ffmpeg can read works.
4. Create `spike/clips/manifest.csv`:
   ```csv
   file,reference_text
   ada_quiet.m4a,I think the water bottle is about thirty dollars.
   kwame_noisy.m4a,Can I get a coffee and a bagel please?
   ```
   Use sentences that cover the 8 patterns (TH, r, raising, flaps, ship/sheep…).

`clips/` and `results/` are git-ignored because they contain real voices. Get each speaker's consent before recording.

## Run
```bash
.venv/Scripts/python spike/azure_spike.py
```
The output is a verdict per locale, plus `spike/results/report.json` with per-clip detail.
