from __future__ import annotations

import math
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


class AIContractModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class DriverState(str, Enum):
    ALERT = "alert"
    DROWSY = "drowsy"
    YAWNING = "yawning"
    DISTRACTED = "distracted"
    MICROSLEEP = "microsleep"


class TripMetadata(AIContractModel):
    trip_id: str = Field(min_length=1)
    description: str
    duration_sec: float = Field(ge=0)
    fps: float = Field(gt=0)
    map: str
    driver_profile: str
    carla_version: str
    random_seed: int
    speed_limit_kmh: float = Field(ge=0)


class Geolocation(AIContractModel):
    lat: float
    lon: float
    alt: float


class Ego(AIContractModel):
    speed_kmh: float = Field(ge=0)
    longitudinal_accel: float
    lateral_accel: float
    geolocation: Geolocation


class Driver(AIContractModel):
    state: DriverState
    alertness_score: float = Field(ge=0, le=1)
    eye_state: str
    head_pose: str
    mouth_state: str
    nthu_subject_id: str


class BehaviorFlags(AIContractModel):
    harsh_brake: bool
    harsh_accel: bool
    harsh_corner: bool
    speeding: bool
    tailgating: bool


class AIRisk(AIContractModel):
    base_risk: float = Field(ge=0, le=100)
    driver_factor: float
    final_risk_score: float = Field(ge=0, le=100)


def normalize_distance_time(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid TTC/headway value")
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"inf", "infinity", "+inf", "+infinity"}:
            return math.inf
        try:
            value = float(normalized)
        except ValueError as exc:
            raise ValueError("value must be a number or 'Infinity'") from exc
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be a number or 'Infinity'") from exc
    if math.isnan(parsed) or parsed == -math.inf:
        raise ValueError("NaN and -Infinity are not valid TTC/headway values")
    return parsed


class AIFrame(AIContractModel):
    frame_id: int = Field(ge=0)
    timestamp: float = Field(ge=0)
    ego: Ego
    driver: Driver
    min_ttc: float
    headway_sec: float
    behavior_flags: BehaviorFlags
    risk: AIRisk

    @field_validator("min_ttc", "headway_sec", mode="before")
    @classmethod
    def validate_distance_time(cls, value: Any) -> float:
        return normalize_distance_time(value)

    @field_serializer("min_ttc", "headway_sec", when_used="json")
    def serialize_distance_time(self, value: float) -> float | str:
        return "Infinity" if math.isinf(value) else value


class AITrip(AIContractModel):
    trip_id: str = Field(min_length=1)
    metadata: TripMetadata
    frames: list[AIFrame] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_trip_ids(self) -> "AITrip":
        if self.trip_id != self.metadata.trip_id:
            raise ValueError("trip_id must match metadata.trip_id")
        return self


class BackendEnrichment(BaseModel):
    model_config = ConfigDict(extra="allow")

    severity: str | None = None
    reasoning: str | None = None
    recommended_action: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
