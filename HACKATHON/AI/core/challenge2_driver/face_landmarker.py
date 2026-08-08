"""Python 3.13-compatible ONNX face detector and 468-point landmarker."""
from __future__ import annotations

import math
import os
import importlib.util
import ctypes
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


class _OnnxYuNetDetector:
    """YuNet face detector executed by ONNX Runtime (CUDA when available)."""

    _STRIDES = (8, 16, 32)
    _MEAN_BGR = (104.0, 117.0, 123.0)

    def __init__(
        self,
        model_path: Path,
        providers: list[str],
        score_threshold: float,
        nms_threshold: float,
        top_k: int,
        intra_op_num_threads: int,
    ) -> None:
        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        options.intra_op_num_threads = intra_op_num_threads
        self.session = ort.InferenceSession(
            str(model_path), sess_options=options, providers=providers
        )
        model_input = self.session.get_inputs()[0]
        if len(model_input.shape) != 4 or not all(
            isinstance(value, int) for value in model_input.shape[2:]
        ):
            raise ValueError(
                f"Unsupported YuNet input shape: {model_input.shape}"
            )
        self.input_name = model_input.name
        self.input_height = int(model_input.shape[2])
        self.input_width = int(model_input.shape[3])
        self.output_names = {item.name for item in self.session.get_outputs()}
        expected = {
            f"{kind}_{stride}"
            for stride in self._STRIDES
            for kind in ("cls", "obj", "bbox", "kps")
        }
        if not expected <= self.output_names:
            raise ValueError(
                f"Unsupported YuNet outputs: {sorted(self.output_names)}"
            )
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k

    def close(self) -> None:
        self.session = None  # type: ignore[assignment]

    def detect(self, frame_bgr: np.ndarray) -> np.ndarray | None:
        frame_height, frame_width = frame_bgr.shape[:2]
        resize_scale = min(
            self.input_width / frame_width,
            self.input_height / frame_height,
        )
        resized_width = max(1, round(frame_width * resize_scale))
        resized_height = max(1, round(frame_height * resize_scale))
        resized = cv2.resize(
            frame_bgr, (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )
        offset_x = (self.input_width - resized_width) // 2
        offset_y = (self.input_height - resized_height) // 2
        model_image = np.empty(
            (self.input_height, self.input_width, 3), dtype=np.uint8
        )
        model_image[:] = np.asarray(self._MEAN_BGR, dtype=np.uint8)
        model_image[
            offset_y:offset_y + resized_height,
            offset_x:offset_x + resized_width,
        ] = resized
        tensor = cv2.dnn.blobFromImage(
            model_image, 1.0, (self.input_width, self.input_height),
            self._MEAN_BGR, swapRB=False, crop=False,
        )
        names = [
            f"{kind}_{stride}"
            for stride in self._STRIDES
            for kind in ("cls", "obj", "bbox", "kps")
        ]
        values = self.session.run(names, {self.input_name: tensor})
        outputs = dict(zip(names, values))
        detections: list[np.ndarray] = []
        for stride in self._STRIDES:
            cls = np.asarray(outputs[f"cls_{stride}"]).reshape(-1)
            obj = np.asarray(outputs[f"obj_{stride}"]).reshape(-1)
            scores = np.sqrt(
                np.clip(cls, 0.0, 1.0) * np.clip(obj, 0.0, 1.0)
            )
            selected = np.flatnonzero(scores >= self.score_threshold)
            if selected.size == 0:
                continue
            bbox = np.asarray(outputs[f"bbox_{stride}"]).reshape(-1, 4)[selected]
            kps = np.asarray(outputs[f"kps_{stride}"]).reshape(-1, 10)[selected]
            columns = self.input_width // stride
            grid_x = (selected % columns).astype(np.float32)
            grid_y = (selected // columns).astype(np.float32)
            box_width = np.exp(np.clip(bbox[:, 2], -20.0, 20.0)) * stride
            box_height = np.exp(np.clip(bbox[:, 3], -20.0, 20.0)) * stride
            center_x = (bbox[:, 0] + grid_x) * stride
            center_y = (bbox[:, 1] + grid_y) * stride
            decoded = np.empty((selected.size, 15), dtype=np.float32)
            decoded[:, 0] = (
                center_x - box_width * 0.5 - offset_x
            ) / resize_scale
            decoded[:, 1] = (
                center_y - box_height * 0.5 - offset_y
            ) / resize_scale
            decoded[:, 2] = box_width / resize_scale
            decoded[:, 3] = box_height / resize_scale
            for point in range(5):
                decoded[:, 4 + point * 2] = (
                    (kps[:, point * 2] + grid_x) * stride - offset_x
                ) / resize_scale
                decoded[:, 5 + point * 2] = (
                    (kps[:, point * 2 + 1] + grid_y) * stride - offset_y
                ) / resize_scale
            decoded[:, 14] = scores[selected]
            detections.append(decoded)
        if not detections:
            return None
        merged = np.concatenate(detections, axis=0)
        if len(merged) > self.top_k:
            order = np.argpartition(merged[:, 14], -self.top_k)[-self.top_k:]
            merged = merged[order]
        indices = cv2.dnn.NMSBoxes(
            merged[:, :4].tolist(), merged[:, 14].tolist(),
            self.score_threshold, self.nms_threshold,
        )
        if len(indices) == 0:
            return None
        return merged[np.asarray(indices).reshape(-1)]


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
        self.detector_interval_frames = max(
            1, int(config.get("detector_interval_frames", 1))
        )
        self._frame_index = 0
        self._tracked_face: np.ndarray | None = None
        if self.roi_scale <= 0:
            raise ValueError("face.roi_scale must be positive")

        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        session_options.intra_op_num_threads = int(
            config.get("intra_op_num_threads", 0)
        )
        self._torch_dll_directory = None
        self._cuda_dlls: list[Any] = []
        torch_spec = importlib.util.find_spec("torch")
        if (
            os.name == "nt"
            and torch_spec is not None
            and torch_spec.submodule_search_locations
        ):
            torch_lib = Path(next(iter(torch_spec.submodule_search_locations))) / "lib"
            if torch_lib.is_dir():
                self._torch_dll_directory = os.add_dll_directory(str(torch_lib))
                # ORT's CUDA EP may look up NVRTC by module name even though
                # the DLL is bundled inside the PyTorch wheel.  Load it
                # explicitly so webcam-only flows do not silently fall back.
                for pattern in ("nvrtc-builtins64_*.dll", "nvrtc64_*.dll"):
                    for dll_path in sorted(torch_lib.glob(pattern)):
                        self._cuda_dlls.append(ctypes.WinDLL(str(dll_path)))
        # ORT can reuse the CUDA/cuDNN DLLs bundled with the CUDA PyTorch
        # wheel.  Preloading avoids depending on a system-wide CUDA toolkit.
        if hasattr(ort, "preload_dlls"):
            try:
                ort.preload_dlls(
                    directory=(
                        str(torch_lib)
                        if self._torch_dll_directory is not None
                        else None
                    )
                )
            except Exception:
                # Provider selection below remains authoritative and retains
                # a CPU fallback for non-NVIDIA deployment machines.
                pass
        available_providers = set(ort.get_available_providers())
        if "CUDAExecutionProvider" not in available_providers:
            raise RuntimeError(
                "Challenge 2 ONNX runtime requires CUDAExecutionProvider, "
                f"but available providers are: {ort.get_available_providers()}"
            )
        providers = ["CUDAExecutionProvider"]
        self.detector = _OnnxYuNetDetector(
            detector_path,
            providers,
            self.min_detection_confidence,
            float(config.get("nms_threshold", 0.3)),
            int(config.get("top_k", 5000)),
            int(config.get("intra_op_num_threads", 0)),
        )
        self.session = ort.InferenceSession(
            str(landmark_path),
            sess_options=session_options,
            providers=providers,
        )
        # Verify GPU session initialization
        active_providers = self.session.get_providers()
        if not any(p in active_providers for p in ("TensorrtExecutionProvider", "CUDAExecutionProvider")):
            raise RuntimeError(
                f"ONNX session did not initialize on GPU: {active_providers}"
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
        self.detector.close()
        self.session = None  # type: ignore[assignment]
        self.detector = None  # type: ignore[assignment]
        if self._torch_dll_directory is not None:
            self._torch_dll_directory.close()
            self._torch_dll_directory = None
        self._cuda_dlls.clear()

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

        run_detector = bool(
            self._tracked_face is None
            or self._frame_index % self.detector_interval_frames == 0
        )
        self._frame_index += 1
        face = self._tracked_face
        if run_detector:
            detected = self._detect_primary_face(frame_bgr)
            if detected is not None:
                face = detected
                self._tracked_face = detected
        if face is None:
            return None

        result = self._landmarks_from_face(frame_bgr, face)
        if result is None and not run_detector:
            # Tracking/ROI drifted: reacquire immediately rather than waiting
            # for the next scheduled YuNet frame.
            face = self._detect_primary_face(frame_bgr)
            if face is not None:
                result = self._landmarks_from_face(frame_bgr, face)
        if result is None:
            self._tracked_face = None
            return None

        xs = result.landmarks[:, 0] * width
        ys = result.landmarks[:, 1] * height
        x0 = float(np.clip(xs.min(), 0, width - 1))
        y0 = float(np.clip(ys.min(), 0, height - 1))
        x1 = float(np.clip(xs.max(), x0 + 1, width))
        y1 = float(np.clip(ys.max(), y0 + 1, height))
        self._tracked_face = np.asarray(
            [x0, y0, x1 - x0, y1 - y0, result.confidence],
            dtype=np.float32,
        )
        return result

    def _detect_primary_face(
        self, frame_bgr: np.ndarray
    ) -> np.ndarray | None:
        detections = self.detector.detect(frame_bgr)
        if detections is None or len(detections) == 0:
            return None
        face = max(
            detections,
            key=lambda row: float(row[2] * row[3] * max(row[-1], 0.0)),
        )
        if float(face[-1]) < self.min_detection_confidence:
            return None
        return np.asarray(face, dtype=np.float32).copy()

    def _landmarks_from_face(
        self, frame_bgr: np.ndarray, face: np.ndarray
    ) -> FaceLandmarkResult | None:
        height, width = frame_bgr.shape[:2]
        detection_confidence = float(face[-1])

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
