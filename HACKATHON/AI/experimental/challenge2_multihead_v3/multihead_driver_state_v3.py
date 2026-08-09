from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Deque, Mapping


STATES = {"alert", "drowsy", "yawning", "distracted", "microsleep"}
HEADS = ("microsleep", "yawning", "distracted", "drowsy")


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clip01(value: float) -> float:
    return clip(value, 0.0, 1.0)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def angle_diff(current_deg: float, neutral_deg: float) -> float:
    """Smallest signed difference in degrees."""
    return (current_deg - neutral_deg + 180.0) % 360.0 - 180.0


def duration_score(duration_sec: float, start_sec: float, full_sec: float) -> float:
    if full_sec <= start_sec:
        return 1.0 if duration_sec >= full_sec else 0.0
    if duration_sec <= start_sec:
        return 0.0
    if duration_sec >= full_sec:
        return 1.0
    return (duration_sec - start_sec) / (full_sec - start_sec)


def frames_from_seconds(seconds: float, fps: float) -> int:
    return max(1, int(round(seconds * fps)))


@dataclass(slots=True)
class DriverProfile:
    driver_id: str = "default"
    ear_open: float = 0.3225
    ear_closed: float = 0.2170
    mar_neutral: float = 0.2010
    mar_yawn: float = 0.6500
    neutral_yaw_deg: float = 0.0
    neutral_pitch_deg: float = 0.0
    neutral_roll_deg: float = 0.0
    eye_closure_threshold: float = 0.72
    quality_score: float = 0.85

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "DriverProfile":
        if not data:
            return cls()
        allowed = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        payload = {key: value for key, value in data.items() if key in allowed}
        return cls(**payload)


@dataclass(slots=True)
class RawDriverFeatures:
    frame_id: int
    timestamp_sec: float
    ear: float | None = None
    mar: float | None = None
    yaw_deg: float | None = None
    pitch_deg: float | None = None
    roll_deg: float | None = None
    eye_quality: float = 1.0
    mouth_quality: float = 1.0
    head_quality: float = 1.0
    hand_visible: bool = False
    hand_quality: float = 1.0
    phone_detected: bool = False
    speed_kmh: float = 0.0
    longitudinal_accel: float = 0.0
    lateral_accel: float = 0.0

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RawDriverFeatures":
        return cls(
            frame_id=int(data.get("frame_id", 0)),
            timestamp_sec=safe_float(data.get("timestamp_sec", data.get("timestamp", 0.0))),
            ear=None if data.get("ear") is None else safe_float(data.get("ear")),
            mar=None if data.get("mar") is None else safe_float(data.get("mar")),
            yaw_deg=None if data.get("yaw_deg") is None else safe_float(data.get("yaw_deg")),
            pitch_deg=None if data.get("pitch_deg") is None else safe_float(data.get("pitch_deg")),
            roll_deg=None if data.get("roll_deg") is None else safe_float(data.get("roll_deg")),
            eye_quality=clip01(safe_float(data.get("eye_quality", 1.0), 1.0)),
            mouth_quality=clip01(safe_float(data.get("mouth_quality", 1.0), 1.0)),
            head_quality=clip01(safe_float(data.get("head_quality", 1.0), 1.0)),
            hand_visible=bool(data.get("hand_visible", False)),
            hand_quality=clip01(safe_float(data.get("hand_quality", 1.0), 1.0)),
            phone_detected=bool(data.get("phone_detected", False)),
            speed_kmh=safe_float(data.get("speed_kmh", 0.0)),
            longitudinal_accel=safe_float(data.get("longitudinal_accel", 0.0)),
            lateral_accel=safe_float(data.get("lateral_accel", 0.0)),
        )


@dataclass(slots=True)
class PersonalizedFeatures:
    raw: RawDriverFeatures
    profile: DriverProfile
    ear_threshold: float
    mar_open_threshold: float
    eye_openness_norm: float
    mouth_open_norm: float
    eye_closed: bool
    mouth_open: bool
    yaw_relative: float
    pitch_relative: float
    roll_relative: float
    head_zone: str
    offroad_now: bool


