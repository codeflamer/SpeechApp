"""Phase 0 spike: can the server convert every browser's recording format? (SPEC §6.1, §10)

Browsers' MediaRecorder output differs, and some files are unusual:
  - Chrome / Edge / Android: WebM + Opus, written as a live stream with NO duration in the header
  - Firefox:                 Ogg + Opus
  - Safari / iOS:            MP4 + AAC, written as a FRAGMENTED MP4 (moov box up front, no index)
This script builds a file that mimics each one from a real clip, converts it to 16 kHz mono WAV
the same way the scoring service will, and checks the result (rate, channels, duration).

Usage (from scoring/):
    .venv/Scripts/python spike/format_spike.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from azure_spike import CLIPS_DIR, to_wav16k

SOURCE = CLIPS_DIR / "tolu_clear_1.mp4"

# name -> ffmpeg output args that mimic what that browser's MediaRecorder writes
FORMATS = {
    "chrome.webm": ["-c:a", "libopus", "-b:a", "32k", "-f", "webm", "-live", "1",
                    "-cluster_time_limit", "1000"],
    "firefox.ogg": ["-c:a", "libopus", "-b:a", "32k", "-f", "ogg"],
    "safari.mp4": ["-c:a", "aac", "-b:a", "64k", "-f", "mp4",
                   "-movflags", "frag_keyframe+empty_moov+default_base_moof"],
}
DURATION_TOLERANCE_S = 0.1


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    duration = data["format"].get("duration") or stream.get("duration")
    return {
        "codec": stream.get("codec_name"),
        "rate": int(stream.get("sample_rate", 0)),
        "channels": stream.get("channels"),
        "duration": float(duration) if duration not in (None, "N/A") else None,
    }


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing {SOURCE}; any short speech clip works.")
        return 1
    src = probe(SOURCE)
    print(f"source: {SOURCE.name} {src}\n")
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, args in FORMATS.items():
            browser_file = Path(tmp) / name
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(SOURCE), "-ac", "1", *args,
                            str(browser_file)], check=True)
            before = probe(browser_file)
            wav = Path(tmp) / (name + ".wav")
            try:
                to_wav16k(browser_file, wav)
                after = probe(wav)
            except subprocess.CalledProcessError as e:
                print(f"{name:12} FAIL conversion: {e}")
                failures += 1
                continue
            ok = (
                after["rate"] == 16000 and after["channels"] == 1
                and after["duration"] is not None
                and abs(after["duration"] - src["duration"]) <= DURATION_TOLERANCE_S
            )
            failures += not ok
            header_len = "MISSING" if before["duration"] is None else f"{before['duration']:.2f}s"
            print(f"{name:12} {'OK  ' if ok else 'FAIL'} in: {before['codec']}, header duration {header_len}"
                  f"  ->  out: {after['rate']} Hz, {after['channels']} ch, {after['duration']:.2f}s")
    print("\nAll formats convert cleanly." if not failures else f"\n{failures} format(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
