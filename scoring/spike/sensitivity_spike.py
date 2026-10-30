"""Phase 0 spike: does Azure en-US actually notice the accent patterns we teach? (SPEC §13.1)

For each module we take two test words and make the SAME TTS voice say each word twice:
  - "target":    the normal North American pronunciation (plain TTS)
  - "different": the typical Nigerian/Ghanaian pronunciation, forced with an SSML IPA override
                 (e.g. "think" said as /tɪŋk/)
Both are scored by Azure en-US against the same reference text ("Say think again.").
If Azure is sensitive to the pattern, the target phoneme's score drops clearly for "different".

Using one voice for both versions means the ONLY change is the sound under test, so a
score drop can only come from that sound.

Usage (from scoring/):
    .venv/Scripts/python spike/sensitivity_spike.py
Results land in spike/results/sensitivity_report.json; audio in spike/results/sensitivity/.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import azure.cognitiveservices.speech as speechsdk
from azure_spike import RESULTS_DIR, SPIKE_DIR, assess, check_credentials
from dotenv import load_dotenv

VOICES = ["en-US-JennyNeural", "en-US-GuyNeural"]
CARRIER = "Say {} again."

# A drop this big (on Azure's 0-100 scale) counts as "Azure noticed the difference".
DETECT_MIN_DROP = 25


@dataclass
class Case:
    module: str
    word: str
    phonemes: tuple[str, ...]  # Azure SAPI labels of the sound under test inside `word`
    different_ipa: str  # how a Nigerian/Ghanaian speaker typically says it


CASES = [
    Case("1 Rhotic R", "car", ("r",), "ka"),
    Case("1 Rhotic R", "worker", ("er",), "wɔka"),
    Case("2 TH sounds", "think", ("th",), "tɪŋk"),
    Case("2 TH sounds", "this", ("dh",), "dɪs"),
    Case("3 ship vs sheep", "ship", ("ih",), "ʃip"),
    Case("3 ship vs sheep", "sit", ("ih",), "sit"),
    Case("4 full vs fool", "full", ("uh",), "ful"),
    Case("4 full vs fool", "look", ("uh",), "luk"),
    Case("5 Schwa", "today", ("ax",), "tudeɪ"),
    Case("5 Schwa", "support", ("ax",), "sɔpɔt"),
    Case("6 cat vs cut", "cat", ("ae",), "kat"),
    Case("6 cat vs cut", "cut", ("ah",), "kɔt"),
    Case("7 Flapped t", "water", ("t",), "wɔtʰa"),
    Case("7 Flapped t", "better", ("t",), "bɛtʰa"),
]


def synthesize_ssml(voice: str, ssml: str, out: Path) -> None:
    cfg = speechsdk.SpeechConfig(
        subscription=os.environ["AZURE_SPEECH_KEY"], region=os.environ["AZURE_SPEECH_REGION"]
    )
    cfg.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )
    synth = speechsdk.SpeechSynthesizer(
        speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=str(out))
    )
    result = synth.speak_ssml_async(ssml).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"synthesis failed: {result.cancellation_details.error_details}")


def ssml(voice: str, case: Case, different: bool) -> str:
    word = escape(case.word)
    if different:
        word = f'<phoneme alphabet="ipa" ph="{escape(case.different_ipa)}">{word}</phoneme>'
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
        f'<voice name="{voice}">{CARRIER.format(word)}</voice></speak>'
    )


def target_score(wav: Path, case: Case) -> float | None:
    """Azure's accuracy for the sound under test, found by label inside the test word."""
    words = assess(wav, CARRIER.format(case.word), "en-US")["NBest"][0]["Words"]
    word = next((w for w in words if w["Word"].lower() == case.word), None)
    if word is None:
        return None
    scores = [
        p["PronunciationAssessment"]["AccuracyScore"]
        for p in word.get("Phonemes", [])
        if p.get("Phoneme") in case.phonemes
    ]
    return min(scores) if scores else None


@dataclass
class Result:
    module: str
    word: str
    voice: str
    target_score: float | None
    different_score: float | None

    @property
    def drop(self) -> float | None:
        if self.target_score is None or self.different_score is None:
            return None
        return self.target_score - self.different_score


def main() -> int:
    load_dotenv(SPIKE_DIR.parent / ".env")
    if problem := check_credentials():
        print(f"{problem}. Check the key and region in scoring/.env (see spike/README.md).")
        return 1

    out_dir = RESULTS_DIR / "sensitivity"
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[Result] = []
    for voice in VOICES:
        print(f"Testing with {voice}…", flush=True)
        for case in CASES:
            scores = []
            for different in (False, True):
                wav = out_dir / f"{voice}_{case.word}_{'different' if different else 'target'}.wav"
                synthesize_ssml(voice, ssml(voice, case, different), wav)
                scores.append(target_score(wav, case))
            results.append(Result(case.module, case.word, voice, *scores))

    (RESULTS_DIR / "sensitivity_report.json").write_text(
        json.dumps([asdict(r) | {"drop": r.drop} for r in results], indent=2), encoding="utf-8"
    )

    print(f"\n{'word':8} {'voice':18} target  different  drop")
    for r in results:
        fmt = lambda x: " n/a" if x is None else f"{x:4.0f}"
        print(f"{r.word:8} {r.voice:18}  {fmt(r.target_score)}     {fmt(r.different_score)}   {fmt(r.drop)}")

    print("\nPer module (median drop across words and voices):")
    for module in dict.fromkeys(c.module for c in CASES):
        drops = [r.drop for r in results if r.module == module and r.drop is not None]
        if not drops:
            print(f"  {module:18} NO DATA")
            continue
        median = statistics.median(drops)
        verdict = "DETECTS" if median >= DETECT_MIN_DROP else "MISSES"
        print(f"  {module:18} {verdict:8} median drop {median:4.0f}  (range {min(drops):.0f} to {max(drops):.0f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