@dataclass(slots=True)
class TemporalFeatures:
    continuous_eye_closure_sec: float
    continuous_mouth_open_sec: float
    continuous_offroad_sec: float
    continuous_hand_visible_sec: float
    PERCLOS_5s: float
    blink_duration_mean_5s: float
    eye_openness_mean_5s: float
    eye_openness_std_5s: float
    blink_rate_10s: float
    long_closure_count_10s: float

    def as_dict(self) -> dict[str, float]:
        return {
            "continuous_eye_closure_sec": self.continuous_eye_closure_sec,
            "continuous_mouth_open_sec": self.continuous_mouth_open_sec,
            "continuous_offroad_sec": self.continuous_offroad_sec,
            "continuous_hand_visible_sec": self.continuous_hand_visible_sec,
            "PERCLOS_5s": self.PERCLOS_5s,
            "blink_duration_mean_5s": self.blink_duration_mean_5s,
            "eye_openness_mean_5s": self.eye_openness_mean_5s,
            "eye_openness_std_5s": self.eye_openness_std_5s,
            "blink_rate_10s": self.blink_rate_10s,
            "long_closure_count_10s": self.long_closure_count_10s,
        }


@dataclass(slots=True)
class HeadOutput:
    name: str
    score: float
    quality: float
    active: bool = False
    debug: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MultiHeadOutput:
    state: str
    confidence: float
    source_head: str
    head_scores: dict[str, float]
    heads: dict[str, HeadOutput]
    temporal: TemporalFeatures
    debug: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "confidence": self.confidence,
            "source_head": self.source_head,
            "head_scores": self.head_scores,
            "temporal": self.temporal.as_dict(),
            "heads": {
                name: {
                    "score": head.score,
                    "quality": head.quality,
                    "active": head.active,
                    "debug": head.debug,
                }
                for name, head in self.heads.items()
            },
            "debug": self.debug,
        }


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).with_name("multihead_config.yaml")
    path = Path(path)
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency exists in product env
        raise RuntimeError("PyYAML is required to read multihead_config.yaml") from exc
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


class PersonalizationLayer:
    def __init__(self, config: Mapping[str, Any]):
        self.config = config
        self.default_profile = DriverProfile.from_mapping(config.get("default_profile"))
        distracted = config.get("distracted", {})
        self.yaw_threshold_deg = safe_float(distracted.get("yaw_threshold_deg", 18.0), 18.0)
        self.pitch_threshold_deg = safe_float(distracted.get("pitch_threshold_deg", 16.0), 16.0)
        self.mouth_open_norm_threshold = safe_float(
            config.get("yawning", {}).get("mouth_open_norm_threshold", 0.65), 0.65
        )

    def _blend(self, personal: float, default: float, quality: float) -> float:
        quality = clip01(quality)
        return quality * personal + (1.0 - quality) * default

    def transform(
        self, raw: RawDriverFeatures, profile: DriverProfile | Mapping[str, Any] | None = None
    ) -> PersonalizedFeatures:
        profile = profile if isinstance(profile, DriverProfile) else DriverProfile.from_mapping(profile)
        quality = clip01(profile.quality_score)
        default = self.default_profile

        ear_open = self._blend(profile.ear_open, default.ear_open, quality)
        ear_closed = self._blend(profile.ear_closed, default.ear_closed, quality)
        mar_neutral = self._blend(profile.mar_neutral, default.mar_neutral, quality)
        mar_yawn = self._blend(profile.mar_yawn, default.mar_yawn, quality)

        ear = raw.ear if raw.ear is not None else ear_open
        mar = raw.mar if raw.mar is not None else mar_neutral

        ear_range = max(1e-6, ear_open - ear_closed)
        mar_range = max(1e-6, mar_yawn - mar_neutral)
        eye_openness_norm = clip01((ear - ear_closed) / ear_range)
        mouth_open_norm = clip01((mar - mar_neutral) / mar_range)

        ear_threshold = ear_open * profile.eye_closure_threshold
        mar_open_threshold = mar_neutral + self.mouth_open_norm_threshold * mar_range

        yaw = raw.yaw_deg if raw.yaw_deg is not None else profile.neutral_yaw_deg
        pitch = raw.pitch_deg if raw.pitch_deg is not None else profile.neutral_pitch_deg
        roll = raw.roll_deg if raw.roll_deg is not None else profile.neutral_roll_deg
        yaw_relative = yaw - profile.neutral_yaw_deg
        pitch_relative = angle_diff(pitch, profile.neutral_pitch_deg)
        roll_relative = angle_diff(roll, profile.neutral_roll_deg)

        if abs(yaw_relative) <= self.yaw_threshold_deg and abs(pitch_relative) <= self.pitch_threshold_deg:
            head_zone = "forward"
        elif yaw_relative < -self.yaw_threshold_deg:
            head_zone = "left"
        elif yaw_relative > self.yaw_threshold_deg:
            head_zone = "right"
        elif pitch_relative > self.pitch_threshold_deg:
            head_zone = "down"
        else:
            head_zone = "up"

        return PersonalizedFeatures(
            raw=raw,
            profile=profile,
            ear_threshold=ear_threshold,
            mar_open_threshold=mar_open_threshold,
            eye_openness_norm=eye_openness_norm,
            mouth_open_norm=mouth_open_norm,
            eye_closed=ear <= ear_threshold,
            mouth_open=mar >= mar_open_threshold,
            yaw_relative=yaw_relative,
            pitch_relative=pitch_relative,
            roll_relative=roll_relative,
            head_zone=head_zone,
            offroad_now=head_zone != "forward",
        )


