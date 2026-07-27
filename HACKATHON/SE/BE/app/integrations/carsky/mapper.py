from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.domain.schemas.ai_contract import AIFrame, TripMetadata


class CarSkyHMIState(str, Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    RECOVERY = "RECOVERY"


class EventTransition(str, Enum):
    NONE = "NONE"
    START = "START"
    UPDATE = "UPDATE"
    END = "END"


class AIStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


@dataclass(frozen=True)
class CarSkySignalMap:
    driver_state: str = "Vehicle.Driver.State"
    alertness_score: str = "Vehicle.Driver.AlertnessScore"
    speed: str = "Vehicle.Speed"
    speed_limit: str = "Vehicle.SpeedLimit"
    min_ttc: str = "Vehicle.ADAS.MinTTC"
    headway: str = "Vehicle.ADAS.Headway"
    final_risk_score: str = "Vehicle.ADAS.FinalRiskScore"
    critical_alert: str = "Vehicle.ADAS.CriticalAlert"
    display_severity: str = "Vehicle.ADAS.DisplaySeverity"
    alert_reason: str = "Vehicle.ADAS.AlertReasonCode"
    recommended_action: str = "Vehicle.ADAS.RecommendedActionCode"
    event_transition: str = "Vehicle.ADAS.EventTransition"
    ai_status: str = "Vehicle.ADAS.AIStatus"
    data_age_ms: str = "Vehicle.ADAS.DataAgeMs"

    @property
    def required_paths(self) -> tuple[str, ...]:
        return tuple(self.__dict__.values())


class CarSkySignalMapper:
    def __init__(self, signal_map: CarSkySignalMap | None = None) -> None:
        self.paths = signal_map or CarSkySignalMap()

    def map_frame(
        self,
        frame: AIFrame,
        metadata: TripMetadata,
        *,
        severity: CarSkyHMIState = CarSkyHMIState.SAFE,
        reason_code: str = "NONE",
        action_code: str = "NONE",
        transition: EventTransition = EventTransition.NONE,
        ai_status: AIStatus = AIStatus.ONLINE,
        data_age_ms: int = 0,
    ) -> dict[str, list[dict[str, Any]]]:
        if data_age_ms < 0:
            raise ValueError("data_age_ms must not be negative")

        values: list[tuple[str, Any]] = [
            (self.paths.driver_state, frame.driver.state.value),
            (self.paths.alertness_score, frame.driver.alertness_score),
            (self.paths.speed, frame.ego.speed_kmh),
            (self.paths.speed_limit, metadata.speed_limit_kmh),
            (self.paths.final_risk_score, frame.risk.final_risk_score),
            (self.paths.critical_alert, severity is CarSkyHMIState.CRITICAL),
            (self.paths.display_severity, severity.value),
            (self.paths.alert_reason, reason_code),
            (self.paths.recommended_action, action_code),
            (self.paths.event_transition, transition.value),
            (self.paths.ai_status, ai_status.value),
            (self.paths.data_age_ms, data_age_ms),
        ]
        if math.isfinite(frame.min_ttc):
            values.append((self.paths.min_ttc, frame.min_ttc))
        if math.isfinite(frame.headway_sec):
            values.append((self.paths.headway, frame.headway_sec))

        return {"signals": [{"path": path, "value": value} for path, value in values]}
