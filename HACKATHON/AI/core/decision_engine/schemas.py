"""Canonical schemas shared by AI core, SE clients and FastAPI."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Audience = Literal["driver_display", "fleet_dashboard"]
EventStatus = Literal["open", "update", "resolved"]
Severity = Literal["info", "warning", "critical"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DriverMessage(StrictModel):
    message_code: str = Field(min_length=1)
    display_text: str = Field(min_length=1, max_length=160)
    audible: bool = True
    ttl_ms: int = Field(gt=0, le=60000)


class DecisionSnapshot(StrictModel):
    """One synchronized C1+C2+C3 observation consumed in timestamp order."""

    trip_id: str = Field(min_length=1)
    frame_id: int = Field(ge=0)
    timestamp_ms: int = Field(ge=0)
    driver_id: str | None = None
    speed_kmh: float = Field(ge=0)
    speed_limit_kmh: float = Field(gt=0)
    longitudinal_accel: float = 0.0
    lateral_accel: float = 0.0
    predicted_ttc_sec: float = float("inf")
    ttc_confirmed: bool = True
    road_quality_status: str = "valid"
    driver_state: str = "alert"
    driver_confidence: float = Field(default=0.0, ge=0, le=1)
    alertness_score: float = Field(default=1.0, ge=0, le=1)
    driver_quality_status: str = "invalid"
    face_detected: bool = False
    left_eye_valid: bool = False
    right_eye_valid: bool = False
    monitoring_available: bool = False
    valid_window_ratio: float = Field(default=0.0, ge=0, le=1)
    continuous_eye_closure_ms: int = Field(default=0, ge=0)
    perclos_30s: float = Field(default=0.0, ge=0, le=1)
    off_road_duration_ms: int = Field(default=0, ge=0)
    mouth_state: str = "normal"
    mouth_open_duration_ms: int = Field(default=0, ge=0)
    c3_risk_score: float = Field(default=0.0, ge=0, le=100)
    c3_safe_score: float = Field(default=100.0, ge=0, le=100)
    c3_penalty_points: float = Field(default=0.0, ge=0)
    harsh_brake: bool = False
    harsh_accel: bool = False
    harsh_corner: bool = False
    speeding: bool = False
    tailgating: bool = False
    harsh_brake_count: int = Field(default=0, ge=0)
    harsh_accel_count: int = Field(default=0, ge=0)
    harsh_corner_count: int = Field(default=0, ge=0)
    near_miss_count: int = Field(default=0, ge=0)
    speeding_pct_time: float = Field(default=0.0, ge=0, le=100)
    tailgating_pct_time: float = Field(default=0.0, ge=0, le=100)
    avg_headway_sec: float = Field(default=0.0, ge=0)
    vigilance_lapse_probability: float | None = Field(default=None, ge=0, le=1)
    vigilance_evidence_groups: int = Field(default=0, ge=0, le=4)
    hmi_response_latency_ms: int | None = Field(default=None, ge=0)

    @field_validator(
        "speed_kmh",
        "speed_limit_kmh",
        "longitudinal_accel",
        "lateral_accel",
        "alertness_score",
        "perclos_30s",
        "c3_risk_score",
        "c3_safe_score",
        "c3_penalty_points",
        "speeding_pct_time",
        "tailgating_pct_time",
        "avg_headway_sec",
    )
    @classmethod
    def finite_numbers(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("field must be finite")
        return value

    @field_validator("predicted_ttc_sec")
    @classmethod
    def valid_ttc(cls, value: float) -> float:
        if math.isnan(value) or value < 0:
            raise ValueError("predicted_ttc_sec must be non-negative or inf")
        return value


class DecisionEvent(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)
    driver_id: str | None = None
    frame_id: int = Field(ge=0)
    trip_timestamp_ms: int = Field(ge=0)
    timestamp_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: EventStatus
    alert_type: str = Field(min_length=1)
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    audiences: list[Audience]
    driver_message: DriverMessage | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = Field(min_length=1)
    model_versions: dict[str, str] = Field(default_factory=dict)

    def transport_dict(self) -> dict[str, Any]:
        """JSON-safe payload; non-finite internal values become null."""

        def clean(value: Any) -> Any:
            if isinstance(value, float) and not math.isfinite(value):
                return None
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [clean(item) for item in value]
            return value

        return clean(self.model_dump(mode="json"))
