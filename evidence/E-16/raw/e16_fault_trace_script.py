
from __future__ import annotations
import json, pathlib, sys, tempfile
sys.path.insert(0, "/Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE")
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings
client = TestClient(create_app(Settings(APP_ENV="test", DATASET_DIR=pathlib.Path(tempfile.mkdtemp()) / "dataset", OUTPUT_SUBMISSION_DIR=pathlib.Path(tempfile.mkdtemp()) / "submissions", AI_SOURCE_MODE="file", _env_file=None)))
valid = {
    "schema_version": "1.0",
    "event_id": "e16-valid",
    "idempotency_key": "e16-valid-open-1",
    "trip_id": "T01-Sample",
    "driver_id": "driver_001",
    "frame_id": 1,
    "trip_timestamp_ms": 50,
    "timestamp_utc": "2026-08-10T00:00:00Z",
    "status": "open",
    "alert_type": "collision_risk",
    "severity": "critical",
    "confidence": 1.0,
    "audiences": ["driver_display", "fleet_dashboard"],
    "evidence": {"predicted_ttc_sec": 1.0},
    "recommended_action": "Brake safely",
}
rows = []
bad = dict(valid)
bad.pop("event_id")
r = client.post("/api/v1/alerts", json=bad, headers={"Idempotency-Key": bad["idempotency_key"]})
rows.append({"case": "malformed_decision_event_missing_event_id", "status_code": r.status_code, "body": r.json(), "safe_state": "rejected; no accepted alert fabricated"})
bad2 = dict(valid)
bad2["idempotency_key"] = "payload-key"
r = client.post("/api/v1/alerts", json=bad2, headers={"Idempotency-Key": "header-key"})
rows.append({"case": "idempotency_key_mismatch", "status_code": r.status_code, "body": r.json(), "safe_state": "rejected before store/broadcast"})
r = client.get("/api/v1/alerts/snapshot?trip_id=missing-trip")
rows.append({"case": "missing_live_snapshot", "status_code": r.status_code, "body": r.json(), "safe_state": "404; frontend can fall back to saved frame/offline state"})
r = client.post("/api/v1/alerts", json=valid, headers={"Idempotency-Key": valid["idempotency_key"]})
rows.append({"case": "recovery_valid_event_after_errors", "status_code": r.status_code, "body": r.json(), "safe_state": "accepted after rejected errors"})
print("\n".join(json.dumps(x, ensure_ascii=False) for x in rows))
