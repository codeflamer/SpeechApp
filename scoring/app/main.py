from fastapi import FastAPI

# Bump whenever scoring logic or thresholds change; stored on every Attempt (SPEC §6.1).
SCORING_VERSION = "0.0.0"

app = FastAPI(title="Maple scoring")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "scoring_version": SCORING_VERSION}
