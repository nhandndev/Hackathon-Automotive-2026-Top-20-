"""Stateful, causal driver-state inference shared by batch and webcam flows."""
from __future__ import annotations

import copy
import warnings
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
    FatigueFeatureBuffer,
    DistractionFeatureBuffer,
    ArchitectV2FeatureBuffer,
    feature_names,
    fatigue_feature_names,
    distraction_feature_names,
    predict_latest,
)

from .label_contract import FINAL_LABELS as DRIVER_STATES
from .model_contract import load_driver_artifact, validate_driver_artifact


# Landmark backend validation is done inside validate_driver_artifact



@dataclass(frozen=True)
class FusionResult:
    """Final state after applying the production safety policy."""

    state: str
    confidence: float
    source: str
    reason: str | None = None

def choose_hierarchical_state(
    *,
    fatigue_state: str,
    fatigue_confidence: float,
    distracted_probability: float,
    distracted_threshold: float,
) -> tuple[str, float, str]:
    if distracted_probability >= distracted_threshold:
        return (
            "distracted",
            distracted_probability,
            "distraction-model",
        )

    return (
        fatigue_state,
        fatigue_confidence,
        "fatigue-model",
    )


from .safety_fusion import should_force_microsleep


def fuse_driver_state(
    ml_state: str,
    ml_confidence: float,
    dms_output: dict[str, Any],
    microsleep_min_ms: int,
) -> FusionResult:
    """Override ML only for reliable continuous eye-closure evidence."""
    if should_force_microsleep(dms_output, microsleep_min_ms):
        closure_ms = max(
            0, int(dms_output.get("features", {}).get("continuous_eye_closure_ms", 0) or 0)
        )
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


def state_adjusted_alertness(
    raw_alertness: float,
    final_state: str,
    confidence: float,
) -> float:
    """Keep alertness consistent with the final ML/fusion driver state.

    The primitive rule engine can report high alertness when EAR calibration is
    conservative, while the Random Forest still detects a fatigue state from
    rolling temporal features.  Dashboard/Decision Engine consumers should see
    the final C2 decision, not a contradictory "microsleep + 100% alert" pair.
    """
    value = max(0.0, min(1.0, float(raw_alertness)))
    if confidence < 0.50:
        return value
    caps = {
        "microsleep": 0.05,
        "drowsy": 0.45,
        "yawning": 0.70,
        "distracted": 0.60,
    }
    cap = caps.get(final_state)
    return min(value, cap) if cap is not None else value


