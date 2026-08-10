
from __future__ import annotations
import json, pathlib, sys, tempfile
sys.path.insert(0, "/Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE")
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings

def make_client():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="e14_restart_"))
    return TestClient(create_app(Settings(APP_ENV="test", DATASET_DIR=tmp / "dataset", OUTPUT_SUBMISSION_DIR=tmp / "submissions", AI_SOURCE_MODE="file", _env_file=None)))

def event(suffix="1"):
    return {
        "schema_version": "1.0",
        "event_id": f"e14-evt-{suffix}",
        "idempotency_key": f"e14-evt-{suffix}-open-100",
        "trip_id": "T01-Sample",
        "driver_id": "driver_001",
        "frame_id": 2,
        "trip_timestamp_ms": 100,
        "timestamp_utc": "2026-08-10T00:00:00Z",
        "status": "open",
        "alert_type": "collision_risk",
        "severity": "critical",
        "confidence": 1.0,
        "audiences": ["driver_display", "fleet_dashboard"],
        "evidence": {"predicted_ttc_sec": 1.0, "risk_score": 88},
        "recommended_action": "Brake safely",
    }

trace = []
c1 = make_client()
p = event("dedup")
for label in ["first", "duplicate"]:
    r = c1.post("/api/v1/alerts", json=p, headers={"Idempotency-Key": p["idempotency_key"]})
    trace.append({"check": f"dedup_{label}", "status_code": r.status_code, "body": r.json()})
r = c1.get("/api/v1/alerts/recent")
trace.append({"check": "recent_before_restart", "status_code": r.status_code, "body": r.json()})
try:
    with c1.websocket_connect("/api/v1/alerts/live") as ws:
        p2 = event("ws")
        r2 = c1.post("/api/v1/alerts", json=p2, headers={"Idempotency-Key": p2["idempotency_key"]})
        msg = ws.receive_json()
        trace.append({"check": "websocket_broadcast", "post_status_code": r2.status_code, "message_event_id": msg.get("event_id"), "message_trip_id": msg.get("trip_id"), "message_severity": msg.get("severity")})
except Exception as exc:
    trace.append({"check": "websocket_broadcast", "error": repr(exc)})
c2 = make_client()
r = c2.get("/api/v1/alerts/recent")
trace.append({"check": "recent_after_new_app_restart", "status_code": r.status_code, "body": r.json(), "interpretation": "in-memory recent alerts are not durable across backend process restart"})
print("\n".join(json.dumps(x, ensure_ascii=False) for x in trace))
