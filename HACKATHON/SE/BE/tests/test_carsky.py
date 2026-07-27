from __future__ import annotations

import json

import httpx
import pytest

from app.domain.schemas.ai_contract import AIFrame, TripMetadata
from app.integrations.carsky.client import CarSkyClient, CarSkyDeliveryError
from app.integrations.carsky.mapper import (
    CarSkyHMIState,
    CarSkySignalMapper,
    EventTransition,
)
from app.integrations.carsky.service import CarSkyPublisher, DeliveryKind


def make_metadata() -> TripMetadata:
    return TripMetadata(
        trip_id="T01d",
        description="mock",
        duration_sec=90,
        fps=20,
        map="Town01",
        driver_profile="normal",
        carla_version="0.9.15",
        random_seed=1001,
        speed_limit_kmh=80,
    )


def make_frame() -> AIFrame:
    return AIFrame.model_validate(
        {
            "frame_id": 0,
            "timestamp": 0,
            "ego": {
                "speed_kmh": 75,
                "longitudinal_accel": 0,
                "lateral_accel": 0,
                "geolocation": {"lat": 0, "lon": 0, "alt": 0},
            },
            "driver": {
                "state": "distracted",
                "alertness_score": 0.45,
                "eye_state": "open",
                "head_pose": "side",
                "mouth_state": "normal",
                "nthu_subject_id": "14",
            },
            "min_ttc": "Infinity",
            "headway_sec": "Infinity",
            "behavior_flags": {
                "harsh_brake": False,
                "harsh_accel": False,
                "harsh_corner": False,
                "speeding": False,
                "tailgating": False,
            },
            "risk": {"base_risk": 20, "driver_factor": 2.2, "final_risk_score": 55},
        }
    )


def test_mapper_omits_infinite_ttc_and_preserves_ai_risk() -> None:
    payload = CarSkySignalMapper().map_frame(
        make_frame(),
        make_metadata(),
        severity=CarSkyHMIState.WARNING,
        reason_code="DISTRACTED",
        action_code="FOCUS_FORWARD",
        transition=EventTransition.START,
    )
    mapped = {item["path"]: item["value"] for item in payload["signals"]}
    assert "Vehicle.ADAS.MinTTC" not in mapped
    assert "Vehicle.ADAS.Headway" not in mapped
    assert mapped["Vehicle.ADAS.FinalRiskScore"] == 55
    assert mapped["Vehicle.ADAS.DisplaySeverity"] == "WARNING"


@pytest.mark.asyncio
async def test_client_uses_bearer_and_expected_path() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/signals/room-1/node-1/actuate"
        assert request.headers["Authorization"] == "Bearer secret"
        assert json.loads(request.content)["signals"]
        return httpx.Response(200, json={"ok": True})

    client = CarSkyClient(
        base_url="https://carsky.test",
        api_key="secret",
        room_id="room-1",
        node_key="node-1",
        transport=httpx.MockTransport(handler),
    )
    try:
        assert await client.actuate({"signals": [{"path": "x", "value": 1}]}) == {"ok": True}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_client_does_not_retry_auth_failure() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, json={"detail": "invalid"})

    client = CarSkyClient(
        base_url="https://carsky.test",
        api_key="wrong",
        room_id="room-1",
        node_key="node-1",
        max_retries=2,
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(CarSkyDeliveryError):
            await client.actuate({"signals": []})
        assert calls == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_publisher_delivers_without_blocking_producer() -> None:
    delivered: list[dict] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        delivered.append(json.loads(request.content))
        return httpx.Response(200, json={"ok": True})

    client = CarSkyClient(
        base_url="https://carsky.test",
        api_key="secret",
        room_id="room-1",
        node_key="node-1",
        transport=httpx.MockTransport(handler),
    )
    publisher = CarSkyPublisher(client, queue_size=2)
    await publisher.start()
    try:
        accepted = await publisher.enqueue(
            {"signals": [{"path": "x", "value": True}]},
            dedup_key="T01d:episode-1:START",
            kind=DeliveryKind.TRANSITION,
        )
        assert accepted is True
        await publisher.queue.join()
        assert delivered and publisher.delivery_status == "ready"
    finally:
        await publisher.stop()
