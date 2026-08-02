from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

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

    def map_decision_event(
        self,
        event: Mapping[str, Any],
        *,
        data_age_ms: int = 0,
    ) -> dict[str, list[dict[str, Any]]]:
        """Map the AI-owned DecisionEvent without recomputing its decision.

        Only evidence already emitted by AI is forwarded. Missing telemetry is
        omitted instead of fabricated. Alert type/severity/lifecycle remain
        owned by AI; Backend only translates them to the stable VSS vocabulary.
        """
        if data_age_ms < 0:
            raise ValueError("data_age_ms must not be negative")
        status = str(event.get("status", "update")).lower()
        severity = str(event.get("severity", "warning")).lower()
        alert_type = str(event.get("alert_type", "unknown"))
        evidence = event.get("evidence") or {}
        if not isinstance(evidence, Mapping):
            evidence = {}

        hmi_state = (
            CarSkyHMIState.RECOVERY
            if status == "resolved"
            else CarSkyHMIState.CRITICAL
            if severity == "critical"
            else CarSkyHMIState.WARNING
        )
        transition = {
            "open": EventTransition.START,
            "update": EventTransition.UPDATE,
            "resolved": EventTransition.END,
        }.get(status, EventTransition.UPDATE)
        reason_code = {
            "collision_risk": "TTC_CRITICAL",
            "microsleep": "MICROSLEEP",
            "driver_drowsiness": "DROWSY",
            "driver_distraction": "DISTRACTED",
            "yawning": "YAWNING",
            "tailgating": "TAILGATING",
            "speeding": "SPEEDING",
            "harsh_brake": "HARSH_BRAKE",
            "harsh_accel": "HARSH_ACCEL",
            "harsh_corner": "HARSH_CORNER",
        }.get(alert_type, "NONE")
        action_code = {
            "collision_risk": "BRAKE_SAFE",
            "microsleep": "TAKE_BREAK",
            "driver_drowsiness": "TAKE_BREAK",
            "driver_distraction": "FOCUS_FORWARD",
            "speeding": "REDUCE_SPEED",
        }.get(alert_type, "NONE")

        values: list[tuple[str, Any]] = [
            (self.paths.critical_alert, hmi_state is CarSkyHMIState.CRITICAL),
            (self.paths.display_severity, hmi_state.value),
            (self.paths.alert_reason, reason_code),
            (self.paths.recommended_action, action_code),
            (self.paths.event_transition, transition.value),
            (self.paths.ai_status, AIStatus.ONLINE.value),
            (self.paths.data_age_ms, data_age_ms),
        ]
        optional = (
            ("driver_state", self.paths.driver_state),
            ("alertness_score", self.paths.alertness_score),
            ("speed_kmh", self.paths.speed),
            ("c3_risk_score", self.paths.final_risk_score),
        )
        for key, path in optional:
            value = evidence.get(key)
            if value is not None:
                values.append((path, value))
        ttc = evidence.get("predicted_ttc_sec")
        if isinstance(ttc, (int, float)) and math.isfinite(float(ttc)):
            values.append((self.paths.min_ttc, float(ttc)))
        return {"signals": [{"path": path, "value": value} for path, value in values]}
