"""Phase 0 spike: pick the two en-US TTS reference voices (SPEC §8).

Learners imitate these voices, so a good reference voice must:
  1. pronounce our 4 module sounds very clearly: Azure en-US should score its own TH,
     ship/sheep vowels, r-coloured vowels and schwas near 100
  2. speak at a learner-friendly pace (not rushed)

For every candidate it synthesizes the module sentences, scores them with Azure en-US,
and measures speaking pace. It ranks voices per gender, then saves the module sentences
and Canadian place names for the top 2 of each gender, for a human listen test.

Usage (from scoring/):
    .venv/Scripts/python spike/voice_pick_spike.py
Report: spike/results/voice_pick_report.json; audio: spike/results/voices/<voice>/.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from azure_spike import RESULTS_DIR, SPIKE_DIR, TICKS_PER_SECOND, assess, check_credentials
from dotenv import load_dotenv
from tts_spike import synthesize

# Standard neural voices only. HD/Dragon/MAI voices cost more and aren't in every region;
# multilingual voices can drift in accent; child and AI-generated voices are excluded.
CANDIDATES = [
    "en-US-AvaNeural", "en-US-EmmaNeural", "en-US-JennyNeural", "en-US-AriaNeural",
    "en-US-JaneNeural", "en-US-SaraNeural", "en-US-NancyNeural", "en-US-AmberNeural",
    "en-US-AshleyNeural", "en-US-CoraNeural", "en-US-ElizabethNeural", "en-US-MichelleNeural",
    "en-US-MonicaNeural", "en-US-LunaNeural",
    "en-US-AndrewNeural", "en-US-BrianNeural", "en-US-GuyNeural", "en-US-DavisNeural",
    "en-US-JasonNeural", "en-US-TonyNeural", "en-US-BrandonNeural", "en-US-ChristopherNeural",
    "en-US-EricNeural", "en-US-JacobNeural", "en-US-RogerNeural", "en-US-SteffanNeural",
    "en-US-KaiNeural",
]

# One or two sentences per MVP module, workplace/everyday flavoured, no Canada-only words.
SENTENCES = [
    ("rhotic", "I worked as a nurse for the first three years."),
    ("rhotic", "Her early work was perfect for the third term."),
    ("th", "I think this is the third thing they mentioned."),
    ("th", "Thank you for thinking of me for this role."),
    ("ship_sheep", "Please sit in this seat and fill in the sheet."),
    ("schwa", "The police will support the community today."),
]
# Azure SAPI labels scored for each module.
MODULE_PHONEMES = {
    "rhotic": {"er"},
    "th": {"th", "dh"},
    "ship_sheep": {"ih", "iy"},
    "schwa": {"ax"},
}
PLACE_NAMES = [
    "Toronto", "Ottawa", "Montreal", "Saskatchewan", "Etobicoke", "Mississauga",
    "Nova Scotia", "Newfoundland", "Winnipeg", "Regina", "Halifax", "Edmonton",
]

GENDER = {v: ("Male" if i >= 14 else "Female") for i, v in enumerate(CANDIDATES)}
IDEAL_WORDS_PER_SEC = 2.6  # calm, clear read-aloud pace


def with_retry(fn, *args, tries: int = 4):
    for attempt in range(tries):
        try:
            return fn(*args)
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def score_sentence(voice: str, module: str, text: str, out: Path) -> dict:
    with_retry(synthesize, voice, text, out)
    words = with_retry(assess, out, text, "en-US")["NBest"][0]["Words"]
    targets = [
        p["PronunciationAssessment"]["AccuracyScore"]
        for w in words
        for p in w.get("Phonemes", [])
        if p.get("Phoneme") in MODULE_PHONEMES[module]
    ]
    start = words[0]["Offset"] / TICKS_PER_SECOND
    end = (words[-1]["Offset"] + words[-1]["Duration"]) / TICKS_PER_SECOND
    return {"module": module, "targets": targets, "words": len(words), "seconds": end - start}


def evaluate_voice(voice: str) -> dict:
    out_dir = RESULTS_DIR / "voices" / voice
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        rows = [
            score_sentence(voice, module, text, out_dir / f"sentence_{i}.wav")
            for i, (module, text) in enumerate(SENTENCES)
        ]
    except Exception as e:  # noqa: BLE001
        return {"voice": voice, "error": str(e)}

    per_module = {
        m: statistics.mean(s for r in rows if r["module"] == m for s in r["targets"])
        for m in MODULE_PHONEMES
    }
    pace = sum(r["words"] for r in rows) / sum(r["seconds"] for r in rows)
    return {
        "voice": voice,
        "gender": GENDER[voice],
        "clarity": round(statistics.mean(per_module.values()), 1),
        "weakest_module": min(per_module, key=per_module.get),
        "per_module": {m: round(v, 1) for m, v in per_module.items()},
        "words_per_sec": round(pace, 2),
    }


def rank_key(r: dict) -> tuple[float, float]:
    # Clarity first (rounded so tiny differences don't dominate), then closeness to ideal pace.
    return (-round(r["clarity"]), abs(r["words_per_sec"] - IDEAL_WORDS_PER_SEC))


def main() -> int:
    load_dotenv(SPIKE_DIR.parent / ".env")
    if problem := check_credentials():
        print(f"{problem}. Check the key and region in scoring/.env (see spike/README.md).")
        return 1

    print(f"Scoring {len(CANDIDATES)} voices × {len(SENTENCES)} sentences…", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(evaluate_voice, CANDIDATES))
    (RESULTS_DIR / "voice_pick_report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    for r in (r for r in results if "error" in r):
        print(f"  {r['voice']}: ERROR {r['error'][:120]}")
    ok = [r for r in results if "error" not in r]

    shortlist = []
    for gender in ("Female", "Male"):
        ranked = sorted((r for r in ok if r["gender"] == gender), key=rank_key)
        print(f"\n{gender} voices (best first):")
        print(f"  {'voice':26} clarity  pace(w/s)  weakest")
        for r in ranked:
            print(f"  {r['voice']:26} {r['clarity']:6.1f}  {r['words_per_sec']:8.2f}   "
                  f"{r['weakest_module']} ({r['per_module'][r['weakest_module']]:.0f})")
        shortlist += [r["voice"] for r in ranked[:2]]

    print(f"\nSaving place names for the shortlist: {', '.join(shortlist)}")
    for voice in shortlist:
        for place in PLACE_NAMES:
            out = RESULTS_DIR / "voices" / voice / f"place_{place.lower().replace(' ', '_')}.wav"
            with_retry(synthesize, voice, f"I live in {place}.", out)
    print(f"Listen in {RESULTS_DIR / 'voices'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
