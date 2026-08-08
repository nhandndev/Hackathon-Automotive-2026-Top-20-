"""Causal rolling-window features for the Challenge 2 ML classifier."""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

import numpy as np


WINDOW_SECONDS = (3, 10, 30)
BASE_KEYS = (
    "ear_robust",
    "closure_ratio",
    "perclos_30s",
    "continuous_eye_closure_sec",
    "mar",
    "yaw_deg",
    "pitch_deg",
    "roll_deg",
)


def _number(value: Any, default: float = np.nan) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if np.isfinite(number) else default


def feature_names() -> list[str]:
    names = [f"instant_{key}" for key in BASE_KEYS]
    for seconds in WINDOW_SECONDS:
        suffix = f"{seconds}s"
        names.extend([
            f"ear_median_{suffix}",
            f"ear_q10_{suffix}",
            f"ear_std_{suffix}",
            f"closed_fraction_{suffix}",
            f"max_eye_closure_sec_{suffix}",
            f"long_closure_fraction_{suffix}",
            f"microsleep_onset_count_{suffix}",
            f"mar_median_{suffix}",
            f"mar_q75_{suffix}",
            f"mar_max_{suffix}",
            f"mouth_open_fraction_{suffix}",
            f"abs_yaw_median_{suffix}",
            f"abs_yaw_q90_{suffix}",
            f"abs_pitch_median_{suffix}",
            f"abs_pitch_q90_{suffix}",
            f"off_road_fraction_{suffix}",
            f"face_coverage_{suffix}",
        ])
    return names


def _quantile(values: list[float], q: float, default: float = 0.0) -> float:
    finite = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    return float(np.quantile(finite, q)) if finite.size else default


def _median(values: list[float], default: float = 0.0) -> float:
    return _quantile(values, 0.5, default)


def _row_values(row: dict[str, Any]) -> dict[str, float]:
    features = row.get("features", row)
    observation = row.get("observation", {})
    ear = _number(features.get("ear_robust"))
    mar = _number(features.get("mar"))
    yaw = _number(features.get("yaw_deg"))
    pitch = _number(features.get("pitch_deg"))
    detected = observation.get("face_detected")
    if detected is None:
        detected = np.isfinite(ear)
    eye_state = row.get("eye_state")
    mouth_state = row.get("mouth_state")
    return {
        "ear_robust": ear,
        "closure_ratio": _number(features.get("closure_ratio"), 0.0),
        "perclos_30s": _number(features.get("perclos_30s"), 0.0),
        "continuous_eye_closure_sec": (
            _number(features.get("continuous_eye_closure_ms"), 0.0) / 1000.0
        ),
        "mar": mar,
        "yaw_deg": yaw,
        "pitch_deg": pitch,
        "roll_deg": _number(features.get("roll_deg"), 0.0),
        "closed": float(eye_state == "closed"),
        "mouth_open": float(mouth_state in {"open", "yawning"}),
        "off_road": float(
            (np.isfinite(yaw) and abs(yaw) >= 20.0)
            or (np.isfinite(pitch) and abs(pitch) >= 15.0)
        ),
        "detected": float(bool(detected)),
    }