class TemporalFeatureEngine:
    def __init__(self, config: Mapping[str, Any]):
        self.fps = safe_float(config.get("fps", 20.0), 20.0)
        self.long_closure_sec = safe_float(config.get("drowsy", {}).get("long_closure_sec", 0.50), 0.50)
        self.eye_closure_frames = 0
        self.mouth_open_frames = 0
        self.offroad_frames = 0
        self.hand_visible_frames = 0
        self._eye_window: Deque[tuple[float, bool, float]] = deque()
        self._blink_events: Deque[tuple[float, float]] = deque()
        self._long_closure_events: Deque[tuple[float, float]] = deque()
        self._closure_start_ts: float | None = None
        self._previous_eye_closed = False

    def reset(self) -> None:
        self.__init__({"fps": self.fps, "drowsy": {"long_closure_sec": self.long_closure_sec}})

    def _trim(self, now: float) -> None:
        while self._eye_window and now - self._eye_window[0][0] > 10.0:
            self._eye_window.popleft()
        while self._blink_events and now - self._blink_events[0][0] > 10.0:
            self._blink_events.popleft()
        while self._long_closure_events and now - self._long_closure_events[0][0] > 10.0:
            self._long_closure_events.popleft()

    def update(self, features: PersonalizedFeatures) -> TemporalFeatures:
        raw = features.raw
        now = raw.timestamp_sec

        self.eye_closure_frames = self.eye_closure_frames + 1 if features.eye_closed else 0
        self.mouth_open_frames = self.mouth_open_frames + 1 if features.mouth_open else 0
        self.offroad_frames = self.offroad_frames + 1 if features.offroad_now else 0
        self.hand_visible_frames = self.hand_visible_frames + 1 if raw.hand_visible else 0

        if features.eye_closed and not self._previous_eye_closed:
            self._closure_start_ts = now
        if not features.eye_closed and self._previous_eye_closed and self._closure_start_ts is not None:
            duration = max(0.0, now - self._closure_start_ts)
            if 0.05 <= duration <= 1.00:
                self._blink_events.append((now, duration))
            if duration >= self.long_closure_sec:
                self._long_closure_events.append((now, duration))
            self._closure_start_ts = None
        self._previous_eye_closed = features.eye_closed

        self._eye_window.append((now, features.eye_closed, features.eye_openness_norm))
        self._trim(now)

        eye_5s = [row for row in self._eye_window if now - row[0] <= 5.0]
        closed_5s = sum(1 for _, closed, _ in eye_5s if closed)
        openness_5s = [openness for _, _, openness in eye_5s]
        blink_5s = [duration for ts, duration in self._blink_events if now - ts <= 5.0]
        blink_10s = [duration for ts, duration in self._blink_events if now - ts <= 10.0]
        long_10s = [duration for ts, duration in self._long_closure_events if now - ts <= 10.0]

        return TemporalFeatures(
            continuous_eye_closure_sec=self.eye_closure_frames / self.fps,
            continuous_mouth_open_sec=self.mouth_open_frames / self.fps,
            continuous_offroad_sec=self.offroad_frames / self.fps,
            continuous_hand_visible_sec=self.hand_visible_frames / self.fps,
            PERCLOS_5s=(closed_5s / len(eye_5s)) if eye_5s else 0.0,
            blink_duration_mean_5s=mean(blink_5s) if blink_5s else 0.0,
            eye_openness_mean_5s=mean(openness_5s) if openness_5s else 1.0,
            eye_openness_std_5s=pstdev(openness_5s) if len(openness_5s) > 1 else 0.0,
            blink_rate_10s=len(blink_10s) / 10.0,
            long_closure_count_10s=float(len(long_10s)),
        )


