"""Stateful, causal driver-state inference shared by batch and webcam flows."""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import yaml

from .dms_core import DMSCore
from .ml_features import feature_names, predict_states

DRIVER_STATES = {
    "alert", "drowsy", "yawning", "distracted", "microsleep"
}


class DriverStatePredictor:
    """MediaPipe feature extraction plus the production Random Forest."""

    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path,
    ) -> None:
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.config = yaml.safe_load(
            self.config_path.read_text(encoding="utf-8")
        )
        self.artifact: dict[str, Any] = joblib.load(self.model_path)
        if self.artifact.get("feature_names") != feature_names():
            raise ValueError(
                "Model feature schema does not match Challenge 2 runtime"
            )
        model_classes = set(self.artifact.get("model_classes", []))
        if not model_classes or not model_classes <= DRIVER_STATES:
            raise ValueError(f"Invalid model classes: {sorted(model_classes)}")
        self._engine = DMSCore(self.config)
        self._history: deque[dict[str, Any]] = deque()

    @property
    def model_classes(self) -> list[str]:
        return list(self.artifact["model_classes"])

    def predict_frame(
        self,
        frame_id: int,
        timestamp_ms: int,
        cabin_bgr: np.ndarray,
    ) -> dict[str, Any]:
        primitive = self._engine.process(
            cabin_bgr, int(frame_id), int(timestamp_ms)
        )
        self._history.append(primitive)
        cutoff = int(timestamp_ms) - 30_000
        while self._history and self._history[0]["timestamp_ms"] < cutoff:
            self._history.popleft()

        states, confidences = predict_states(
            list(self._history), self.artifact
        )
        state = states[-1]
        if state not in DRIVER_STATES:
            state = "alert"
        return {
            "state": state,
            "confidence": float(confidences[-1]),
            "alertness_score": float(primitive["alertness_score"]),
            "eye_state": primitive["eye_state"],
            "mouth_state": primitive["mouth_state"],
            "head_pose": primitive["head_state"],
            "rule_state": primitive["driver_state"],
            "quality_status": primitive["observation"]["quality_status"],
            "features": primitive["features"],
        }

    def reset(self) -> None:
        self._engine.close()
        self._engine = DMSCore(self.config)
        self._history.clear()

    def close(self) -> None:
        self._engine.close()
        self._history.clear()

    def __enter__(self) -> "DriverStatePredictor":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
