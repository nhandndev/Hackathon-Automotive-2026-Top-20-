"""Python 3.13-compatible ONNX face detector and 468-point landmarker."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort


LANDMARK_INPUT_SIZE = 192
LANDMARK_COUNT = 468
LANDMARK_BACKEND = "onnx-yunet-facemesh468"


@dataclass(frozen=True)
class FaceLandmarkResult:
    """FaceMesh-compatible normalized landmarks for one detected face."""

    landmarks: np.ndarray
    confidence: float
    backend: str = LANDMARK_BACKEND


def _resolve_model_path(value: str | Path, default_model_dir: Path) -> Path:
    path = Path(value)
    candidates = [path] if path.is_absolute() else [
        default_model_dir / path,
        default_model_dir / path.name,
        path,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Face model not found. Searched: {searched}")


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


class OnnxFaceLandmarker:
    """YuNet face localization followed by MediaPipe-compatible FaceMesh ONNX."""

    def __init__(
        self,
        config: dict[str, Any],
        default_model_dir: Path,
    ) -> None:
        backend = str(config.get("backend", "onnx")).strip().lower()
        if backend != "onnx":
            raise ValueError(
                f"Unsupported face backend '{backend}'; Python 3.13 runtime "
                "requires backend=onnx"
            )
        detector_path = _resolve_model_path(
            config.get("detector_model", "face_detection_yunet_2023mar.onnx"),
            default_model_dir,
        )
        landmark_path = _resolve_model_path(
            config.get("landmark_model", "face_landmark_468.onnx"),
            default_model_dir,
        )
        self.min_detection_confidence = float(
            config.get("min_detection_confidence", 0.5)
        )
        self.min_landmark_confidence = float(
            config.get("min_landmark_confidence", 0.5)
        )
        self.roi_scale = float(config.get("roi_scale", 1.5))
        self.roi_vertical_shift = float(config.get("roi_vertical_shift", -0.05))
        if self.roi_scale <= 0:
            raise ValueError("face.roi_scale must be positive")

        self.detector = cv2.FaceDetectorYN.create(
            str(detector_path),
            "",
            (320, 320),
            self.min_detection_confidence,
            float(config.get("nms_threshold", 0.3)),
            int(config.get("top_k", 5000)),
        )
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        session_options.intra_op_num_threads = int(
            config.get("intra_op_num_threads", 0)
        )
        self.session = ort.InferenceSession(
            str(landmark_path),
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
        model_input = self.session.get_inputs()[0]
        model_outputs = self.session.get_outputs()
        if list(model_input.shape) != [1, 192, 192, 3]:
            raise ValueError(
                f"Unsupported face landmark input shape: {model_input.shape}"
            )
        if not any(
            int(np.prod([dim for dim in output.shape if isinstance(dim, int)]))
            == LANDMARK_COUNT * 3
            for output in model_outputs
        ):
            raise ValueError("ONNX model does not expose 468 x 3 landmarks")
        self.input_name = model_input.name
        self.landmark_output_name = next(
            output.name
            for output in model_outputs
            if int(np.prod([dim for dim in output.shape if isinstance(dim, int)]))
            == LANDMARK_COUNT * 3
        )
        self.presence_output_name = next(
            (
                output.name
                for output in model_outputs
                if int(
                    np.prod(
                        [dim for dim in output.shape if isinstance(dim, int)]
                    )
                )
                == 1
            ),
            None,
        )

    def close(self) -> None:
        """Release references to native runtimes."""
        self.session = None  # type: ignore[assignment]
        self.detector = None  # type: ignore[assignment]

    def detect(
        self,
        frame_bgr: np.ndarray,
        timestamp_ms: int | None = None,
    ) -> FaceLandmarkResult | None:
        del timestamp_ms
        if frame_bgr is None or frame_bgr.ndim != 3:
            return None
        height, width = frame_bgr.shape[:2]
        if width < 2 or height < 2:
            return None

        self.detector.setInputSize((width, height))
        _, detections = self.detector.detect(frame_bgr)
        if detections is None or len(detections) == 0:
            return None
        face = max(
            detections,
            key=lambda row: float(row[2] * row[3] * max(row[-1], 0.0)),
        )
        detection_confidence = float(face[-1])
        if detection_confidence < self.min_detection_confidence:
            return None

        x, y, box_width, box_height = map(float, face[:4])
        side = max(box_width, box_height) * self.roi_scale
        center_x = x + box_width * 0.5
        center_y = y + box_height * (0.5 + self.roi_vertical_shift)
        x0 = center_x - side * 0.5
        y0 = center_y - side * 0.5
        scale = LANDMARK_INPUT_SIZE / max(side, 1e-6)
        transform = np.asarray(
            [[scale, 0.0, -x0 * scale], [0.0, scale, -y0 * scale]],
            dtype=np.float32,
        )
        crop = cv2.warpAffine(
            frame_bgr,
            transform,
            (LANDMARK_INPUT_SIZE, LANDMARK_INPUT_SIZE),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        tensor = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32)
        tensor = np.expand_dims(tensor / 255.0, axis=0)
        output_names = [self.landmark_output_name]
        if self.presence_output_name is not None:
            output_names.append(self.presence_output_name)
        outputs = self.session.run(output_names, {self.input_name: tensor})
        landmarks = np.asarray(outputs[0], dtype=np.float32).reshape(
            LANDMARK_COUNT, 3
        )
        presence = (
            _sigmoid(float(np.asarray(outputs[1]).reshape(-1)[0]))
            if len(outputs) > 1
            else 1.0
        )
        confidence = min(detection_confidence, presence)
        if confidence < self.min_landmark_confidence:
            return None

        normalized = np.empty_like(landmarks, dtype=np.float64)
        normalized[:, 0] = (x0 + landmarks[:, 0] / scale) / width
        normalized[:, 1] = (y0 + landmarks[:, 1] / scale) / height
        normalized[:, 2] = landmarks[:, 2] / LANDMARK_INPUT_SIZE
        if not np.isfinite(normalized).all():
            return None
        return FaceLandmarkResult(
            landmarks=normalized,
            confidence=float(np.clip(confidence, 0.0, 1.0)),
        )