class MicrosleepHead:
    def __init__(self, config: Mapping[str, Any]):
        self.config = config.get("microsleep", {})

    def predict(self, features: PersonalizedFeatures, temporal: TemporalFeatures) -> HeadOutput:
        score = 0.0
        if features.eye_closed:
            score = duration_score(
                temporal.continuous_eye_closure_sec,
                safe_float(self.config.get("start_sec", 0.35), 0.35),
                safe_float(self.config.get("full_sec", 1.20), 1.20),
            )
        quality = clip01(features.raw.eye_quality * features.profile.quality_score)
        return HeadOutput(
            name="microsleep",
            score=clip01(score * quality),
            quality=quality,
            debug={
                "ear": features.raw.ear,
                "ear_threshold": features.ear_threshold,
                "eye_closed": features.eye_closed,
                "continuous_eye_closure_sec": temporal.continuous_eye_closure_sec,
            },
        )


class YawningHead:
    def __init__(self, config: Mapping[str, Any]):
        self.config = config.get("yawning", {})

    def predict(self, features: PersonalizedFeatures, temporal: TemporalFeatures) -> HeadOutput:
        score = 0.0
        if features.mouth_open:
            score = duration_score(
                temporal.continuous_mouth_open_sec,
                safe_float(self.config.get("start_sec", 0.60), 0.60),
                safe_float(self.config.get("full_sec", 1.80), 1.80),
            )
        quality = clip01(features.raw.mouth_quality * features.profile.quality_score)
        return HeadOutput(
            name="yawning",
            score=clip01(score * quality),
            quality=quality,
            debug={
                "mar": features.raw.mar,
                "mar_open_threshold": features.mar_open_threshold,
                "mouth_open": features.mouth_open,
                "mouth_open_norm": features.mouth_open_norm,
                "continuous_mouth_open_sec": temporal.continuous_mouth_open_sec,
            },
        )


class DistractedHead:
    def __init__(self, config: Mapping[str, Any]):
        self.config = config.get("distracted", {})

    def predict(self, features: PersonalizedFeatures, temporal: TemporalFeatures) -> HeadOutput:
        raw = features.raw
        visual_duration = duration_score(
            temporal.continuous_offroad_sec,
            safe_float(self.config.get("offroad_start_sec", 0.45), 0.45),
            safe_float(self.config.get("offroad_full_sec", 1.60), 1.60),
        )
        head_quality = clip01(raw.head_quality * features.profile.quality_score)
        visual_score = visual_duration * head_quality

        side_glance = features.head_zone in {"left", "right"}
        lateral_motion = abs(raw.lateral_accel) >= safe_float(
            self.config.get("lateral_accel_threshold", 0.45), 0.45
        )
        if side_glance and lateral_motion:
            visual_score *= safe_float(self.config.get("lateral_context_discount", 0.80), 0.80)

        hand_duration = duration_score(
            temporal.continuous_hand_visible_sec,
            safe_float(self.config.get("hand_start_sec", 0.50), 0.50),
            safe_float(self.config.get("hand_full_sec", 3.00), 3.00),
        )
        hand_quality = clip01(raw.hand_quality)
        hand_score = hand_duration * hand_quality

        score = (
            safe_float(self.config.get("visual_weight", 0.65), 0.65) * visual_score
            + safe_float(self.config.get("hand_weight", 0.35), 0.35) * hand_score
        )
        if raw.phone_detected:
            score += safe_float(self.config.get("phone_bonus", 0.30), 0.30)
        if features.head_zone == "down" and temporal.continuous_offroad_sec >= safe_float(
            self.config.get("down_sec", 1.20), 1.20
        ):
            score += safe_float(self.config.get("down_bonus", 0.15), 0.15)

        quality = max(head_quality, hand_quality if raw.hand_visible else 0.0)
        return HeadOutput(
            name="distracted",
            score=clip01(score),
            quality=clip01(quality),
            debug={
                "head_zone": features.head_zone,
                "yaw_relative": features.yaw_relative,
                "pitch_relative": features.pitch_relative,
                "continuous_offroad_sec": temporal.continuous_offroad_sec,
                "visual_score": clip01(visual_score),
                "hand_visible": raw.hand_visible,
                "continuous_hand_visible_sec": temporal.continuous_hand_visible_sec,
                "hand_score": clip01(hand_score),
                "phone_detected": raw.phone_detected,
                "speed_kmh": raw.speed_kmh,
                "lateral_accel": raw.lateral_accel,
            },
        )