class DriverStatePredictor:
    """ONNX feature extraction plus the production Random Forest."""

    def __init__(
        self,
        model_path: str | Path,
        config_path: str | Path,
        driver_profile: DriverProfile | None = None,
        face_detector_interval_frames: int = 1,
    ) -> None:
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.config = yaml.safe_load(
            self.config_path.read_text(encoding="utf-8")
        )
        self.config = copy.deepcopy(self.config)
        self.config.setdefault("face", {})["detector_interval_frames"] = max(
            1, int(face_detector_interval_frames)
        )
        
        self.artifact = load_driver_artifact(self.model_path)
        validate_driver_artifact(self.artifact)
            
        self.architecture = self.artifact.get("architecture", "legacy_5class")
        if self.architecture == "legacy_5class":
            self.model = self.artifact.get("model")
            if self.model is not None and hasattr(self.model, "n_jobs"):
                self.model.n_jobs = 1
        elif self.architecture in ("hierarchical_v1", "hierarchical_v2"):
            self.fatigue_model = self.artifact["fatigue_model"]
            self.distraction_model = self.artifact["distraction_model"]
            if hasattr(self.fatigue_model, "n_jobs"):
                self.fatigue_model.n_jobs = 1
            if hasattr(self.distraction_model, "n_jobs"):
                self.distraction_model.n_jobs = 1
        elif self.architecture == "architect_v2":
            self.model = self.artifact.get("model")
            if self.model is not None and hasattr(self.model, "n_jobs"):
                self.model.n_jobs = 1
                
        self.driver_profile = driver_profile
        self._engine = DMSCore(
            self.config, driver_profile=self.driver_profile
        )
        if self.architecture == "legacy_5class":
            self._features = CausalFeatureBuffer()
        elif self.architecture == "hierarchical_v1":
            self._fatigue_features = FatigueFeatureBuffer()
            self._distraction_features = DistractionFeatureBuffer()
        elif self.architecture == "hierarchical_v2":
            self._fatigue_features = CausalFeatureBuffer()
            self._distraction_features = DistractionFeatureBuffer()
        elif self.architecture == "architect_v2":
            self._features = ArchitectV2FeatureBuffer()

    @property
    def model_classes(self) -> list[str]:
        return list(self.artifact["model_classes"])

    def set_face_detector_interval_frames(self, interval: int) -> None:
        self._engine.face_landmarker.detector_interval_frames = max(1, int(interval))

    def predict_frame(
        self,
        frame_id: int,
        timestamp_ms: int,
        cabin_bgr: np.ndarray,
    ) -> dict[str, Any]:
        primitive = self._engine.process(
            cabin_bgr, int(frame_id), int(timestamp_ms)
        )
        
        fatigue_state_debug = "alert"
        fatigue_conf_debug = 0.0
        distraction_prob_debug = 0.0
        
        if self.architecture == "legacy_5class":
            state, confidence = predict_latest(
                primitive, self.artifact, self._features
            )
            prediction_source = "ML model"
        elif self.architecture in ("hierarchical_v1", "hierarchical_v2"):
            fatigue_vector = self._fatigue_features.update(primitive).reshape(1, -1)
            distraction_vector = self._distraction_features.update(primitive).reshape(1, -1)
            
            fatigue_probs = self.fatigue_model.predict_proba(fatigue_vector)[0]
            distraction_probs = self.distraction_model.predict_proba(distraction_vector)[0]
            
            fatigue_idx = int(np.argmax(fatigue_probs))
            fatigue_state = str(self.fatigue_model.classes_[fatigue_idx])
            fatigue_confidence = float(fatigue_probs[fatigue_idx])
            
            distraction_classes = list(self.distraction_model.classes_)
            p_distracted = float(distraction_probs[distraction_classes.index("distracted")])
            
            distracted_threshold = float(
                self.artifact.get("fusion", {}).get("distracted_threshold", self.config.get("ml", {}).get("distracted_threshold", 0.70))
            )
            
            state, confidence, prediction_source = choose_hierarchical_state(
                fatigue_state=fatigue_state,
                fatigue_confidence=fatigue_confidence,
                distracted_probability=p_distracted,
                distracted_threshold=distracted_threshold,
            )
            
            fatigue_state_debug = fatigue_state
            fatigue_conf_debug = fatigue_confidence
            distraction_prob_debug = p_distracted
        elif self.architecture == "architect_v2":
            vector = self._features.update(primitive).reshape(1, -1)
            probs = self.model.predict_proba(vector)[0]
            index = int(np.argmax(probs))
            state = str(self.model.classes_[index])
            confidence = float(probs[index])
            prediction_source = "architect-v2"
            
            classes = list(self.model.classes_)
            p_distracted = float(probs[classes.index("distracted")])
            distraction_prob_debug = p_distracted
            
        if state not in DRIVER_STATES:
            state = "alert"
        fused = fuse_driver_state(
            state,
            confidence,
            primitive,
            int(self.config["eye"]["microsleep_min_ms"]),
        )
        alertness_score = state_adjusted_alertness(
            float(primitive["alertness_score"]),
            fused.state,
            fused.confidence,
        )
        observation = primitive.get("observation", {})
        return {
            "state": fused.state,
            "confidence": fused.confidence,
            "prediction_source": fused.source if self.architecture == "legacy_5class" or fused.source == "safety-fusion" else prediction_source,
            "fusion_reason": fused.reason,
            "alertness_score": alertness_score,
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
            # webcam compatibility
            "driver_state": fused.state,
            "state_confidence": fused.confidence,
            "rule_driver_state": primitive.get("driver_state", "unknown"),
            "attention_state": primitive.get("attention_state", "unknown"),
            "fatigue_level": primitive.get("fatigue_level", "unknown"),
            "eye_event": primitive.get("eye_event", "none"),
            "mouth_event": primitive.get("mouth_event", "none"),
            "head_state": primitive.get("head_state", "unknown"),
            "observation": observation,
            # new debug fields
            "fatigue_state": fatigue_state_debug,
            "fatigue_confidence": fatigue_conf_debug,
            "distraction_probability": distraction_prob_debug,
            "personalization": "profile" if self.driver_profile is not None else "session",
        }

    def reset(self) -> None:
        self._engine.close()
        self._engine = DMSCore(
            self.config, driver_profile=self.driver_profile
        )
        if self.architecture in ("legacy_5class", "architect_v2"):
            self._features.reset()
        elif self.architecture in ("hierarchical_v1", "hierarchical_v2"):
            self._fatigue_features.reset()
            self._distraction_features.reset()

    def close(self) -> None:
        self._engine.close()
        if self.architecture in ("legacy_5class", "architect_v2"):
            self._features.reset()
        elif self.architecture in ("hierarchical_v1", "hierarchical_v2"):
            self._fatigue_features.reset()
            self._distraction_features.reset()

    def __enter__(self) -> "DriverStatePredictor":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