class CausalFeatureBuffer:
    """Incrementally build one causal feature vector per incoming frame."""

    def __init__(self) -> None:
        self.histories = {seconds: deque() for seconds in WINDOW_SECONDS}

    def reset(self) -> None:
        for history in self.histories.values():
            history.clear()

    def update(self, row: dict[str, Any]) -> np.ndarray:
        timestamp_ms = int(_number(row.get("timestamp_ms"), 0.0))
        values = _row_values(row)
        for seconds, history in self.histories.items():
            history.append((timestamp_ms, values))
            cutoff = timestamp_ms - seconds * 1000
            while history and history[0][0] < cutoff:
                history.popleft()

        vector = [
            values[key] if np.isfinite(values[key]) else 0.0
            for key in BASE_KEYS
        ]
        for seconds in WINDOW_SECONDS:
            samples = [item for _, item in self.histories[seconds]]
            ears = [item["ear_robust"] for item in samples]
            closure_seconds = [
                item["continuous_eye_closure_sec"] for item in samples
            ]
            mars = [item["mar"] for item in samples]
            yaws = [abs(item["yaw_deg"]) for item in samples]
            pitches = [abs(item["pitch_deg"]) for item in samples]
            valid = max(1, sum(item["detected"] > 0 for item in samples))
            detected_samples = [item for item in samples if item["detected"] > 0]
            onset_count = sum(
                previous["continuous_eye_closure_sec"] < 1.0
                <= current["continuous_eye_closure_sec"]
                for previous, current in zip(samples, samples[1:])
            )
            vector.extend([
                _median(ears),
                _quantile(ears, 0.10),
                float(np.nanstd(ears)) if np.isfinite(ears).any() else 0.0,
                sum(item["closed"] for item in detected_samples) / valid,
                max(closure_seconds, default=0.0),
                sum(
                    item["continuous_eye_closure_sec"] >= 1.0
                    for item in detected_samples
                ) / valid,
                float(onset_count),
                _median(mars),
                _quantile(mars, 0.75),
                _quantile(mars, 1.0),
                sum(item["mouth_open"] for item in detected_samples) / valid,
                _median(yaws),
                _quantile(yaws, 0.90),
                _median(pitches),
                _quantile(pitches, 0.90),
                sum(item["off_road"] for item in detected_samples) / valid,
                sum(item["detected"] for item in samples) / max(1, len(samples)),
            ])
        result = np.asarray(vector, dtype=np.float32)
        if result.shape != (len(feature_names()),):
            raise RuntimeError("Rolling feature-name and value counts do not match")
        return result


def rolling_feature_matrix(rows: Iterable[dict[str, Any]]) -> np.ndarray:
    """Return one causal feature vector per input row."""
    builder = CausalFeatureBuffer()
    matrix = [builder.update(row) for row in rows]
    if not matrix:
        return np.empty((0, len(feature_names())), dtype=np.float32)

    return np.asarray(matrix, dtype=np.float32)


def predict_latest(
    row: dict[str, Any],
    artifact: dict[str, Any],
    buffer: CausalFeatureBuffer,
) -> tuple[str, float]:
    """Predict one frame without rebuilding the previous 30-second matrix."""
    if artifact.get("feature_names") != feature_names():
        raise ValueError(
            "Model feature schema does not match this code; retrain the model"
        )
    vector = buffer.update(row).reshape(1, -1)
    model = artifact["model"]
    state = str(model.predict(vector)[0])
    confidence = (
        float(model.predict_proba(vector).max())
        if hasattr(model, "predict_proba")
        else 1.0
    )
    return state, confidence


def predict_states(
    rows: Iterable[dict[str, Any]],
    artifact: dict[str, Any],
) -> tuple[list[str], list[float]]:
    """Apply a saved classifier artifact to causal rolling features."""
    if artifact.get("feature_names") != feature_names():
        raise ValueError(
            "Model feature schema does not match this code; retrain the model"
        )
    matrix = rolling_feature_matrix(rows)
    model = artifact["model"]
    states = model.predict(matrix).tolist()
    if hasattr(model, "predict_proba"):
        confidence = model.predict_proba(matrix).max(axis=1).astype(float).tolist()
    else:
        confidence = [1.0] * len(states)
    return states, confidence


FATIGUE_WINDOW_SECONDS = (3, 5, 7, 10)
DISTRACTION_WINDOW_SECONDS = (1, 3)

def fatigue_feature_names() -> list[str]:
    names = [
        "instant_ear_robust", "instant_closure_ratio", 
        "instant_continuous_eye_closure_sec", "instant_mar"
    ]
    for seconds in FATIGUE_WINDOW_SECONDS:
        suffix = f"{seconds}s"
        names.extend([
            f"ear_median_{suffix}", f"ear_q10_{suffix}", f"ear_std_{suffix}",
            f"closed_fraction_{suffix}", f"max_eye_closure_sec_{suffix}", 
            f"long_closure_fraction_{suffix}", f"microsleep_onset_count_{suffix}",
            f"mar_median_{suffix}", f"mar_q75_{suffix}", f"mar_max_{suffix}", 
            f"mouth_open_fraction_{suffix}", f"face_coverage_{suffix}"
        ])
    return names

