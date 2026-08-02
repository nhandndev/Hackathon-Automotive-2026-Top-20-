"""Reference FastAPI receiver for the SE team.

This is a contract/demo receiver, not the production Fleet Dashboard backend.
SE can replace storage, authentication and downstream Fleet/CarSky routing
without changing the canonical DecisionEvent payload.
"""
from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict

from core.decision_engine.schemas import DecisionEvent


class AckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: bool
    duplicate: bool
    event_id: str
    idempotency_key: str


app = FastAPI(
    title="FPTU DMS Decision Event Contract",
    version="1.0.0",
    description=(
        "Reference receiver for canonical AI DecisionEvents. "
        "Production authentication, persistence and routing belong to SE."
    ),
)

_recent: deque[dict[str, Any]] = deque(maxlen=100)
_idempotency_keys: set[str] = set()
_lock = Lock()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "se-reference-api", "schema": "1.0"}


@app.post(
    "/api/v1/alerts",
    response_model=AckResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_alert(
    event: DecisionEvent,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> AckResponse:
    if idempotency_key != event.idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header must match payload",
        )
    with _lock:
        duplicate = idempotency_key in _idempotency_keys
        if not duplicate:
            _idempotency_keys.add(idempotency_key)
            _recent.append(event.transport_dict())
    return AckResponse(
        accepted=True,
        duplicate=duplicate,
        event_id=event.event_id,
        idempotency_key=idempotency_key,
    )


@app.get("/api/v1/alerts/recent")
def recent_alerts(limit: int = 20) -> dict[str, Any]:
    """Development-only inspection endpoint for contract testing."""
    bounded = max(1, min(int(limit), 100))
    with _lock:
        events = list(_recent)[-bounded:]
    return {"count": len(events), "events": events}
