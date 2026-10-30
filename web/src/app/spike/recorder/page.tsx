"use client";

// Phase 0 spike (SPEC §10): which audio format does this browser's MediaRecorder produce,
// and can the server convert it? Not production UI. Needs scoring/spike/recorder_server.py on :8001.

import { useEffect, useRef, useState } from "react";

const CANDIDATE_TYPES = [
  "audio/webm;codecs=opus",
  "audio/ogg;codecs=opus",
  "audio/mp4",
  "audio/mp4;codecs=mp4a.40.2",
  "audio/webm",
];
const CONVERT_URL = "http://localhost:8001/convert";

export default function RecorderSpike() {
  const [supported, setSupported] = useState<Record<string, boolean>>({});
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState<unknown>(null);
  const recorder = useRef<MediaRecorder | null>(null);

  useEffect(() => {
    if (typeof MediaRecorder === "undefined") {
      setStatus("MediaRecorder is not available in this browser");
      return;
    }
    setSupported(Object.fromEntries(CANDIDATE_TYPES.map((t) => [t, MediaRecorder.isTypeSupported(t)])));
  }, []);

  async function start() {
    try {
      // Must run from a user gesture (the click), or iOS Safari refuses the mic.
      record(await navigator.mediaDevices.getUserMedia({ audio: true }));
    } catch (e) {
      setStatus(`microphone error: ${e}`);
    }
  }

  // Records a 3 s warbling tone through the same MediaRecorder path, for browsers (or the
  // Claude browser pane) where the mic is blocked. The container/codec output is identical.
  function startTone() {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    const dest = ctx.createMediaStreamDestination();
    osc.frequency.value = 220;
    lfo.frequency.value = 3;
    lfoGain.gain.value = 60;
    lfo.connect(lfoGain).connect(osc.frequency);
    osc.connect(dest);
    osc.start();
    lfo.start();
    const rec = record(dest.stream, () => ctx.close());
    setTimeout(() => rec.stop(), 3000);
  }

  function record(stream: MediaStream, cleanup?: () => void): MediaRecorder {
    const mimeType = CANDIDATE_TYPES.find((t) => MediaRecorder.isTypeSupported(t));
    const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      cleanup?.();
      const blob = new Blob(chunks, { type: rec.mimeType });
      setStatus(`uploading ${blob.size} bytes of ${rec.mimeType}…`);
      try {
        const res = await fetch(CONVERT_URL, {
          method: "POST",
          headers: { "Content-Type": rec.mimeType || "application/octet-stream" },
          body: blob,
        });
        setResult(await res.json());
        setStatus("done");
      } catch (e) {
        setStatus(`upload failed: ${e}`);
      }
    };
    rec.start(250);
    recorder.current = rec;
    setResult(null);
    setStatus(`recording as ${rec.mimeType}…`);
    return rec;
  }

  return (
    <main className="mx-auto max-w-2xl space-y-4 p-4 font-mono text-sm">
      <h1 className="text-xl font-semibold">Recorder spike</h1>
      <section>
        <h2 className="font-semibold">MediaRecorder.isTypeSupported</h2>
        <ul>
          {Object.entries(supported).map(([t, ok]) => (
            <li key={t}>
              {ok ? "✅" : "❌"} {t}
            </li>
          ))}
        </ul>
      </section>
      <div className="flex gap-2">
        <button className="rounded border px-3 py-1" onClick={start} disabled={status.startsWith("recording")}>
          Record
        </button>
        <button className="rounded border px-3 py-1" onClick={startTone} disabled={status.startsWith("recording")}>
          Record 3 s test tone (no mic)
        </button>
        <button
          className="rounded border px-3 py-1"
          onClick={() => recorder.current?.stop()}
          disabled={!status.startsWith("recording")}
        >
          Stop and upload
        </button>
      </div>
      <p data-testid="status">Status: {status}</p>
      {result !== null && (
        <pre className="overflow-x-auto rounded border p-2" data-testid="result">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </main>
  );
}