def distraction_feature_names() -> list[str]:
    names = [
        "instant_yaw_deg", "instant_pitch_deg", "instant_roll_deg", 
        "instant_off_road_duration_sec", "instant_hand_visible", 
        "instant_hand_x_rel_face", "instant_hand_y_rel_face", 
        "instant_hand_to_face_distance", "instant_hand_motion", 
        "instant_hand_active", "instant_head_side_and_hand_active", 
        "instant_head_down_and_hand_active"
    ]
    for seconds in DISTRACTION_WINDOW_SECONDS:
        suffix = f"{seconds}s"
        names.extend([
            f"abs_yaw_median_{suffix}", f"abs_yaw_q90_{suffix}",
            f"abs_pitch_median_{suffix}", f"abs_pitch_q90_{suffix}",
            f"off_road_fraction_{suffix}", f"face_coverage_{suffix}",
            f"hand_visible_ratio_{suffix}", f"hand_active_ratio_{suffix}",
            f"head_hand_interaction_ratio_{suffix}"
        ])
    return names

def _extended_row_values(row: dict[str, Any]) -> dict[str, float]:
    base = _row_values(row)
    features = row.get("features", row)
    base.update({
        "off_road_duration_sec": _number(features.get("off_road_duration_ms"), 0.0) / 1000.0,
        "hand_visible": _number(features.get("hand_visible"), 0.0),
        "hand_x_rel_face": _number(features.get("hand_x_rel_face"), 0.0),
        "hand_y_rel_face": _number(features.get("hand_y_rel_face"), 0.0),
        "hand_to_face_distance": _number(features.get("hand_to_face_distance"), 2.0),
        "hand_motion": _number(features.get("hand_motion"), 0.0),
        "hand_active": _number(features.get("hand_active"), 0.0),
        "head_side_and_hand_active": _number(features.get("head_side_and_hand_active"), 0.0),
        "head_down_and_hand_active": _number(features.get("head_down_and_hand_active"), 0.0),
        "head_hand_interaction": _number(features.get("head_hand_interaction"), 0.0),
    })
    return base

class FatigueFeatureBuffer:
    def __init__(self) -> None:
        self.histories = {s: deque() for s in FATIGUE_WINDOW_SECONDS}
        
    def reset(self) -> None:
        for history in self.histories.values():
            history.clear()
            
    def update(self, row: dict[str, Any]) -> np.ndarray:
        timestamp_ms = int(_number(row.get("timestamp_ms"), 0.0))
        values = _extended_row_values(row)
        for seconds, history in self.histories.items():
            history.append((timestamp_ms, values))
            cutoff = timestamp_ms - seconds * 1000
            while history and history[0][0] < cutoff:
                history.popleft()
                
        vector = [
            values["ear_robust"] if np.isfinite(values["ear_robust"]) else 0.0,
            values["closure_ratio"],
            values["continuous_eye_closure_sec"],
            values["mar"] if np.isfinite(values["mar"]) else 0.0,
        ]
        
        for seconds in FATIGUE_WINDOW_SECONDS:
            samples = [item for _, item in self.histories[seconds]]
            ears = [item["ear_robust"] for item in samples]
            mars = [item["mar"] for item in samples]
            closure_seconds = [item["continuous_eye_closure_sec"] for item in samples]
            valid = max(1, sum(item["detected"] > 0 for item in samples))
            detected_samples = [item for item in samples if item["detected"] > 0]
            onset_count = sum(
                previous["continuous_eye_closure_sec"] < 1.0 <= current["continuous_eye_closure_sec"]
                for previous, current in zip(samples, samples[1:])
            )
            
            vector.extend([
                _median(ears),
                _quantile(ears, 0.10),
                float(np.nanstd(ears)) if np.isfinite(ears).any() else 0.0,
                sum(item["closed"] for item in detected_samples) / valid,
                max(closure_seconds, default=0.0),
                sum(item["continuous_eye_closure_sec"] >= 1.0 for item in detected_samples) / valid,
                float(onset_count),
                _median(mars),
                _quantile(mars, 0.75),
                _quantile(mars, 1.0),
                sum(item["mouth_open"] for item in detected_samples) / valid,
                sum(item["detected"] for item in samples) / max(1, len(samples)),
            ])
            
        return np.asarray(vector, dtype=np.float32)

