"""Validated YAML policy for the Decision Engine."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GeneralPolicy(StrictModel):
    moving_speed_kmh: float = Field(ge=0)
    driver_warning_min_speed_kmh: float = Field(ge=0)
    max_source_skew_ms: int = Field(ge=0)
    max_realtime_age_ms: int = Field(gt=0)
    min_valid_window_ratio: float = Field(ge=0, le=1)
    min_driver_confidence: float = Field(ge=0, le=1)
    startup_warmup_ms: int = Field(ge=0)
    perclos_warmup_ms: int = Field(ge=0)
    update_interval_ms: int = Field(gt=0)


class TTCPolicy(StrictModel):
    watch_sec: float = Field(gt=0)
    warning_sec: float = Field(gt=0)
    critical_sec: float = Field(gt=0)
    warning_persistence_ms: int = Field(ge=0)
    recovery_sec: float = Field(gt=0)
    recovery_ms: int = Field(ge=0)
    cooldown_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> "TTCPolicy":
        if not self.critical_sec < self.warning_sec < self.watch_sec:
            raise ValueError("TTC thresholds must be critical < warning < watch")
        if self.recovery_sec <= self.warning_sec:
            raise ValueError("TTC recovery must be above warning threshold")
        return self


class MicrosleepPolicy(StrictModel):
    reliable_closure_ms: int = Field(gt=0)
    ml_confidence: float = Field(ge=0, le=1)
    ml_persistence_ms: int = Field(ge=0)
    stopped_warning_closure_ms: int = Field(gt=0)
    stopped_fleet_closure_ms: int = Field(gt=0)
    recovery_ms: int = Field(ge=0)
    cooldown_ms: int = Field(ge=0)


class DistractionPolicy(StrictModel):
    high_speed_kmh: float = Field(gt=0)
    high_speed_duration_ms: int = Field(gt=0)
    medium_speed_kmh: float = Field(gt=0)
    medium_speed_duration_ms: int = Field(gt=0)
    critical_duration_ms: int = Field(gt=0)
    gaze_gap_tolerance_ms: int = Field(ge=0)
    recovery_ms: int = Field(ge=0)
    cooldown_ms: int = Field(ge=0)


class DrowsinessPolicy(StrictModel):
    perclos_watch: float = Field(ge=0, le=1)
    perclos_warning: float = Field(ge=0, le=1)
    perclos_critical: float = Field(ge=0, le=1)
    perclos_persistence_ms: int = Field(ge=0)
    ml_watch_confidence: float = Field(ge=0, le=1)
    ml_watch_persistence_ms: int = Field(ge=0)
    warning_confidence: float = Field(ge=0, le=1)
    warning_alertness_max: float = Field(ge=0, le=1)
    warning_persistence_ms: int = Field(ge=0)
    critical_warning_persistence_ms: int = Field(ge=0)
    strong_yawn_ms: int = Field(gt=0)
    yawn_count: int = Field(gt=0)
    yawn_window_ms: int = Field(gt=0)
    yawn_perclos_min: float = Field(ge=0, le=1)
    yawn_alertness_max: float = Field(ge=0, le=1)
    recovery_alertness_min: float = Field(ge=0, le=1)
    recovery_perclos_max: float = Field(ge=0, le=1)
    recovery_ms: int = Field(ge=0)
    cooldown_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_perclos_order(self) -> "DrowsinessPolicy":
        if not self.perclos_watch < self.perclos_warning < self.perclos_critical:
            raise ValueError("PERCLOS thresholds must be watch < warning < critical")
        return self


class SpeedingPolicy(StrictModel):
    warning_over_limit_kmh: float = Field(gt=0)
    warning_persistence_ms: int = Field(ge=0)
    critical_over_limit_kmh: float = Field(gt=0)
    critical_persistence_ms: int = Field(ge=0)
    recovery_over_limit_kmh: float = Field(ge=0)
    recovery_ms: int = Field(ge=0)
    cooldown_ms: int = Field(ge=0)


class HarshBehaviorPolicy(StrictModel):
    brake_g: float = Field(gt=0)
    accel_g: float = Field(gt=0)
    corner_g: float = Field(gt=0)
    episode_confirm_ms: int = Field(ge=0)
    episode_end_ms: int = Field(ge=0)
    warning_count: int = Field(gt=0)
    warning_window_ms: int = Field(gt=0)
    cooldown_ms: int = Field(ge=0)


class RiskTierPolicy(StrictModel):
    thresholds: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "RiskTierPolicy":
        if self.thresholds != sorted(set(self.thresholds)):
            raise ValueError("risk tier thresholds must be sorted and unique")
        if any(value <= 0 or value > 100 for value in self.thresholds):
            raise ValueError("risk tier thresholds must be in (0, 100]")
        return self


class SensorHealthPolicy(StrictModel):
    carsky_after_ms: int = Field(gt=0)
    fleet_after_ms: int = Field(gt=0)
    recovery_ms: int = Field(ge=0)
    cooldown_ms: int = Field(ge=0)


class VigilanceLapsePolicy(StrictModel):
    enabled: bool
    shadow_only: bool
    watch_probability: float = Field(ge=0, le=1)
    watch_persistence_ms: int = Field(ge=0)
    prompt_probability: float = Field(ge=0, le=1)
    prompt_persistence_ms: int = Field(ge=0)
    warning_probability: float = Field(ge=0, le=1)
    warning_persistence_ms: int = Field(ge=0)
    critical_probability: float = Field(ge=0, le=1)
    response_timeout_ms: int = Field(gt=0)
    reset_probability: float = Field(ge=0, le=1)
    reset_persistence_ms: int = Field(ge=0)
    prompt_cooldown_ms: int = Field(ge=0)


class DecisionPolicy(StrictModel):
    version: str = Field(min_length=1)
    enabled: bool
    general: GeneralPolicy
    ttc: TTCPolicy
    microsleep: MicrosleepPolicy
    distraction: DistractionPolicy
    drowsiness: DrowsinessPolicy
    speeding: SpeedingPolicy
    harsh_behavior: HarshBehaviorPolicy
    risk_tiers: RiskTierPolicy
    sensor_health: SensorHealthPolicy
    vigilance_lapse: VigilanceLapsePolicy

    @classmethod
    def load(cls, path: str | Path) -> "DecisionPolicy":
        document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("Decision Engine config must be a YAML mapping")
        return cls.model_validate(document)
