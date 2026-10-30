"""Phase 0 spike: do Azure's en-CA TTS voices actually sound Canadian? (SPEC §6.2, §13.2)

For every en-CA neural voice, synthesizes word pairs in a carrier phrase ("Say ___ again.")
and measures the two Canadian-only patterns:
  - Canadian raising: diphthong onset F1 should be LOWER before voiceless consonants
    (ice vs eyes). We report the drop in Hz; a clear positive drop means the voice raises.
  - Low-back merger: cot and caught should land on the same vowel. We report how far apart
    they are; small distances mean the voice merges them.
It also saves place-name recordings (Toronto, Saskatchewan…) for a human listen test.

Comparing each voice with itself (ice vs eyes from the same voice) cancels out voice
differences, so raw Hz are fine here and no Lobanov normalization is needed.

Usage (from scoring/):
    .venv/Scripts/python spike/tts_spike.py
Audio lands in spike/results/tts/<voice>/ and the summary in spike/results/tts_report.json.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
import parselmouth
from azure_spike import RESULTS_DIR, SPIKE_DIR, TICKS_PER_SECOND, VOWELS, assess, check_credentials
from dotenv import load_dotenv

CARRIER = "Say {} again."

# (voiceless-context word, voiced-context word): same diphthong, different following consonant.
RAISING_PAIRS = [("ice", "eyes"), ("price", "prize"), ("write", "ride"), ("lout", "loud")]
# (LOT word, THOUGHT word): Canadians pronounce each pair the same.
MERGER_PAIRS = [("cot", "caught"), ("Don", "dawn"), ("stock", "stalk")]
PLACE_NAMES = ["Toronto", "Saskatchewan", "Ontario", "Ottawa", "Etobicoke", "Nova Scotia"]

# Rough first-pass thresholds; tune once we hear the voices (SPEC §6.2).
RAISING_MIN_DROP_HZ = 60  # onset F1 must fall at least this much before voiceless consonants
MERGER_MAX_F1_HZ = 75  # cot/caught counted as merged if both gaps are within these limits
MERGER_MAX_F2_HZ = 150


def speech_config() -> speechsdk.SpeechConfig:
    return speechsdk.SpeechConfig(
        subscription=os.environ["AZURE_SPEECH_KEY"], region=os.environ["AZURE_SPEECH_REGION"]
    )


def list_voices() -> list[speechsdk.VoiceInfo]:
    synth = speechsdk.SpeechSynthesizer(speech_config=speech_config(), audio_config=None)
    result = synth.get_voices_async("en-CA").get()
    return [v for v in result.voices if v.locale == "en-CA"]


def synthesize(voice: str, text: str, out: Path) -> None:
    cfg = speech_config()
    cfg.speech_synthesis_voice_name = voice
    cfg.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )
    synth = speechsdk.SpeechSynthesizer(
        speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=str(out))
    )
    result = synth.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"synthesis failed for {voice!r}: {result.cancellation_details.error_details}")


def vowel_formants(wav: Path, word: str, max_formant: int) -> tuple[float, float] | None:
    """F1/F2 of the target vowel in `word` inside the carrier phrase, or None if not found.

    The target is the /ay/ or /aw/ diphthong when the word has one, else its first vowel.
    Picking by position alone would measure the schwa in "about" instead of its /aw/.
    """
    words = assess(wav, CARRIER.format(word), "en-US")["NBest"][0]["Words"]
    target = next((w for w in words if w["Word"].lower() == word.lower()), None)
    if target is None:
        return None
    vowels = [p for p in target.get("Phonemes", []) if p.get("Phoneme") in VOWELS]
    vowel = next((p for p in vowels if p["Phoneme"] in ("ay", "aw")), vowels[0] if vowels else None)
    if vowel is None:
        return None
    start = vowel["Offset"] / TICKS_PER_SECOND
    dur = vowel["Duration"] / TICKS_PER_SECOND
    # Diphthongs: raising lives in the onset, so measure early. Monophthongs: the middle.
    t = start + dur * (0.2 if vowel["Phoneme"] in ("ay", "aw") else 0.5)
    formant = parselmouth.Sound(str(wav)).to_formant_burg(
        max_number_of_formants=5, maximum_formant=max_formant
    )
    return formant.get_value_at_time(1, t), formant.get_value_at_time(2, t)


def measure(voice: speechsdk.VoiceInfo, out_dir: Path) -> dict:
    # Praat's standard ceilings: ~5000 Hz for male voices, ~5500 Hz for female voices.
    max_formant = 5000 if voice.gender == speechsdk.SynthesisVoiceGender.Male else 5500

    def formants(word: str) -> tuple[float, float] | None:
        wav = out_dir / f"{word.lower()}.wav"
        synthesize(voice.short_name, CARRIER.format(word), wav)
        return vowel_formants(wav, word, max_formant)

    raising = []
    for voiceless, voiced in RAISING_PAIRS:
        a, b = formants(voiceless), formants(voiced)
        if a and b:
            raising.append({"pair": f"{voiceless}/{voiced}", "f1_drop_hz": round(b[0] - a[0])})

    merger = []
    for lot, thought in MERGER_PAIRS:
        a, b = formants(lot), formants(thought)
        if a and b:
            merger.append(
                {"pair": f"{lot}/{thought}", "f1_gap_hz": round(abs(a[0] - b[0])),
                 "f2_gap_hz": round(abs(a[1] - b[1]))}
            )

    for place in PLACE_NAMES:
        synthesize(voice.short_name, place, out_dir / f"place_{place.lower().replace(' ', '_')}.wav")

    drops = [r["f1_drop_hz"] for r in raising]
    merged = [
        m["f1_gap_hz"] <= MERGER_MAX_F1_HZ and m["f2_gap_hz"] <= MERGER_MAX_F2_HZ for m in merger
    ]
    return {
        "voice": voice.short_name,
        "gender": voice.gender.name,
        "raising": raising,
        "merger": merger,
        "median_raising_drop_hz": statistics.median(drops) if drops else None,
        "raises": bool(drops) and statistics.median(drops) >= RAISING_MIN_DROP_HZ,
        "merges": bool(merged) and sum(merged) > len(merged) / 2,
    }


def main() -> int:
    load_dotenv(SPIKE_DIR.parent / ".env")
    if problem := check_credentials():
        print(f"{problem}. Check the key and region in scoring/.env (see spike/README.md).")
        return 1

    voices = list_voices()
    if not voices:
        print("No en-CA voices returned for this region.")
        return 1

    reports = []
    for voice in voices:
        out_dir = RESULTS_DIR / "tts" / voice.short_name
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Measuring {voice.short_name}…", flush=True)
        try:
            reports.append(measure(voice, out_dir))
        except Exception as e:  # noqa: BLE001 - spike: report and keep going
            reports.append({"voice": voice.short_name, "error": str(e)})

    (RESULTS_DIR / "tts_report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print()
    for r in reports:
        if "error" in r:
            print(f"{r['voice']}: ERROR {r['error']}")
            continue
        print(
            f"{r['voice']} ({r['gender']}): raising={'YES' if r['raises'] else 'no'} "
            f"(median drop {r['median_raising_drop_hz']} Hz)  merger={'YES' if r['merges'] else 'no'}"
        )
        for x in r["raising"]:
            print(f"    raising {x['pair']:12} onset F1 drop {x['f1_drop_hz']:>4} Hz")
        for x in r["merger"]:
            print(f"    merger  {x['pair']:12} gap F1 {x['f1_gap_hz']:>4} Hz, F2 {x['f2_gap_hz']:>4} Hz")
    print(f"\nListen to the place names in {RESULTS_DIR / 'tts'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
