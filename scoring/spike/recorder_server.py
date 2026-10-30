"""Phase 0 spike: tiny upload endpoint for the browser recorder test page (web/src/app/spike/recorder).

Receives the raw MediaRecorder blob, converts it with the same ffmpeg step the scoring service
will use, and reports what came in and what came out. Not production code.

Usage (from scoring/):
    .venv/Scripts/python -m uvicorn --app-dir spike recorder_server:app --port 8001
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from azure_spike import to_wav16k
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from format_spike import probe

app = FastAPI(title="Recorder spike")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["POST"],
                   allow_headers=["*"])

EXTENSIONS = {"webm": ".webm", "ogg": ".ogg", "mp4": ".mp4", "mpeg": ".mp3", "wav": ".wav"}


@app.post("/convert")
async def convert(request: Request) -> dict:
    body = await request.body()
    mime = request.headers.get("content-type", "")
    ext = next((e for key, e in EXTENSIONS.items() if key in mime), ".bin")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"upload{ext}"
        src.write_bytes(body)
        try:
            before = probe(src)
            wav = Path(tmp) / "out.wav"
            to_wav16k(src, wav)
            after = probe(wav)
        except Exception as e:  # noqa: BLE001 - spike: report any failure to the page
            return {"ok": False, "mime": mime, "bytes": len(body), "error": str(e)}
    return {"ok": True, "mime": mime, "bytes": len(body), "input": before, "output": after}
