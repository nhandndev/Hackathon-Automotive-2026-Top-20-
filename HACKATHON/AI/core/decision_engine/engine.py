"""Causal, config-driven alert Decision Engine.

The engine consumes synchronized snapshots after Challenge 3. It never writes
BTC prediction columns and performs no network I/O.
"""
from __future__ import annotations

import math
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterable

from .policy import DecisionPolicy
from .schemas import DecisionEvent, DecisionSnapshot, DriverMessage

G_MS2 = 9.81
LEVEL_RANK = {"info": 0, "warning": 1, "critical": 2}


@dataclass(frozen=True)
class _Desired:
    alert_type: str
    severity: str
    audiences: tuple[str, ...]
    confidence: float
    reason: str
    recommended_action: str
    evidence: dict[str, Any]
    driver_message: DriverMessage | None = None


@dataclass
class _Runtime:
    event_id: str | None = None
    episode_index: int = 0
    active_since_ms: int | None = None
    last_emit_ms: int | None = None
    recovery_since_ms: int | None = None
    cooldown_until_ms: int = 0
    desired: _Desired | None = None


@dataclass
class _HarshRuntime:
    candidate_since_ms: int | None = None
    active: bool = False
    normal_since_ms: int | None = None


class DecisionEngine:
    """Stateful safety policy over C1, C2, C3 and telemetry outputs."""

    def __init__(
        self,
        policy: DecisionPolicy,
        model_versions: dict[str, str] | None = None,
    ) -> None:
        self.policy = policy
        self.model_versions = {
            "decision_policy": policy.version,
            **(model_versions or {}),
        }
        self.reset()

    def reset(self) -> None:
        self._trip_id: str | None = None
        self._started_ms: int | None = None
        self._last_timestamp_ms: int | None = None
        self._timers: dict[str, int] = {}
        self._rules: dict[str, _Runtime] = {}
        self._risk_tiers_emitted: set[int] = set()
        self._strong_yawn_latched = False
        self._strong_yawns_ms: deque[int] = deque()
        self._harsh: dict[str, _HarshRuntime] = {
            "brake": _HarshRuntime(),
            "accel": _HarshRuntime(),
            "corner": _HarshRuntime(),
        }
        self._harsh_episodes_ms: deque[int] = deque()

    def update(self, snapshot: DecisionSnapshot) -> list[DecisionEvent]:
        """Consume one timestamp-ordered snapshot and return emitted events."""
        if not self.policy.enabled:
            return []
        self._validate_sequence(snapshot)
        now = snapshot.timestamp_ms
        events: list[DecisionEvent] = []

        self._observe_yawn(snapshot)
        self._observe_harsh(snapshot)
        events.extend(self._risk_tier_events(snapshot))

        driver_valid = self._driver_valid(snapshot)
        compound = bool(
            driver_valid
            and snapshot.driver_state in {"drowsy", "distracted", "microsleep"}
            and math.isfinite(snapshot.predicted_ttc_sec)
            and snapshot.predicted_ttc_sec <= self.policy.ttc.warning_sec
            and snapshot.speed_kmh >= self.policy.general.moving_speed_kmh
        )

        collision = self._collision_desired(snapshot, compound)
        events.extend(self._apply_rule(
            "collision",
            collision,
            self._collision_recovered(snapshot),
            self.policy.ttc.recovery_ms,
            self.policy.ttc.cooldown_ms,
            snapshot,
        ))

        # A compound collision event carries driver evidence and suppresses
        # simultaneous component alerts to avoid double notification.
        microsleep = None if compound else self._microsleep_desired(snapshot)
        distraction = None if compound else self._distraction_desired(snapshot)
        drowsiness = None if compound else self._drowsiness_desired(snapshot)

        events.extend(self._apply_rule(
            "microsleep",
            microsleep,
            True if compound else self._microsleep_recovered(snapshot),
            0 if compound else self.policy.microsleep.recovery_ms,
            self.policy.microsleep.cooldown_ms,
            snapshot,
        ))
        events.extend(self._apply_rule(
            "distraction",
            distraction,
            True if compound else self._distraction_recovered(snapshot),
            0 if compound else self.policy.distraction.recovery_ms,
            self.policy.distraction.cooldown_ms,
            snapshot,
        ))
        events.extend(self._apply_rule(
            "drowsiness",
            drowsiness,
            True if compound else self._drowsiness_recovered(snapshot),
            0 if compound else self.policy.drowsiness.recovery_ms,
            self.policy.drowsiness.cooldown_ms,
            snapshot,
        ))

        events.extend(self._apply_rule(
            "speeding",
            self._speeding_desired(snapshot),
            self._speeding_recovered(snapshot),
            self.policy.speeding.recovery_ms,
            self.policy.speeding.cooldown_ms,
            snapshot,
        ))
        events.extend(self._apply_rule(
            "harsh_behavior",
            self._harsh_desired(snapshot),
            self._harsh_recovered(snapshot),
            0,
            self.policy.harsh_behavior.cooldown_ms,
            snapshot,
        ))
        events.extend(self._apply_rule(
            "sensor_health",
            self._sensor_desired(snapshot),
            self._sensor_recovered(snapshot),
            self.policy.sensor_health.recovery_ms,
            self.policy.sensor_health.cooldown_ms,
            snapshot,
        ))
        return events

    def resolve_all(self, snapshot: DecisionSnapshot) -> list[DecisionEvent]:
        """Resolve all open events at trip end without opening new events."""
        events: list[DecisionEvent] = []
        for runtime in self._rules.values():
            if runtime.event_id and runtime.desired:
                events.append(self._build_event(
                    runtime, runtime.desired, "resolved", snapshot
                ))
                runtime.event_id = None
                runtime.desired = None
        return events

    def _validate_sequence(self, snapshot: DecisionSnapshot) -> None:
        if self._trip_id is None:
            self._trip_id = snapshot.trip_id
            self._started_ms = snapshot.timestamp_ms
        elif snapshot.trip_id != self._trip_id:
            raise ValueError(
                f"DecisionEngine is bound to {self._trip_id}; reset before "
                f"processing {snapshot.trip_id}"
            )
        if (
            self._last_timestamp_ms is not None
            and snapshot.timestamp_ms < self._last_timestamp_ms
        ):
            raise ValueError("Decision snapshots must be timestamp ordered")
        self._last_timestamp_ms = snapshot.timestamp_ms

    def _held(
        self, key: str, condition: bool, now_ms: int, duration_ms: int
    ) -> bool:
        if not condition:
            self._timers.pop(key, None)
            return False
        start = self._timers.setdefault(key, now_ms)
        return now_ms - start >= duration_ms

    def _driver_quality_valid(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            snapshot.driver_quality_status in {"valid", "valid_profile"}
            and snapshot.face_detected
            and snapshot.monitoring_available
        )

    def _driver_valid(self, snapshot: DecisionSnapshot) -> bool:
        startup_ok = bool(
            self._started_ms is not None
            and snapshot.timestamp_ms - self._started_ms
            >= self.policy.general.startup_warmup_ms
        )
        return bool(
            startup_ok
            and self._driver_quality_valid(snapshot)
            and snapshot.driver_confidence
            >= self.policy.general.min_driver_confidence
        )

    def _eyes_reliable(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            self._driver_quality_valid(snapshot)
            and snapshot.left_eye_valid
            and snapshot.right_eye_valid
        )

    def _perclos_ready(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            self._started_ms is not None
            and snapshot.timestamp_ms - self._started_ms
            >= self.policy.general.perclos_warmup_ms
            and snapshot.valid_window_ratio
            >= self.policy.general.min_valid_window_ratio
            and self._eyes_reliable(snapshot)
        )

    def _base_evidence(self, snapshot: DecisionSnapshot) -> dict[str, Any]:
        return {
            "frame_id": snapshot.frame_id,
            "trip_timestamp_ms": snapshot.timestamp_ms,
            "speed_kmh": round(snapshot.speed_kmh, 3),
            "longitudinal_accel": round(snapshot.longitudinal_accel, 4),
            "lateral_accel": round(snapshot.lateral_accel, 4),
            "predicted_ttc_sec": snapshot.predicted_ttc_sec,
            "driver_state": snapshot.driver_state,
            "driver_confidence": round(snapshot.driver_confidence, 4),
            "alertness_score": round(snapshot.alertness_score, 4),
            "perclos_30s": round(snapshot.perclos_30s, 4),
            "continuous_eye_closure_ms": snapshot.continuous_eye_closure_ms,
            "off_road_duration_ms": snapshot.off_road_duration_ms,
            "c3_risk_score": round(snapshot.c3_risk_score, 3),
            "driver_quality_status": snapshot.driver_quality_status,
            "road_quality_status": snapshot.road_quality_status,
        }

    def _collision_desired(
        self, snapshot: DecisionSnapshot, compound: bool
    ) -> _Desired | None:
        policy = self.policy.ttc
        moving = snapshot.speed_kmh >= self.policy.general.moving_speed_kmh
        valid = bool(
            moving
            and snapshot.ttc_confirmed
            and snapshot.road_quality_status == "valid"
            and math.isfinite(snapshot.predicted_ttc_sec)
        )
        ttc = snapshot.predicted_ttc_sec
        warning = self._held(
            "ttc.warning",
            valid and ttc <= policy.warning_sec,
            snapshot.timestamp_ms,
            policy.warning_persistence_ms,
        )
        critical = valid and ttc <= policy.critical_sec
        if compound and valid and ttc <= policy.warning_sec:
            critical = True
        if not critical and not warning:
            return None
        severity = "critical" if critical else "warning"
        reason = (
            f"compound risk: TTC={ttc:.2f}s and driver={snapshot.driver_state}"
            if compound
            else f"confirmed TTC={ttc:.2f}s"
        )
        return _Desired(
            alert_type="collision_risk",
            severity=severity,
            audiences=("driver_display", "fleet_dashboard"),
            confidence=max(0.9, snapshot.driver_confidence if compound else 0.0),
            reason=reason,
            recommended_action="Brake safely and restore a safe following gap",
            driver_message=DriverMessage(
                message_code="COLLISION_CRITICAL" if critical else "COLLISION_WARNING",
                display_text="Collision risk. Brake safely.",
                audible=True,
                ttl_ms=5000,
            ),
            evidence={**self._base_evidence(snapshot), "compound": compound},
        )

    def _collision_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            not math.isfinite(snapshot.predicted_ttc_sec)
            or snapshot.predicted_ttc_sec >= self.policy.ttc.recovery_sec
        )

    def _microsleep_desired(
        self, snapshot: DecisionSnapshot
    ) -> _Desired | None:
        policy = self.policy.microsleep
        reliable = self._eyes_reliable(snapshot)
        moving = snapshot.speed_kmh >= self.policy.general.moving_speed_kmh
        closure = snapshot.continuous_eye_closure_ms
        severity: str | None = None
        audiences: tuple[str, ...] = ()
        confidence = snapshot.driver_confidence
        reason = ""
        if moving and reliable and closure >= policy.reliable_closure_ms:
            severity = "critical"
            audiences = ("driver_display", "fleet_dashboard")
            confidence = max(confidence, 0.95)
            reason = f"reliable continuous eye closure={closure}ms"
        elif (
            not moving
            and reliable
            and closure >= policy.stopped_fleet_closure_ms
        ):
            severity = "warning"
            audiences = ("driver_display", "fleet_dashboard")
            confidence = max(confidence, 0.95)
            reason = f"eye closure while stopped={closure}ms"
        elif (
            not moving
            and reliable
            and closure >= policy.stopped_warning_closure_ms
        ):
            severity = "warning"
            audiences = ("driver_display",)
            confidence = max(confidence, 0.9)
            reason = f"eye closure while stopped={closure}ms"
        else:
            ml_only = self._held(
                "microsleep.ml",
                self._driver_valid(snapshot)
                and snapshot.driver_state == "microsleep"
                and snapshot.driver_confidence >= policy.ml_confidence,
                snapshot.timestamp_ms,
                policy.ml_persistence_ms,
            )
            if ml_only:
                severity = "warning"
                audiences = ("driver_display", "fleet_dashboard")
                reason = "microsleep model persisted without reliable closure"
        if severity is None:
            return None
        return _Desired(
            alert_type="microsleep",
            severity=severity,
            audiences=audiences,
            confidence=confidence,
            reason=reason,
            recommended_action="Stop at a safe location and rest",
            driver_message=DriverMessage(
                message_code="MICROSLEEP",
                display_text="Microsleep risk. Stop safely.",
                audible=True,
                ttl_ms=8000,
            ),
            evidence=self._base_evidence(snapshot),
        )

    def _microsleep_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            self._eyes_reliable(snapshot)
            and snapshot.continuous_eye_closure_ms == 0
            and snapshot.driver_state != "microsleep"
        )

    def _distraction_desired(
        self, snapshot: DecisionSnapshot
    ) -> _Desired | None:
        if not self._driver_valid(snapshot):
            return None
        policy = self.policy.distraction
        speed = snapshot.speed_kmh
        offroad = snapshot.off_road_duration_ms
        threshold: int | None = None
        if speed >= policy.high_speed_kmh:
            threshold = policy.high_speed_duration_ms
        elif speed >= policy.medium_speed_kmh:
            threshold = policy.medium_speed_duration_ms
        if threshold is None or offroad < threshold:
            return None
        critical = offroad >= policy.critical_duration_ms
        return _Desired(
            alert_type="driver_distraction",
            severity="critical" if critical else "warning",
            audiences=("driver_display", "fleet_dashboard"),
            confidence=snapshot.driver_confidence,
            reason=f"off-road head-pose proxy={offroad}ms at {speed:.1f}km/h",
            recommended_action="Return attention to the road",
            driver_message=DriverMessage(
                message_code="DISTRACTION_CRITICAL" if critical else "DISTRACTION_WARNING",
                display_text="Keep your attention on the road.",
                audible=True,
                ttl_ms=6000,
            ),
            evidence=self._base_evidence(snapshot),
        )

    def _distraction_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            self._driver_quality_valid(snapshot)
            and snapshot.off_road_duration_ms == 0
        )

    def _observe_yawn(self, snapshot: DecisionSnapshot) -> None:
        policy = self.policy.drowsiness
        strong = bool(
            snapshot.mouth_state == "yawning"
            and snapshot.mouth_open_duration_ms >= policy.strong_yawn_ms
        )
        if strong and not self._strong_yawn_latched:
            self._strong_yawns_ms.append(snapshot.timestamp_ms)
            self._strong_yawn_latched = True
        elif not strong:
            self._strong_yawn_latched = False
        cutoff = snapshot.timestamp_ms - policy.yawn_window_ms
        while self._strong_yawns_ms and self._strong_yawns_ms[0] < cutoff:
            self._strong_yawns_ms.popleft()

    def _drowsiness_desired(
        self, snapshot: DecisionSnapshot
    ) -> _Desired | None:
        if snapshot.speed_kmh < self.policy.general.driver_warning_min_speed_kmh:
            return None
        policy = self.policy.drowsiness
        perclos_ready = self._perclos_ready(snapshot)
        perclos_warning = self._held(
            "drowsy.perclos.warning",
            perclos_ready and snapshot.perclos_30s >= policy.perclos_warning,
            snapshot.timestamp_ms,
            policy.perclos_persistence_ms,
        )
        perclos_critical = self._held(
            "drowsy.perclos.critical",
            perclos_ready and snapshot.perclos_30s >= policy.perclos_critical,
            snapshot.timestamp_ms,
            policy.perclos_persistence_ms,
        )
        ml_warning = self._held(
            "drowsy.ml.warning",
            self._driver_valid(snapshot)
            and snapshot.driver_state == "drowsy"
            and snapshot.driver_confidence >= policy.warning_confidence
            and snapshot.alertness_score <= policy.warning_alertness_max,
            snapshot.timestamp_ms,
            policy.warning_persistence_ms,
        )
        yawn_warning = bool(
            len(self._strong_yawns_ms) >= policy.yawn_count
            and (
                (perclos_ready and snapshot.perclos_30s >= policy.yawn_perclos_min)
                or snapshot.alertness_score <= policy.yawn_alertness_max
            )
        )
        warning = perclos_warning or ml_warning or yawn_warning
        warning_long = self._held(
            "drowsy.warning.long",
            warning,
            snapshot.timestamp_ms,
            policy.critical_warning_persistence_ms,
        )
        if not warning and not perclos_critical:
            return None
        critical = perclos_critical or warning_long
        if perclos_critical:
            reason = f"PERCLOS={snapshot.perclos_30s:.3f}"
        elif perclos_warning:
            reason = f"PERCLOS={snapshot.perclos_30s:.3f}"
        elif ml_warning:
            reason = (
                f"drowsy confidence={snapshot.driver_confidence:.2f}, "
                f"alertness={snapshot.alertness_score:.2f}"
            )
        else:
            reason = f"repeated strong yawns={len(self._strong_yawns_ms)}"
        return _Desired(
            alert_type="driver_drowsiness",
            severity="critical" if critical else "warning",
            audiences=("driver_display", "fleet_dashboard"),
            confidence=max(snapshot.driver_confidence, 0.8 if perclos_warning else 0.0),
            reason=reason,
            recommended_action="Plan a safe rest stop",
            driver_message=DriverMessage(
                message_code="DROWSINESS_CRITICAL" if critical else "DROWSINESS_WARNING",
                display_text="Fatigue risk detected. Rest safely.",
                audible=True,
                ttl_ms=8000,
            ),
            evidence={
                **self._base_evidence(snapshot),
                "strong_yawns_60s": len(self._strong_yawns_ms),
            },
        )

    def _drowsiness_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            self._driver_valid(snapshot)
            and snapshot.driver_state == "alert"
            and snapshot.alertness_score
            >= self.policy.drowsiness.recovery_alertness_min
            and snapshot.perclos_30s < self.policy.drowsiness.recovery_perclos_max
        )

    def _speeding_desired(self, snapshot: DecisionSnapshot) -> _Desired | None:
        policy = self.policy.speeding
        over = snapshot.speed_kmh - snapshot.speed_limit_kmh
        critical = self._held(
            "speeding.critical",
            over > policy.critical_over_limit_kmh,
            snapshot.timestamp_ms,
            policy.critical_persistence_ms,
        )
        warning = self._held(
            "speeding.warning",
            over > policy.warning_over_limit_kmh,
            snapshot.timestamp_ms,
            policy.warning_persistence_ms,
        )
        if not critical and not warning:
            return None
        return _Desired(
            alert_type="speeding",
            severity="critical" if critical else "warning",
            audiences=("driver_display", "fleet_dashboard"),
            confidence=1.0,
            reason=f"speed is {over:.1f}km/h over limit",
            recommended_action="Reduce speed to the posted limit",
            driver_message=DriverMessage(
                message_code="SEVERE_SPEEDING" if critical else "SPEEDING",
                display_text="Reduce speed.",
                audible=critical,
                ttl_ms=6000,
            ),
            evidence=self._base_evidence(snapshot),
        )

    def _speeding_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            snapshot.speed_kmh - snapshot.speed_limit_kmh
            <= self.policy.speeding.recovery_over_limit_kmh
        )

    def _observe_harsh(self, snapshot: DecisionSnapshot) -> None:
        policy = self.policy.harsh_behavior
        conditions = {
            "brake": snapshot.longitudinal_accel < -policy.brake_g * G_MS2,
            "accel": snapshot.longitudinal_accel > policy.accel_g * G_MS2,
            "corner": abs(snapshot.lateral_accel) > policy.corner_g * G_MS2,
        }
        # A brake inside an active TTC danger window is evidence for the
        # collision episode, not a separate harsh-behavior episode.
        if (
            conditions["brake"]
            and math.isfinite(snapshot.predicted_ttc_sec)
            and snapshot.predicted_ttc_sec <= self.policy.ttc.warning_sec
        ):
            conditions["brake"] = False
        for name, condition in conditions.items():
            runtime = self._harsh[name]
            if condition:
                runtime.normal_since_ms = None
                if runtime.candidate_since_ms is None:
                    runtime.candidate_since_ms = snapshot.timestamp_ms
                if (
                    not runtime.active
                    and snapshot.timestamp_ms - runtime.candidate_since_ms
                    >= policy.episode_confirm_ms
                ):
                    runtime.active = True
                    self._harsh_episodes_ms.append(snapshot.timestamp_ms)
            else:
                runtime.candidate_since_ms = None
                if runtime.active:
                    if runtime.normal_since_ms is None:
                        runtime.normal_since_ms = snapshot.timestamp_ms
                    if (
                        snapshot.timestamp_ms - runtime.normal_since_ms
                        >= policy.episode_end_ms
                    ):
                        runtime.active = False
                        runtime.normal_since_ms = None
        cutoff = snapshot.timestamp_ms - policy.warning_window_ms
        while self._harsh_episodes_ms and self._harsh_episodes_ms[0] < cutoff:
            self._harsh_episodes_ms.popleft()

    def _harsh_desired(self, snapshot: DecisionSnapshot) -> _Desired | None:
        if len(self._harsh_episodes_ms) < self.policy.harsh_behavior.warning_count:
            return None
        return _Desired(
            alert_type="repeated_harsh_behavior",
            severity="warning",
            audiences=("fleet_dashboard",),
            confidence=1.0,
            reason=f"harsh episodes in 60s={len(self._harsh_episodes_ms)}",
            recommended_action="Review repeated harsh vehicle control",
            evidence={
                **self._base_evidence(snapshot),
                "harsh_episodes_60s": len(self._harsh_episodes_ms),
            },
        )

    def _harsh_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return len(self._harsh_episodes_ms) < self.policy.harsh_behavior.warning_count

    def _sensor_desired(self, snapshot: DecisionSnapshot) -> _Desired | None:
        policy = self.policy.sensor_health
        moving = snapshot.speed_kmh >= self.policy.general.moving_speed_kmh
        startup_complete = bool(
            self._started_ms is not None
            and snapshot.timestamp_ms - self._started_ms
            >= self.policy.general.startup_warmup_ms
        )
        driver_bad = startup_complete and not self._driver_quality_valid(snapshot)
        road_bad = snapshot.road_quality_status != "valid"
        degraded = moving and (driver_bad or road_bad)
        carsky = self._held(
            "sensor.carsky", degraded, snapshot.timestamp_ms, policy.carsky_after_ms
        )
        fleet = self._held(
            "sensor.fleet", degraded, snapshot.timestamp_ms, policy.fleet_after_ms
        )
        if not carsky and not fleet:
            return None
        failed = [
            name for name, bad in (("driver", driver_bad), ("road", road_bad)) if bad
        ]
        return _Desired(
            alert_type="system_health",
            severity="warning",
            audiences=("driver_display", "fleet_dashboard") if fleet else ("driver_display",),
            confidence=1.0,
            reason=f"degraded signal: {','.join(failed)}",
            recommended_action="Inspect or clean the affected camera",
            driver_message=DriverMessage(
                message_code="CAMERA_DEGRADED",
                display_text="Camera blocked or unavailable.",
                audible=False,
                ttl_ms=8000,
            ),
            evidence=self._base_evidence(snapshot),
        )

    def _sensor_recovered(self, snapshot: DecisionSnapshot) -> bool:
        return bool(
            self._driver_quality_valid(snapshot)
            and snapshot.road_quality_status == "valid"
        )

    def _risk_tier_events(
        self, snapshot: DecisionSnapshot
    ) -> list[DecisionEvent]:
        events: list[DecisionEvent] = []
        for index, threshold in enumerate(
            self.policy.risk_tiers.thresholds, start=1
        ):
            if index in self._risk_tiers_emitted:
                continue
            if snapshot.c3_risk_score < threshold:
                continue
            self._risk_tiers_emitted.add(index)
            desired = _Desired(
                alert_type=f"fleet_risk_tier_{index}",
                severity="info" if index == 1 else "warning",
                audiences=("fleet_dashboard",),
                confidence=1.0,
                reason=f"C3 risk crossed {threshold:.0f}",
                recommended_action="Review the trip risk timeline",
                evidence=self._base_evidence(snapshot),
            )
            runtime = _Runtime(
                event_id=str(uuid.uuid4()),
                episode_index=1,
                active_since_ms=snapshot.timestamp_ms,
                desired=desired,
            )
            events.append(self._build_event(runtime, desired, "open", snapshot))
        return events

    def _apply_rule(
        self,
        key: str,
        desired: _Desired | None,
        recovery_ready: bool,
        recovery_ms: int,
        cooldown_ms: int,
        snapshot: DecisionSnapshot,
    ) -> list[DecisionEvent]:
        runtime = self._rules.setdefault(key, _Runtime())
        now = snapshot.timestamp_ms
        if runtime.event_id is None:
            runtime.recovery_since_ms = None
            if desired is None:
                return []
            if now < runtime.cooldown_until_ms and desired.severity != "critical":
                return []
            runtime.episode_index += 1
            runtime.event_id = str(uuid.uuid4())
            runtime.active_since_ms = now
            runtime.last_emit_ms = now
            runtime.desired = desired
            return [self._build_event(runtime, desired, "open", snapshot)]

        if desired is not None:
            runtime.recovery_since_ms = None
            previous = runtime.desired or desired
            severity = (
                desired.severity
                if LEVEL_RANK[desired.severity] >= LEVEL_RANK[previous.severity]
                else previous.severity
            )
            audiences = tuple(dict.fromkeys((*previous.audiences, *desired.audiences)))
            merged = _Desired(
                alert_type=previous.alert_type,
                severity=severity,
                audiences=audiences,
                confidence=max(previous.confidence, desired.confidence),
                reason=desired.reason,
                recommended_action=desired.recommended_action,
                evidence=desired.evidence,
                driver_message=desired.driver_message or previous.driver_message,
            )
            escalated = LEVEL_RANK[merged.severity] > LEVEL_RANK[previous.severity]
            audience_changed = merged.audiences != previous.audiences
            action_changed = (
                merged.recommended_action != previous.recommended_action
            )
            previous_code = (
                previous.driver_message.message_code
                if previous.driver_message is not None else None
            )
            merged_code = (
                merged.driver_message.message_code
                if merged.driver_message is not None else None
            )
            message_changed = merged_code != previous_code
            runtime.desired = merged
            # Snapshot/media endpoints already carry continuous evidence.
            # DecisionEvent is an episode transition, not a heartbeat: emit
            # only when the operator-facing meaning materially changes.
            if escalated or audience_changed or action_changed or message_changed:
                runtime.last_emit_ms = now
                return [self._build_event(runtime, merged, "update", snapshot)]
            return []

        if not recovery_ready:
            runtime.recovery_since_ms = None
            return []
        if runtime.recovery_since_ms is None:
            runtime.recovery_since_ms = now
        if now - runtime.recovery_since_ms < recovery_ms:
            return []
        previous = runtime.desired
        if previous is None:
            return []
        event = self._build_event(runtime, previous, "resolved", snapshot)
        runtime.event_id = None
        runtime.active_since_ms = None
        runtime.last_emit_ms = now
        runtime.recovery_since_ms = None
        runtime.cooldown_until_ms = now + cooldown_ms
        runtime.desired = None
        return [event]

    def _build_event(
        self,
        runtime: _Runtime,
        desired: _Desired,
        status: str,
        snapshot: DecisionSnapshot,
    ) -> DecisionEvent:
        assert runtime.event_id is not None
        return DecisionEvent(
            event_id=runtime.event_id,
            idempotency_key=(
                f"{snapshot.trip_id}:{desired.alert_type}:"
                f"{runtime.episode_index}:{status}:{snapshot.timestamp_ms}"
            ),
            trip_id=snapshot.trip_id,
            driver_id=snapshot.driver_id,
            frame_id=snapshot.frame_id,
            trip_timestamp_ms=snapshot.timestamp_ms,
            status=status,
            alert_type=desired.alert_type,
            severity=desired.severity,
            confidence=desired.confidence,
            audiences=list(desired.audiences),
            driver_message=(
                desired.driver_message
                if "driver_display" in desired.audiences
                else None
            ),
            evidence={**desired.evidence, "reason": desired.reason},
            recommended_action=desired.recommended_action,
            model_versions=self.model_versions,
        )

    def open_alert_types(self) -> Iterable[str]:
        return tuple(
            runtime.desired.alert_type
            for runtime in self._rules.values()
            if runtime.event_id and runtime.desired
        )
