"""Phase 0 spike: is Azure Pronunciation Assessment usable for Canadian scoring? (SPEC §13.1, §13.3)

For each clip in clips/manifest.csv, runs Azure Pronunciation Assessment in en-CA and en-US
and records whether phoneme-level scores, names and timestamps come back. It also measures
F1/F2 with Parselmouth on every aligned vowel, to see whether phone-mic formants are stable
enough to use. Writes results/report.json and prints a verdict per locale.

Usage (from scoring/):
    .venv/Scripts/python spike/azure_spike.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
import parselmouth
from dotenv import load_dotenv

SPIKE_DIR = Path(__file__).parent
CLIPS_DIR = SPIKE_DIR / "clips"
RESULTS_DIR = SPIKE_DIR / "results"
LOCALES = ["en-CA", "en-US"]
TICKS_PER_SECOND = 10_000_000  # Azure offsets and durations are in 100 ns ticks

# Azure's phoneme alphabet (SAPI-style) vowel labels, used to pick segments for formant checks.
VOWELS = {"iy", "ih", "eh", "ae", "aa", "ao", "ah", "uw", "uh", "er", "ax", "ay", "aw", "ey", "ow", "oy"}


@dataclass
class ClipResult:
    file: str
    locale: str
    recognized_text: str = ""
    word_count: int = 0
    words_with_phonemes: int = 0
    phonemes_named: int = 0
    phonemes_total: int = 0
    phonemes_timed: int = 0
    vowels_measured: int = 0
    vowels_with_formants: int = 0
    mean_accuracy: float | None = None
    error: str | None = None


@dataclass
class LocaleSummary:
    locale: str
    clips: int = 0
    clips_failed: int = 0
    phoneme_coverage: float = 0.0  # share of words that came back with phoneme detail
    phoneme_name_rate: float = 0.0  # share of phonemes with a label (not just a score)
    phoneme_timing_rate: float = 0.0  # share of phonemes with offset + duration
    formant_success_rate: float = 0.0  # share of vowels where F1 and F2 were measurable
    results: list[ClipResult] = field(default_factory=list)


def to_wav16k(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "16000", str(dst)],
        check=True,
    )


def assess(wav: Path, reference_text: str, locale: str) -> dict:
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ["AZURE_SPEECH_KEY"], region=os.environ["AZURE_SPEECH_REGION"]
    )
    speech_config.speech_recognition_language = locale
    pa_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True,
    )
    pa_config.phoneme_alphabet = "SAPI"
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=speechsdk.audio.AudioConfig(filename=str(wav))
    )
    pa_config.apply_to(recognizer)
    result = recognizer.recognize_once()
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        raise RuntimeError(f"recognition failed: {result.reason}")
    return json.loads(result.properties[speechsdk.PropertyId.SpeechServiceResponse_JsonResult])


def formants_ok(formant: parselmouth.Formant, start_s: float, dur_s: float) -> bool:
    t = start_s + dur_s / 2
    f1, f2 = formant.get_value_at_time(1, t), formant.get_value_at_time(2, t)
    return not (math.isnan(f1) or math.isnan(f2))


def run_clip(file: str, reference_text: str, locale: str, wav: Path) -> ClipResult:
    r = ClipResult(file=file, locale=locale)
    try:
        data = assess(wav, reference_text, locale)
    except Exception as e:  # noqa: BLE001 - spike: record and keep going
        r.error = str(e)
        return r

    best = data["NBest"][0]
    r.recognized_text = best.get("Display", "")
    formant = parselmouth.Sound(str(wav)).to_formant_burg(max_number_of_formants=5)
    scores = []
    for word in best.get("Words", []):
        r.word_count += 1
        phonemes = word.get("Phonemes") or []
        if phonemes:
            r.words_with_phonemes += 1
        for ph in phonemes:
            r.phonemes_total += 1
            acc = ph.get("PronunciationAssessment", {}).get("AccuracyScore")
            if acc is not None:
                scores.append(acc)
            name = ph.get("Phoneme")
            if name:
                r.phonemes_named += 1
            if "Offset" in ph and "Duration" in ph:
                r.phonemes_timed += 1
                if name in VOWELS:
                    r.vowels_measured += 1
                    start = ph["Offset"] / TICKS_PER_SECOND
                    dur = ph["Duration"] / TICKS_PER_SECOND
                    r.vowels_with_formants += formants_ok(formant, start, dur)
    r.mean_accuracy = sum(scores) / len(scores) if scores else None
    return r


def summarize(locale: str, results: list[ClipResult]) -> LocaleSummary:
    def rate(num: int, den: int) -> float:
        return num / den if den else 0.0

    ok = [r for r in results if r.error is None]
    return LocaleSummary(
        locale=locale,
        clips=len(results),
        clips_failed=len(results) - len(ok),
        phoneme_coverage=rate(sum(r.words_with_phonemes for r in ok), sum(r.word_count for r in ok)),
        phoneme_name_rate=rate(sum(r.phonemes_named for r in ok), sum(r.phonemes_total for r in ok)),
        phoneme_timing_rate=rate(sum(r.phonemes_timed for r in ok), sum(r.phonemes_total for r in ok)),
        formant_success_rate=rate(
            sum(r.vowels_with_formants for r in ok), sum(r.vowels_measured for r in ok)
        ),
        results=results,
    )


def evaluate_locale(s: LocaleSummary) -> tuple[str, str]:
    """Decide whether a locale is usable for scoring. Returns (verdict, reason).

    verdict is one of:
      "use"        - good enough to score Canadian patterns directly
      "align-only" - timings usable for our feature layer, but don't trust its labels/scores
      "reject"     - not usable
    """
    if s.clips == 0:
        return "reject", "no clips were run"

    fail_rate = s.clips_failed / s.clips
    if fail_rate > 0.2:
        return "reject", f"{fail_rate:.0%} of clips failed recognition"

    if s.phoneme_timing_rate < 0.9:
        return "reject", f"only {s.phoneme_timing_rate:.0%} of phonemes have timings"

    mic_note = ""
    if s.formant_success_rate < 0.8:
        mic_note = f"; mic warning: formants measurable on only {s.formant_success_rate:.0%} of vowels"

    if s.phoneme_coverage >= 0.9 and s.phoneme_name_rate >= 0.9:
        return "use", "phoneme scores, names and timings all present" + mic_note
    return "align-only", "timings usable, but phoneme detail is incomplete" + mic_note


def main() -> int:
    load_dotenv(SPIKE_DIR.parent / ".env")
    manifest = CLIPS_DIR / "manifest.csv"
    if not manifest.exists():
        print(f"Missing {manifest}. See spike/README.md.")
        return 1
    with manifest.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    RESULTS_DIR.mkdir(exist_ok=True)
    summaries = []
    with tempfile.TemporaryDirectory() as tmp:
        wavs = {}
        for row in rows:
            wav = Path(tmp) / (Path(row["file"]).stem + ".wav")
            to_wav16k(CLIPS_DIR / row["file"], wav)
            wavs[row["file"]] = wav
        for locale in LOCALES:
            results = [run_clip(r["file"], r["reference_text"], locale, wavs[r["file"]]) for r in rows]
            summaries.append(summarize(locale, results))

    (RESULTS_DIR / "report.json").write_text(
        json.dumps([asdict(s) for s in summaries], indent=2), encoding="utf-8"
    )
    for s in summaries:
        verdict, reason = evaluate_locale(s)
        print(
            f"{s.locale}: {verdict.upper()} ({reason})\n"
            f"  clips={s.clips} failed={s.clips_failed} phoneme_coverage={s.phoneme_coverage:.0%} "
            f"named={s.phoneme_name_rate:.0%} timed={s.phoneme_timing_rate:.0%} "
            f"formants={s.formant_success_rate:.0%}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
