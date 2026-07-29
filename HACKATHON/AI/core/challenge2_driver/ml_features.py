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
