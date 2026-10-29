from fastapi.testclient import TestClient

from app.main import SCORING_VERSION, app


def test_health_reports_scoring_version():
    res = TestClient(app).get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "scoring_version": SCORING_VERSION}