class DrowsyHead:
    def __init__(self, config: Mapping[str, Any], model_path: str | Path | None = None):
        self.config = config.get("drowsy", {})
        self.feature_names = list(
            self.config.get(
                "features",
                [
                    "PERCLOS_5s",
                    "blink_duration_mean_5s",
                    "eye_openness_mean_5s",
                    "eye_openness_std_5s",
                    "blink_rate_10s",
                    "long_closure_count_10s",
                ],
            )
        )
        self.model_path = Path(model_path or self.config.get("model_path") or "") if (model_path or self.config.get("model_path")) else None
        self.model: Any | None = None
        if self.model_path:
            self._load_model(self.model_path)

    def _load_model(self, model_path: Path) -> None:
        import joblib

        artifact = joblib.load(model_path)
        self.model = artifact.get("model", artifact) if isinstance(artifact, dict) else artifact

    def predict(self, _features: PersonalizedFeatures, temporal: TemporalFeatures) -> HeadOutput:
        if self.model is None:
            return HeadOutput(
                name="drowsy",
                score=0.0,
                quality=0.0,
                debug={"model_loaded": False, "reason": "binary RF drowsy model not configured"},
            )

        values = temporal.as_dict()
        vector = [[safe_float(values.get(name, 0.0)) for name in self.feature_names]]
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(vector)[0]
            classes = list(getattr(self.model, "classes_", []))
            if "drowsy" in classes:
                score = float(probs[classes.index("drowsy")])
            elif 1 in classes:
                score = float(probs[classes.index(1)])
            else:
                score = float(probs[-1])
        else:
            score = float(self.model.predict(vector)[0])

        return HeadOutput(
            name="drowsy",
            score=clip01(score),
            quality=1.0,
            debug={"model_loaded": True, "feature_vector": dict(zip(self.feature_names, vector[0]))},
        )


