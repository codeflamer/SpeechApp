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

## Troubleshooting: "Azure rejected the key (HTTP 401)"
- In the Azure portal, open the resource and go to **Keys and Endpoint**. Copy **KEY 1** and the **Location/Region** shown there, written lowercase with no spaces, e.g. `canadacentral`.
- The resource must be **Speech** or **Azure AI services (multi-service)**. Keys from Azure OpenAI, a Foundry *project*, or a different service won't work.
- If **local authentication is disabled** on the resource, keys are refused. Turn key access on, or use a new Speech resource.
- A newly created or regenerated key can take a few minutes to start working.

## Run
```bash
.venv/Scripts/python spike/azure_spike.py
```
The output is a verdict per locale, plus `spike/results/report.json` with per-clip detail.

## Sensitivity spike: does Azure en-US notice the patterns we teach?
```bash
.venv/Scripts/python spike/sensitivity_spike.py
```
Two en-US TTS voices say each test word normally and then with a typical Nigerian/Ghanaian sound forced through SSML (e.g. *think* as /tɪŋk/). The script reports how much Azure's score for that sound drops. Before trusting a "miss", check that the TTS actually changed the sound: it sometimes ignores the override. Results are in SPEC §13.1.

## Voice-pick spike: which en-US voices should learners copy?
```bash
.venv/Scripts/python spike/voice_pick_spike.py
```
The script scores standard en-US neural voices on our 4 module sounds and measures their speaking pace. It then saves the module sentences and Canadian place names for the top voices to `spike/results/voices/`. Compare them side by side in `spike/results/listen.html`.

## Browser recording formats
```bash
.venv/Scripts/python spike/format_spike.py
```
This imitates each browser's MediaRecorder file (Chrome WebM with no duration, Firefox Ogg, Safari fragmented MP4) and checks the conversion to 16 kHz mono.

To test a real browser, start the `recorder-spike` and `web` servers from `.claude/launch.json`, then open http://localhost:3000/spike/recorder. **Record** uses the mic; **Record 3 s test tone** works without one.

## TTS spike: are the en-CA voices Canadian?
```bash
.venv/Scripts/python spike/tts_spike.py
```
For every en-CA voice it measures Canadian raising (*ice/eyes*, *write/ride*…) and the low-back merger (*cot/caught*…). It also saves place-name clips to `spike/results/tts/<voice>/` so a human can listen to them.
