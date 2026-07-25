from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.ai_contract import AIFrame, BackendEnrichment


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str
    stream_fps: float


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dataset_ready: bool
    cached_trips: int = Field(ge=0)
    expected_trips: int = Field(default=10, ge=1)
    external_ai_ready: bool
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | list[Any] | None = None
    request_id: str | None = None


class ReplayEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    trip_id: str
    frame: AIFrame | None = None
    backend_enrichment: BackendEnrichment | None = None


class LeaderboardResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    items: list[dict[str, Any]] = Field(default_factory=list)


class CompareResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trip_a: str
    trip_b: str


class EventsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trip_id: str
    total_events: int = Field(ge=0)
    events: list[dict[str, Any]] = Field(default_factory=list)


class CoachingResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    answer: str
    source: str
    action_buttons: list[dict[str, Any]] = Field(default_factory=list)
