from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any, Literal

from fastapi import (
    APIRouter,
    Body,
    Header,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

from app.integrations.carsky.mapper import CarSkySignalMapper
from app.integrations.carsky.service import DeliveryKind


class DecisionEventPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = "1.0"
    event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)
    driver_id: str | None = None
    frame_id: int = Field(ge=0)
    trip_timestamp_ms: int = Field(ge=0)
    timestamp_utc: datetime
    status: Literal["open", "update", "resolved"]
    alert_type: str = Field(min_length=1)
    severity: Literal["info", "warning", "critical"]
    confidence: float = Field(ge=0, le=1)
    audiences: list[Literal["driver_display", "fleet_dashboard"]]
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = Field(min_length=1)


class LiveSnapshotPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    trip_id: str = Field(min_length=1)
    frame_id: int = Field(ge=0)
    trip_timestamp_ms: int = Field(ge=0)
    speed_kmh: float = Field(ge=0)
    predicted_ttc_sec: float | None = Field(default=None, ge=0)
    risk_score: float = Field(ge=0, le=100)
    driver_state: str = Field(min_length=1)
    driver_confidence: float = Field(ge=0, le=1)
    alertness_score: float = Field(ge=0, le=1)


class TripRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trip_id: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TripRegistrationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trips: list[TripRegistration] = Field(min_length=1)
    reset_existing: bool = False


router = APIRouter(prefix="/alerts", tags=["AI Decision Alerts"])
live_clients: set[WebSocket] = set()
carsky_mapper = CarSkySignalMapper()
MAX_CABIN_FRAME_BYTES = 2 * 1024 * 1024


async def _broadcast(document: dict[str, Any]) -> None:
    stale: list[WebSocket] = []
    for client in tuple(live_clients):
        try:
            await client.send_json(document)
        except Exception:
            stale.append(client)
    for client in stale:
        live_clients.discard(client)


def _store(request: Request) -> tuple[deque[dict[str, Any]], set[str]]:
    if not hasattr(request.app.state, "decision_alerts"):
        request.app.state.decision_alerts = deque(maxlen=1000)
        request.app.state.decision_alert_keys = set()
    return request.app.state.decision_alerts, request.app.state.decision_alert_keys


def _trip_store(request: Request) -> dict[str, dict[str, Any]]:
    if not hasattr(request.app.state, "live_trip_sessions"):
        request.app.state.live_trip_sessions = {}
    return request.app.state.live_trip_sessions


def _ensure_trip(
    request: Request,
    trip_id: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sessions = _trip_store(request)
    session = sessions.setdefault(
        trip_id,
        {
            "trip_id": trip_id,
            "status": "pending",
            "metadata": {},
            "latest_snapshot": None,
            "snapshot_history": deque(maxlen=2400),
        },
    )
    if metadata:
        session["metadata"] = {**session["metadata"], **metadata}
    return session


def _public_session(session: dict[str, Any]) -> dict[str, Any]:
    return {
        **session,
        "snapshot_history": list(session["snapshot_history"]),
    }


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def receive_alert(
    payload: DecisionEventPayload,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> dict[str, Any]:
    if idempotency_key != payload.idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key mismatch")
    alerts, keys = _store(request)
    duplicate = idempotency_key in keys
    if not duplicate:
        document = payload.model_dump(mode="json")
        _ensure_trip(request, payload.trip_id)
        alerts.append(document)
        keys.add(idempotency_key)
        await _broadcast(document)
        publisher = getattr(request.app.state, "carsky_publisher", None)
        if publisher is not None and "driver_display" in payload.audiences:
            await publisher.enqueue(
                carsky_mapper.map_decision_event(document),
                dedup_key=payload.idempotency_key,
                kind=DeliveryKind.TRANSITION,
            )
    return {
        "accepted": True,
        "duplicate": duplicate,
        "event_id": payload.event_id,
    }


@router.get("/recent")
async def recent_alerts(request: Request, limit: int = 100) -> dict[str, Any]:
    alerts, _ = _store(request)
    safe_limit = min(max(limit, 1), 1000)
    values = list(alerts)[-safe_limit:]
    return {"count": len(values), "items": values}


@router.post("/trips/register", status_code=status.HTTP_202_ACCEPTED)
async def register_live_trips(
    payload: TripRegistrationPayload,
    request: Request,
) -> dict[str, Any]:
    sessions = _trip_store(request)
    if payload.reset_existing:
        reset_ids = {trip.trip_id for trip in payload.trips}
        for trip_id in reset_ids:
            sessions.pop(trip_id, None)
        for attribute in ("latest_cabin_frames", "latest_road_frames"):
            frames = getattr(request.app.state, attribute, {})
            for trip_id in reset_ids:
                frames.pop(trip_id, None)
        alerts, keys = _store(request)
        retained = [
            item for item in alerts if item.get("trip_id") not in reset_ids
        ]
        alerts.clear()
        alerts.extend(retained)
        keys.clear()
        keys.update(item["idempotency_key"] for item in retained)
    for trip in payload.trips:
        _ensure_trip(request, trip.trip_id, trip.metadata)
    return {
        "accepted": True,
        "count": len(payload.trips),
        "trip_ids": [trip.trip_id for trip in payload.trips],
    }


@router.post("/trips/{trip_id}/complete")
async def complete_live_trip(trip_id: str, request: Request) -> dict[str, Any]:
    session = _ensure_trip(request, trip_id)
    session["status"] = "completed"
    return {"accepted": True, "trip_id": trip_id, "status": "completed"}


@router.get("/trips")
async def live_trips(request: Request) -> dict[str, Any]:
    sessions = _trip_store(request)
    items = [_public_session(session) for session in sessions.values()]
    return {"count": len(items), "items": items}


@router.post("/cabin-frame", status_code=status.HTTP_202_ACCEPTED)
async def receive_cabin_frame(
    request: Request,
    frame: bytes = Body(media_type="image/jpeg"),
    trip_id: str = Header(alias="X-Trip-ID", min_length=1),
    frame_id: int = Header(alias="X-Frame-ID", ge=0),
    timestamp_ms: int = Header(alias="X-Timestamp-MS", ge=0),
    content_type: str | None = Header(default=None, alias="Content-Type"),
) -> dict[str, Any]:
    if content_type is None or content_type.split(";", 1)[0].strip().lower() != "image/jpeg":
        raise HTTPException(status_code=415, detail="Cabin frame must be image/jpeg")
    if not frame or len(frame) > MAX_CABIN_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="Cabin frame is empty or exceeds 2 MiB")
    if not frame.startswith(b"\xff\xd8") or not frame.endswith(b"\xff\xd9"):
        raise HTTPException(status_code=400, detail="Cabin frame is not a valid JPEG envelope")
    frames = getattr(request.app.state, "latest_cabin_frames", None)
    if frames is None:
        frames = request.app.state.latest_cabin_frames = {}
    frames[trip_id] = {
        "content": frame,
        "trip_id": trip_id,
        "frame_id": frame_id,
        "timestamp_ms": timestamp_ms,
    }
    return {"accepted": True, "trip_id": trip_id, "frame_id": frame_id}


@router.get("/cabin-frame", response_class=Response)
async def latest_cabin_frame(
    request: Request,
    trip_id: str | None = None,
) -> Response:
    frames = getattr(request.app.state, "latest_cabin_frames", {})
    frame = frames.get(trip_id) if trip_id is not None else next(
        reversed(frames.values()), None
    )
    if frame is None:
        raise HTTPException(status_code=404, detail="No live cabin frame for this trip")
    return Response(
        content=frame["content"],
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "X-Trip-ID": str(frame["trip_id"]),
            "X-Frame-ID": str(frame["frame_id"]),
            "X-Timestamp-MS": str(frame["timestamp_ms"]),
        },
    )