class FusionEngine:
    def __init__(self, config: Mapping[str, Any]):
        self.config = config
        self.fps = safe_float(config.get("fps", 20.0), 20.0)
        self.quality_gate = config.get("quality_gate", {})
        self.previous_state = "alert"
        self._active = {head: False for head in HEADS}
        self._enter_counts = {head: 0 for head in HEADS}
        self._exit_counts = {head: 0 for head in HEADS}

    def reset(self) -> None:
        self.previous_state = "alert"
        self._active = {head: False for head in HEADS}
        self._enter_counts = {head: 0 for head in HEADS}
        self._exit_counts = {head: 0 for head in HEADS}

    def _head_cfg(self, head: str) -> Mapping[str, Any]:
        return self.config.get(head, {})

    def _gate_quality(self, head: str, output: HeadOutput) -> bool:
        quality_key = {
            "microsleep": "eye",
            "yawning": "mouth",
            "distracted": "head",
            "drowsy": "drowsy",
        }[head]
        return output.quality >= safe_float(self.quality_gate.get(quality_key, 0.45), 0.45)

    def _update_hysteresis(self, head: str, output: HeadOutput) -> bool:
        cfg = self._head_cfg(head)
        enter = safe_float(cfg.get("enter", 0.60), 0.60)
        exit_ = safe_float(cfg.get("exit", 0.35), 0.35)
        enter_frames = frames_from_seconds(safe_float(cfg.get("enter_sec", 0.20), 0.20), self.fps)
        exit_frames = frames_from_seconds(safe_float(cfg.get("exit_sec", 0.30), 0.30), self.fps)

        quality_ok = self._gate_quality(head, output)
        effective_score = output.score if quality_ok else 0.0

        if not self._active[head]:
            if effective_score >= enter:
                self._enter_counts[head] += 1
            else:
                self._enter_counts[head] = 0
            if self._enter_counts[head] >= enter_frames:
                self._active[head] = True
                self._exit_counts[head] = 0
        else:
            if effective_score <= exit_:
                self._exit_counts[head] += 1
            else:
                self._exit_counts[head] = 0
            if self._exit_counts[head] >= exit_frames:
                self._active[head] = False
                self._enter_counts[head] = 0

        output.active = self._active[head]
        output.debug["quality_gate_ok"] = quality_ok
        output.debug["hysteresis_active"] = self._active[head]
        return output.active

    def fuse(self, heads: dict[str, HeadOutput], temporal: TemporalFeatures) -> MultiHeadOutput:
        for name in HEADS:
            self._update_hysteresis(name, heads[name])

        margin = safe_float(self.config.get("fusion", {}).get("conflict_margin", 0.12), 0.12)

        if heads["microsleep"].active:
            state = "microsleep"
            source = "microsleep"
        elif heads["yawning"].active and heads["distracted"].active:
            yawn_score = heads["yawning"].score
            dist_score = heads["distracted"].score
            if yawn_score >= dist_score + margin:
                state = "yawning"
                source = "yawning"
            elif dist_score >= yawn_score + margin:
                state = "distracted"
                source = "distracted"
            elif self.previous_state in {"yawning", "distracted"}:
                state = self.previous_state
                source = f"{self.previous_state}_tie_keep_previous"
            else:
                state = "distracted" if dist_score >= yawn_score else "yawning"
                source = f"{state}_tie_score"
        elif heads["yawning"].active:
            state = "yawning"
            source = "yawning"
        elif heads["distracted"].active:
            state = "distracted"
            source = "distracted"
        elif heads["drowsy"].active:
            state = "drowsy"
            source = "drowsy"
        else:
            state = "alert"
            source = "fallback"

        head_scores = {name: round(heads[name].score, 4) for name in HEADS}
        confidence = heads[source.split("_")[0]].score if source.split("_")[0] in heads else 1.0 - max(head_scores.values())
        confidence = clip01(confidence)
        self.previous_state = state
        return MultiHeadOutput(
            state=state,
            confidence=confidence,
            source_head=source,
            head_scores=head_scores,
            heads=heads,
            temporal=temporal,
            debug={"active_heads": {name: heads[name].active for name in HEADS}},
        )


class MultiHeadDriverStateV3:
    """Experimental stateful Challenge 2 multi-head driver-state engine.

    The class accepts primitive per-frame features. It does not perform face or
    hand landmark extraction itself, so it can be integrated later without
    modifying the stable production extractor.
    """

    def __init__(self, config_path: str | Path | None = None, drowsy_model_path: str | Path | None = None):
        self.config = load_config(config_path)
        self.personalization = PersonalizationLayer(self.config)
        self.temporal = TemporalFeatureEngine(self.config)
        self.heads = {
            "microsleep": MicrosleepHead(self.config),
            "yawning": YawningHead(self.config),
            "distracted": DistractedHead(self.config),
            "drowsy": DrowsyHead(self.config, drowsy_model_path),
        }
        self.fusion = FusionEngine(self.config)

    def reset(self) -> None:
        self.temporal = TemporalFeatureEngine(self.config)
        self.fusion.reset()

    def predict(
        self,
        raw: RawDriverFeatures | Mapping[str, Any],
        profile: DriverProfile | Mapping[str, Any] | None = None,
    ) -> MultiHeadOutput:
        raw_features = raw if isinstance(raw, RawDriverFeatures) else RawDriverFeatures.from_mapping(raw)
        personal = self.personalization.transform(raw_features, profile)
        temporal = self.temporal.update(personal)
        head_outputs = {
            name: head.predict(personal, temporal)
            for name, head in self.heads.items()
        }
        return self.fusion.fuse(head_outputs, temporal)
