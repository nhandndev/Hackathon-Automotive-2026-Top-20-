"""Stateful, causal driver-state inference shared by batch and webcam flows."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import yaml

from .dms_core import DMSCore
from .driver_profile import DriverProfile
from .face_landmarker import LANDMARK_BACKEND
from .ml_features import (
    CausalFeatureBuffer,
    feature_names,
    predict_latest,
)

DRIVER_STATES = {
    "alert", "drowsy", "yawning", "distracted", "microsleep"
}


@dataclass(frozen=True)
class FusionResult:
    """Final state after applying the production safety policy."""

    state: str
    confidence: float
    source: str
    reason: str | None = None


def fuse_driver_state(
    ml_state: str,
    ml_confidence: float,
    dms_output: dict[str, Any],
    microsleep_min_ms: int,
) -> FusionResult:
    """Override ML only for reliable continuous eye-closure evidence."""
    observation = dms_output.get("observation", {})
    features = dms_output.get("features", {})
    reliable = bool(
        observation.get("face_detected")
        and observation.get("left_eye_valid")
        and observation.get("right_eye_valid")
        and observation.get("monitoring_available")
        and observation.get("quality_status")
        not in {"face_missing", "invalid", "calibrating"}
    )
    closure_ms = max(
        0, int(features.get("continuous_eye_closure_ms", 0) or 0)
    )
    if reliable and closure_ms >= int(microsleep_min_ms):
        return FusionResult(
            state="microsleep",
            confidence=max(float(ml_confidence), 0.95),
            source="safety-fusion",
            reason=f"continuous_eye_closure_ms={closure_ms}",
        )
    return FusionResult(
        state=ml_state,
        confidence=float(ml_confidence),
        source="ML model",
    )


class DriverStatePredictor:
    """ONNX feature extraction plus the production Random Forest."""

    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path,
        driver_profile: DriverProfile | None = None,
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
        if self.artifact.get("landmark_backend") != LANDMARK_BACKEND:
            raise ValueError(
                "Model was not trained with the active ONNX landmark backend; "
                "use driver_state_rf_v3_onnx.joblib or retrain it"
            )
        model_classes = set(self.artifact.get("model_classes", []))
        if not model_classes or not model_classes <= DRIVER_STATES:
            raise ValueError(f"Invalid model classes: {sorted(model_classes)}")
        self.driver_profile = driver_profile
        self._engine = DMSCore(
            self.config, driver_profile=self.driver_profile
        )
        self._features = CausalFeatureBuffer()

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
        state, confidence = predict_latest(
            primitive, self.artifact, self._features
        )
        if state not in DRIVER_STATES:
            state = "alert"
        fused = fuse_driver_state(
            state,
            confidence,
            primitive,
            int(self.config["eye"]["microsleep_min_ms"]),
        )
        observation = primitive.get("observation", {})
        return {
            "state": fused.state,
            "confidence": fused.confidence,
            "prediction_source": fused.source,
            "fusion_reason": fused.reason,
            "alertness_score": float(primitive["alertness_score"]),
            "eye_state": primitive["eye_state"],
            "mouth_state": primitive["mouth_state"],
            "head_pose": primitive["head_state"],
            "rule_state": primitive["driver_state"],
            "quality_status": observation.get("quality_status", "invalid"),
            "face_detected": bool(observation.get("face_detected", False)),
            "left_eye_valid": bool(observation.get("left_eye_valid", False)),
            "right_eye_valid": bool(observation.get("right_eye_valid", False)),
            "monitoring_available": bool(
                observation.get("monitoring_available", False)
            ),
            "valid_window_ratio": float(
                observation.get("coverage_30s", 0.0) or 0.0
            ),
            "features": primitive["features"],
            "visualization": primitive.get("visualization", {}),
        }

    def reset(self) -> None:
        self._engine.close()
        self._engine = DMSCore(
            self.config, driver_profile=self.driver_profile
        )
        self._features.reset()

    def close(self) -> None:
        self._engine.close()
        self._features.reset()

    def __enter__(self) -> "DriverStatePredictor":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
