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
    speed_mux: str = "Vehicle.Speed"

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

        payload = {
            "driver_state": frame.driver.state.value,
            "alertness_score": frame.driver.alertness_score,
            "speed_kmh": frame.ego.speed_kmh,
            "speed_limit_kmh": metadata.speed_limit_kmh,
            "predicted_ttc_sec": frame.min_ttc if math.isfinite(frame.min_ttc) else None,
            "risk_score": frame.risk.final_risk_score,
            "severity": severity.value,
            "critical_alert": severity is CarSkyHMIState.CRITICAL,
            "recommended_action": action_code,
            "ai_status": ai_status.value,
        }
        return self.map_live_snapshot(payload, data_age_ms=data_age_ms)

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

        payload = {
            "driver_state": evidence.get("driver_state"),
            "alertness_score": evidence.get("alertness_score"),
            "speed_kmh": evidence.get("speed_kmh"),
            "predicted_ttc_sec": evidence.get("predicted_ttc_sec"),
            "risk_score": evidence.get("c3_risk_score"),
            "severity": hmi_state.value,
            "critical_alert": hmi_state is CarSkyHMIState.CRITICAL,
            "recommended_action": action_code,
            "ai_status": AIStatus.ONLINE.value,
        }
        return self.map_live_snapshot(payload, data_age_ms=data_age_ms, transition=transition.value)

    def map_live_snapshot(
        self,
        snapshot: Mapping[str, Any],
        *,
        data_age_ms: int = 0,
        transition: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Map live dashboard telemetry to the BTC-compatible speed-mux VHAL path.

        Current CarSky/AAOS only accepts standard Vehicle.Speed. The APK V2.2
        decodes decimal groups 41..49 from this one property.
        """
        if data_age_ms < 0:
            raise ValueError("data_age_ms must not be negative")

        risk = self._number(snapshot.get("risk_score"), None)
        ttc = self._number(snapshot.get("predicted_ttc_sec"), None)
        driver_state = str(snapshot.get("driver_state") or "alert").lower()
        alertness = self._number(snapshot.get("alertness_score"), None)
        speed = self._number(snapshot.get("speed_kmh"), None)

        severity = str(snapshot.get("severity") or "").upper()
        if severity not in {"SAFE", "WARNING", "CRITICAL", "RECOVERY"}:
            severity = self._derive_severity(risk or 0.0, ttc, driver_state)

        action = str(snapshot.get("recommended_action") or "")
        if action not in {"NONE", "FOCUS_FORWARD", "TAKE_BREAK", "BRAKE_SAFE", "REDUCE_SPEED"}:
            action = self._derive_action(snapshot, ttc, driver_state, severity)

        values: list[float] = [
            self._mux(42, self._severity_code(severity)),
            self._mux(43, self._driver_state_code(driver_state)),
            self._mux(46, 1 if severity == "CRITICAL" or bool(snapshot.get("critical_alert")) else 0),
            self._mux(47, self._ai_status_code(str(snapshot.get("ai_status") or "ONLINE"))),
            self._mux(48, self._action_code(action)),
        ]
        if risk is not None and math.isfinite(risk):
            values.insert(0, self._mux(41, risk))
        if alertness is not None and math.isfinite(alertness):
            values.append(self._mux(44, self._scale(alertness, 100)))
        if ttc is not None and math.isfinite(ttc):
            values.append(self._mux(45, self._scale(ttc, 10)))
        if speed is not None and math.isfinite(speed):
            values.append(self._mux(49, speed))

        signals = [{"path": self.paths.speed_mux, "value": value} for value in values]
        return {
            "transport": "vehicle-speed-mux",
            "transition": transition,
            "signals": signals,
        }

    @staticmethod
    def _number(value: Any, default: float | None) -> float | None:
        if value is None:
            return default
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return parsed if math.isfinite(parsed) else default

    @staticmethod
    def _scale(value: float | None, scale: float) -> float:
        if value is None:
            return 0.0
        return value * scale

    @staticmethod
    def _mux(group: int, payload: float) -> float:
        clamped = max(0.0, min(999.0, float(payload)))
        return group + (clamped / 1000.0)

    @staticmethod
    def _derive_severity(risk: float, ttc: float | None, driver_state: str) -> str:
        if risk >= 75 or (ttc is not None and ttc <= 1.5) or driver_state == "microsleep":
            return "CRITICAL"
        if risk >= 40 or (ttc is not None and ttc <= 3.0) or driver_state in {"drowsy", "yawning", "distracted"}:
            return "WARNING"
        return "SAFE"

    @staticmethod
    def _derive_action(snapshot: Mapping[str, Any], ttc: float | None, driver_state: str, severity: str) -> str:
        if ttc is not None and ttc <= 1.5:
            return "BRAKE_SAFE"
        if driver_state in {"microsleep", "drowsy", "yawning"}:
            return "TAKE_BREAK"
        if driver_state == "distracted":
            return "FOCUS_FORWARD"
        if bool(snapshot.get("speeding")):
            return "REDUCE_SPEED"
        return "BRAKE_SAFE" if severity == "CRITICAL" else "NONE"

    @staticmethod
    def _severity_code(severity: str) -> int:
        return {"SAFE": 0, "WARNING": 1, "CRITICAL": 2, "RECOVERY": 3}.get(severity.upper(), 0)

    @staticmethod
    def _driver_state_code(driver_state: str) -> int:
        return {
            "alert": 0,
            "normal": 0,
            "drowsy": 1,
            "yawning": 2,
            "distracted": 3,
            "microsleep": 4,
        }.get(driver_state.lower(), 0)

    @staticmethod
    def _ai_status_code(status: str) -> int:
        return {"ONLINE": 0, "DEGRADED": 1, "OFFLINE": 2}.get(status.upper(), 0)

    @staticmethod
    def _action_code(action: str) -> int:
        return {
            "NONE": 0,
            "FOCUS_FORWARD": 1,
            "TAKE_BREAK": 2,
            "BRAKE_SAFE": 3,
            "REDUCE_SPEED": 4,
        }.get(action.upper(), 0)