@router.post("/road-frame", status_code=status.HTTP_202_ACCEPTED)
async def receive_road_frame(
    request: Request,
    frame: bytes = Body(media_type="image/jpeg"),
    trip_id: str = Header(alias="X-Trip-ID", min_length=1),
    frame_id: int = Header(alias="X-Frame-ID", ge=0),
    timestamp_ms: int = Header(alias="X-Timestamp-MS", ge=0),
    content_type: str | None = Header(default=None, alias="Content-Type"),
) -> dict[str, Any]:
    if content_type is None or content_type.split(";", 1)[0].strip().lower() != "image/jpeg":
        raise HTTPException(status_code=415, detail="Road frame must be image/jpeg")
    if not frame or len(frame) > MAX_CABIN_FRAME_BYTES:
        raise HTTPException(status_code=413, detail="Road frame is empty or exceeds 2 MiB")
    if not frame.startswith(b"\xff\xd8") or not frame.endswith(b"\xff\xd9"):
        raise HTTPException(status_code=400, detail="Road frame is not a valid JPEG envelope")
    frames = getattr(request.app.state, "latest_road_frames", None)
    if frames is None:
        frames = request.app.state.latest_road_frames = {}
    frames[trip_id] = {
        "content": frame,
        "trip_id": trip_id,
        "frame_id": frame_id,
        "timestamp_ms": timestamp_ms,
    }
    return {"accepted": True, "trip_id": trip_id, "frame_id": frame_id}


@router.get("/road-frame", response_class=Response)
async def latest_road_frame(request: Request, trip_id: str | None = None) -> Response:
    frames = getattr(request.app.state, "latest_road_frames", {})
    frame = frames.get(trip_id) if trip_id is not None else next(
        reversed(frames.values()), None
    )
    if frame is None:
        raise HTTPException(status_code=404, detail="No live road frame for this trip")
    return Response(
        content=frame["content"],
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "X-Trip-ID": str(frame["trip_id"]),
            "X-Frame-ID": str(frame["frame_id"]),
            "X-Timestamp-MS": str(frame["timestamp_ms"]),
        },
    )


@router.post("/snapshot", status_code=status.HTTP_202_ACCEPTED)
async def receive_live_snapshot(
    payload: LiveSnapshotPayload,
    request: Request,
) -> dict[str, Any]:
    document = payload.model_dump(mode="json")
    session = _ensure_trip(request, payload.trip_id)
    session["status"] = "running"
    session["latest_snapshot"] = document
    session["snapshot_history"].append(document)
    return {"accepted": True, "trip_id": payload.trip_id, "frame_id": payload.frame_id}


@router.get("/snapshot")
async def latest_live_snapshot(request: Request, trip_id: str | None = None) -> dict[str, Any]:
    sessions = _trip_store(request)
    if trip_id is not None:
        session = sessions.get(trip_id)
    else:
        session = next(reversed(sessions.values()), None)
    snapshot = session.get("latest_snapshot") if session is not None else None
    if snapshot is None:
        raise HTTPException(status_code=404, detail="No live snapshot for this trip")
    return snapshot


@router.websocket("/live")
async def live_alerts(websocket: WebSocket) -> None:
    await websocket.accept()
    live_clients.add(websocket)
    try:
        while True:
            # Client messages act as keepalive; alert flow is server -> client.
            await websocket.receive_text()
    except WebSocketDisconnect:
        live_clients.discard(websocket)