class DistractionFeatureBuffer:
    def __init__(self) -> None:
        self.histories = {s: deque() for s in DISTRACTION_WINDOW_SECONDS}
        
    def reset(self) -> None:
        for history in self.histories.values():
            history.clear()
            
    def update(self, row: dict[str, Any]) -> np.ndarray:
        timestamp_ms = int(_number(row.get("timestamp_ms"), 0.0))
        values = _extended_row_values(row)
        for seconds, history in self.histories.items():
            history.append((timestamp_ms, values))
            cutoff = timestamp_ms - seconds * 1000
            while history and history[0][0] < cutoff:
                history.popleft()
                
        vector = [
            values["yaw_deg"] if np.isfinite(values["yaw_deg"]) else 0.0,
            values["pitch_deg"] if np.isfinite(values["pitch_deg"]) else 0.0,
            values["roll_deg"] if np.isfinite(values["roll_deg"]) else 0.0,
            values["off_road_duration_sec"],
            values["hand_visible"],
            values["hand_x_rel_face"],
            values["hand_y_rel_face"],
            values["hand_to_face_distance"],
            values["hand_motion"],
            values["hand_active"],
            values["head_side_and_hand_active"],
            values["head_down_and_hand_active"],
        ]
        
        for seconds in DISTRACTION_WINDOW_SECONDS:
            samples = [item for _, item in self.histories[seconds]]
            yaws = [abs(item["yaw_deg"]) for item in samples]
            pitches = [abs(item["pitch_deg"]) for item in samples]
            valid = max(1, sum(item["detected"] > 0 for item in samples))
            detected_samples = [item for item in samples if item["detected"] > 0]
            
            vector.extend([
                _median(yaws),
                _quantile(yaws, 0.90),
                _median(pitches),
                _quantile(pitches, 0.90),
                sum(item["off_road"] for item in detected_samples) / valid,
                sum(item["detected"] for item in samples) / max(1, len(samples)),
                sum(item["hand_visible"] for item in samples) / max(1, len(samples)),
                sum(item["hand_active"] for item in samples) / max(1, len(samples)),
                sum(item["head_hand_interaction"] for item in samples) / max(1, len(samples)),
            ])
            
        return np.asarray(vector, dtype=np.float32)


# ====================================================================== #
# Challenge 2: Architect-v2 Unified 84-Feature Buffer
# ====================================================================== #

ARCHITECT_V2_HAND_WINDOWS = (1, 3)

def architect_v2_hand_feature_names() -> list[str]:
    names = [
        "instant_hand_visible",
        "instant_hand_count",
        "instant_min_hand_to_mouth_norm",
        "instant_min_hand_to_ear_side_norm",
        "instant_min_hand_to_eye_norm",
        "instant_min_hand_to_face_center_norm",
        "instant_hand_motion_norm",
        # 1s Window
        "hand_visible_fraction_1s",
        "hand_near_mouth_fraction_1s",
        "hand_near_ear_fraction_1s",
        "hand_motion_mean_1s",
        "hand_motion_max_1s",
        "offroad_and_hand_visible_fraction_1s",
        "offroad_and_hand_active_fraction_1s",
        # 3s Window
        "hand_visible_fraction_3s",
        "hand_near_mouth_fraction_3s",
        "hand_near_ear_fraction_3s",
        "hand_motion_mean_3s",
        "hand_motion_max_3s",
        "offroad_and_hand_visible_fraction_3s",
        "offroad_and_hand_active_fraction_3s",
        # Extra instant / 3s
        "instant_min_hand_to_left_ear_side_norm",
        "instant_min_hand_to_right_ear_side_norm",
        "hand_near_face_fraction_3s",
        "hand_active_fraction_3s",
    ]
    return names

def architect_v2_feature_names() -> list[str]:
    names = feature_names() + architect_v2_hand_feature_names()
    if len(names) != 84:
        raise RuntimeError(f"Architect-v2 expected 84 features, got {len(names)}")
    return names

