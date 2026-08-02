from fastapi.testclient import TestClient


class FakePublisher:
    def __init__(self):
        self.deliveries = []

    async def enqueue(self, payload, *, dedup_key, kind):
        self.deliveries.append((payload, dedup_key, kind))
        return True

    async def stop(self):
        return None


def test_ai_alert_is_idempotent(client: TestClient):
    payload = {
        "schema_version": "1.0",
        "event_id": "evt-1",
        "idempotency_key": "evt-1-open-100",
        "trip_id": "T01-Sample",
        "driver_id": "driver_001",
        "frame_id": 2,
        "trip_timestamp_ms": 100,
        "timestamp_utc": "2026-08-02T00:00:00Z",
        "status": "open",
        "alert_type": "collision_risk",
        "severity": "critical",
        "confidence": 1.0,
        "audiences": ["driver_display", "fleet_dashboard"],
        "evidence": {"predicted_ttc_sec": 1.0},
        "recommended_action": "Brake safely",
    }
    headers = {"Idempotency-Key": payload["idempotency_key"]}
    first = client.post("/api/v1/alerts", json=payload, headers=headers)
    second = client.post("/api/v1/alerts", json=payload, headers=headers)
    assert first.status_code == 202
    assert first.json()["duplicate"] is False
    assert second.status_code == 202
    assert second.json()["duplicate"] is True
    recent = client.get("/api/v1/alerts/recent")
    assert recent.status_code == 200
    assert recent.json()["count"] == 1


def test_driver_alert_is_forwarded_to_carsky_once(client: TestClient):
    publisher = FakePublisher()
    client.app.state.carsky_publisher = publisher
    payload = {
        "schema_version": "1.0",
        "event_id": "evt-c1",
        "idempotency_key": "evt-c1-open-100",
        "trip_id": "T01-Sample",
        "frame_id": 2,
        "trip_timestamp_ms": 100,
        "timestamp_utc": "2026-08-02T00:00:00Z",
        "status": "open",
        "alert_type": "collision_risk",
        "severity": "critical",
        "confidence": 1.0,
        "audiences": ["driver_display", "fleet_dashboard"],
        "evidence": {
            "driver_state": "drowsy",
            "speed_kmh": 60,
            "predicted_ttc_sec": 1.0,
            "c3_risk_score": 40,
        },
        "recommended_action": "Brake safely",
    }
    headers = {"Idempotency-Key": payload["idempotency_key"]}
    assert client.post("/api/v1/alerts", json=payload, headers=headers).status_code == 202
    assert client.post("/api/v1/alerts", json=payload, headers=headers).json()["duplicate"] is True
    assert len(publisher.deliveries) == 1
    signals = {
        item["path"]: item["value"]
        for item in publisher.deliveries[0][0]["signals"]
    }
    assert signals["Vehicle.ADAS.DisplaySeverity"] == "CRITICAL"
    assert signals["Vehicle.ADAS.MinTTC"] == 1.0


def test_live_trip_registry_keeps_completed_trip_history(client: TestClient):
    registration = {
        "trips": [
            {"trip_id": "T01-Sample", "metadata": {"fps": 20}},
            {"trip_id": "T02-Sample", "metadata": {"fps": 20}},
        ]
    }
    assert client.post(
        "/api/v1/alerts/trips/register", json=registration
    ).status_code == 202

    def snapshot(trip_id: str, frame_id: int) -> dict:
        return {
            "schema_version": "1.0",
            "trip_id": trip_id,
            "frame_id": frame_id,
            "trip_timestamp_ms": frame_id * 50,
            "speed_kmh": 30,
            "predicted_ttc_sec": 2.5,
            "risk_score": 40,
            "driver_state": "alert",
            "driver_confidence": 0.9,
            "alertness_score": 0.9,
        }

    assert client.post(
        "/api/v1/alerts/snapshot", json=snapshot("T01-Sample", 1)
    ).status_code == 202
    assert client.post(
        "/api/v1/alerts/trips/T01-Sample/complete"
    ).status_code == 200
    assert client.post(
        "/api/v1/alerts/snapshot", json=snapshot("T02-Sample", 2)
    ).status_code == 202

    sessions = client.get("/api/v1/alerts/trips").json()["items"]
    by_id = {item["trip_id"]: item for item in sessions}
    assert by_id["T01-Sample"]["status"] == "completed"
    assert by_id["T01-Sample"]["latest_snapshot"]["frame_id"] == 1
    assert len(by_id["T01-Sample"]["snapshot_history"]) == 1
    assert by_id["T02-Sample"]["status"] == "running"
    assert client.get(
        "/api/v1/alerts/snapshot?trip_id=T01-Sample"
    ).json()["frame_id"] == 1