def _architect_v2_hand_row_values(row: dict[str, Any]) -> dict[str, float]:
    features = row.get("features", row)
    observation = row.get("observation", {})
    detected = observation.get("face_detected")
    if detected is None:
        detected = np.isfinite(_number(features.get("ear_robust")))
        
    return {
        "hand_visible": _number(features.get("hand_visible"), 0.0),
        "hand_count": _number(features.get("hand_count"), 0.0),
        "min_hand_to_mouth_norm": _number(features.get("min_hand_to_mouth_norm"), 2.0),
        "min_hand_to_ear_side_norm": _number(features.get("min_hand_to_ear_side_norm"), 2.0),
        "min_hand_to_eye_norm": _number(features.get("min_hand_to_eye_norm"), 2.0),
        "min_hand_to_face_center_norm": _number(features.get("min_hand_to_face_center_norm"), 2.0),
        "min_hand_to_left_ear_side_norm": _number(features.get("min_hand_to_left_ear_side_norm"), 2.0),
        "min_hand_to_right_ear_side_norm": _number(features.get("min_hand_to_right_ear_side_norm"), 2.0),
        "hand_motion_norm": _number(features.get("hand_motion_norm"), 0.0),
        "hand_near_mouth": _number(features.get("hand_near_mouth"), 0.0),
        "hand_near_ear": _number(features.get("hand_near_ear"), 0.0),
        "hand_near_face": _number(features.get("hand_near_face"), 0.0),
        "offroad_and_hand_visible": _number(features.get("offroad_and_hand_visible"), 0.0),
        "offroad_and_hand_active": _number(features.get("offroad_and_hand_active"), 0.0),
        "hand_active": _number(features.get("hand_active"), 0.0),
        "detected": float(bool(detected)),
    }

class ArchitectV2HandFeatureBuffer:
    def __init__(self) -> None:
        self.histories = {s: deque() for s in ARCHITECT_V2_HAND_WINDOWS}
        
    def reset(self) -> None:
        for history in self.histories.values():
            history.clear()
            
    def update(self, row: dict[str, Any]) -> np.ndarray:
        timestamp_ms = int(_number(row.get("timestamp_ms"), 0.0))
        values = _architect_v2_hand_row_values(row)
        for seconds, history in self.histories.items():
            history.append((timestamp_ms, values))
            cutoff = timestamp_ms - seconds * 1000
            while history and history[0][0] < cutoff:
                history.popleft()
                
        # 1. Instant features (7 items)
        vector = [
            values["hand_visible"],
            values["hand_count"],
            values["min_hand_to_mouth_norm"],
            values["min_hand_to_ear_side_norm"],
            values["min_hand_to_eye_norm"],
            values["min_hand_to_face_center_norm"],
            values["hand_motion_norm"],
        ]
        
        # 2. Window-based features (1s and 3s)
        for seconds in ARCHITECT_V2_HAND_WINDOWS:
            samples = [item for _, item in self.histories[seconds]]
            valid = max(1, sum(item["detected"] > 0 for item in samples))
            detected_samples = [item for item in samples if item["detected"] > 0]
            
            motions = [item["hand_motion_norm"] for item in samples]
            
            vector.extend([
                sum(item["hand_visible"] for item in detected_samples) / valid,
                sum(item["hand_near_mouth"] for item in detected_samples) / valid,
                sum(item["hand_near_ear"] for item in detected_samples) / valid,
                float(np.nanmean(motions)) if np.isfinite(motions).any() else 0.0,
                float(np.nanmax(motions)) if np.isfinite(motions).any() else 0.0,
                sum(item["offroad_and_hand_visible"] for item in detected_samples) / valid,
                sum(item["offroad_and_hand_active"] for item in detected_samples) / valid,
            ])
            
        # 3. Extra instant / 3s features (4 items)
        vector.extend([
            values["min_hand_to_left_ear_side_norm"],
            values["min_hand_to_right_ear_side_norm"],
            sum(item["hand_near_face"] for item in [i for _, i in self.histories[3] if i["detected"] > 0]) / max(1, sum(i["detected"] > 0 for _, i in self.histories[3])),
            sum(item["hand_active"] for item in [i for _, i in self.histories[3] if i["detected"] > 0]) / max(1, sum(i["detected"] > 0 for _, i in self.histories[3])),
        ])
        
        return np.asarray(vector, dtype=np.float32)

class ArchitectV2FeatureBuffer:
    def __init__(self) -> None:
        self.legacy = CausalFeatureBuffer()
        self.hand = ArchitectV2HandFeatureBuffer()
        
    def reset(self) -> None:
        self.legacy.reset()
        self.hand.reset()
        
    def update(self, row: dict[str, Any]) -> np.ndarray:
        legacy_vec = self.legacy.update(row)
        hand_vec = self.hand.update(row)
        vector = np.concatenate([legacy_vec, hand_vec]).astype(np.float32, copy=False)
        if vector.shape != (84,):
            raise RuntimeError(f"Architect-v2 expected 84 features, got {vector.shape[0]}")
        return vector
