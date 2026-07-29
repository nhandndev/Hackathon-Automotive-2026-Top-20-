"""Guided driver enrollment and profile estimation from DMS primitives."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from .driver_profile import DriverProfile


@dataclass(frozen=True)
class EnrollmentStep:
    key: str
    prompt: str
    minimum_duration_ms: int
    minimum_samples: int


DEFAULT_STEPS = (
    EnrollmentStep(
        "neutral", "Look forward and open eyes normally", 3000, 45
    ),
    EnrollmentStep("blink", "Blink naturally several times", 2500, 35),
    EnrollmentStep("left", "Turn your head LEFT and hold", 2000, 30),
    EnrollmentStep("right", "Turn your head RIGHT and hold", 2000, 30),
    EnrollmentStep("down", "Look slightly DOWN and hold", 2000, 30),
    EnrollmentStep("mouth", "Keep your mouth relaxed", 2000, 30),
    EnrollmentStep("yawn", "Simulate a moderate YAWN and hold", 2500, 35),
    EnrollmentStep(
        "closed", "Close eyes safely for 1.2-1.5 seconds", 1800, 25
    ),
)


@dataclass(frozen=True)
class EnrollmentStatus:
    step: EnrollmentStep | None
    progress: float
    ready: bool
    valid_samples: int
    elapsed_ms: int
    step_number: int
    total_steps: int
    action_detected: bool
    evidence: str


def _feature(row: dict[str, Any], name: str) -> float | None:
    try:
        value = float(row.get("features", {}).get(name))
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


class EnrollmentAccumulator:
    """Collect only numeric primitives; frames are never retained."""

    def __init__(self) -> None:
        self.samples: dict[str, list[dict[str, float]]] = defaultdict(list)

    def add(self, phase: str, row: dict[str, Any]) -> bool:
        observation = row.get("observation", {})
        if not observation.get("face_detected"):
            return False
        if observation.get("head_pose_valid") is False:
            return False
        values = {
            name: _feature(row, name)
            for name in (
                "ear_robust",
                "mar",
                "raw_yaw_deg",
                "raw_pitch_deg",
                "raw_roll_deg",
            )
        }
        if any(value is None for value in values.values()):
            return False
        self.samples[phase].append(values)  # type: ignore[arg-type]
        return True

    def _values(self, phases: tuple[str, ...], key: str) -> np.ndarray:
        return np.asarray(
            [
                sample[key]
                for phase in phases
                for sample in self.samples.get(phase, [])
            ],
            dtype=float,
        )

    def build_profile(
        self,
        driver_id: str,
        eye_closure_threshold: float = 0.72,
    ) -> DriverProfile:
        required = (
            "neutral",
            "blink",
            "left",
            "right",
            "down",
            "mouth",
            "yawn",
            "closed",
        )
        missing = [phase for phase in required if len(self.samples[phase]) < 3]
        if missing:
            raise ValueError(
                "Enrollment has insufficient valid face samples for: "
                + ", ".join(missing)
            )

        open_ears = self._values(("neutral", "mouth"), "ear_robust")
        closed_ears = self._values(("closed",), "ear_robust")
        neutral_mars = self._values(("neutral", "mouth"), "mar")
        yawn_mars = self._values(("yawn",), "mar")
        ear_open = float(np.median(open_ears))
        ear_closed = float(np.quantile(closed_ears, 0.20))
        mar_neutral = float(np.median(neutral_mars))
        # A midpoint is a more useful runtime threshold than the yawn peak.
        yawn_peak = float(np.quantile(yawn_mars, 0.75))
        mar_yawn = max(
            mar_neutral + 0.02,
            mar_neutral + 0.55 * (yawn_peak - mar_neutral),
        )
        if ear_open - ear_closed < 0.025:
            raise ValueError(
                "Open/closed eye samples are not sufficiently separated"
            )
        if yawn_peak - mar_neutral < 0.03:
            raise ValueError(
                "Neutral/yawn mouth samples are not sufficiently separated"
            )

        neutral = self.samples["neutral"]
        yaw_left = self._values(("left",), "raw_yaw_deg")
        yaw_right = self._values(("right",), "raw_yaw_deg")
        neutral_yaw = self._values(("neutral",), "raw_yaw_deg")
        neutral_pitch = self._values(("neutral",), "raw_pitch_deg")
        down_pitch = self._values(("down",), "raw_pitch_deg")
        blink_ears = self._values(("blink",), "ear_robust")
        pose_range = abs(float(np.median(yaw_left) - np.median(yaw_right)))
        left_delta = float(np.median(yaw_left) - np.median(neutral_yaw))
        right_delta = float(np.median(yaw_right) - np.median(neutral_yaw))
        pitch_range = float(
            np.median(down_pitch) - np.median(neutral_pitch)
        )
        blink_drop = ear_open - float(np.quantile(blink_ears, 0.10))
        if left_delta > -5.0 or right_delta < 5.0 or pose_range < 10.0:
            raise ValueError(
                "Left/right head samples do not show opposite directions"
            )
        if pitch_range < 4.0:
            raise ValueError(
                "Neutral/down head samples are not sufficiently separated"
            )
        if blink_drop < 0.01:
            raise ValueError(
                "Natural blink was not observed during enrollment"
            )
        sample_score = min(
            1.0, min(len(self.samples[p]) for p in required) / 20.0
        )
        eye_score = min(1.0, (ear_open - ear_closed) / 0.12)
        mouth_score = min(1.0, (yawn_peak - mar_neutral) / 0.25)
        pose_score = min(
            1.0, 0.7 * pose_range / 30.0 + 0.3 * pitch_range / 15.0
        )
        quality = float(
            np.clip(
                0.35 * sample_score
                + 0.30 * eye_score
                + 0.20 * mouth_score
                + 0.15 * pose_score,
                0.0,
                1.0,
            )
        )
        if quality < 0.35:
            raise ValueError(
                f"Enrollment quality is too low ({quality:.2f}); retry"
            )
        return DriverProfile.create(
            driver_id,
            ear_open=round(ear_open, 6),
            ear_closed=round(ear_closed, 6),
            mar_neutral=round(mar_neutral, 6),
            mar_yawn=round(mar_yawn, 6),
            neutral_yaw_deg=round(
                float(np.median([x["raw_yaw_deg"] for x in neutral])), 4
            ),
            neutral_pitch_deg=round(
                float(np.median([x["raw_pitch_deg"] for x in neutral])), 4
            ),
            neutral_roll_deg=round(
                float(np.median([x["raw_roll_deg"] for x in neutral])), 4
            ),
            eye_closure_threshold=float(eye_closure_threshold),
            quality_score=round(quality, 4),
        )


class GuidedEnrollment:
    """User-confirmed enrollment: each valid step advances only on Space."""

    def __init__(
        self,
        driver_id: str,
        steps: tuple[EnrollmentStep, ...] = DEFAULT_STEPS,
    ) -> None:
        self.driver_id = driver_id
        self.steps = steps
        self.accumulator = EnrollmentAccumulator()
        self.current_index = 0
        self.step_started_ms: int | None = None

    @property
    def complete(self) -> bool:
        return self.current_index >= len(self.steps)

    def _semantic_evidence(
        self,
        step: EnrollmentStep,
    ) -> tuple[bool, str]:
        """Return whether the gesture is visible and a UI-facing reason."""
        samples = self.accumulator.samples
        current = samples[step.key]
        if not current:
            return False, "No valid face/landmark sample"
        if step.key == "neutral":
            yaw_std = float(
                np.std([item["raw_yaw_deg"] for item in current])
            )
            detected = yaw_std <= 6.0
            return detected, f"head stability {yaw_std:.1f} deg (need <= 6.0)"
        if not samples["neutral"]:
            return False, "Neutral baseline is missing"
        neutral_ear = float(
            np.median([item["ear_robust"] for item in samples["neutral"]])
        )
        neutral_mar = float(
            np.median(
                [
                    item["mar"]
                    for phase in ("neutral", "mouth")
                    for item in samples[phase]
                ]
            )
        )
        neutral_yaw = float(
            np.median([item["raw_yaw_deg"] for item in samples["neutral"]])
        )
        neutral_pitch = float(
            np.median(
                [item["raw_pitch_deg"] for item in samples["neutral"]]
            )
        )
        if step.key == "mouth":
            current_mar = float(
                np.median([item["mar"] for item in current])
            )
            delta = current_mar - neutral_mar
            detected = abs(delta) <= 0.05
            return detected, (
                f"relaxed MAR delta {delta:+.3f} (need within +/-0.050)"
            )
        if step.key == "blink":
            drop = neutral_ear - float(
                np.quantile(
                    [item["ear_robust"] for item in current], 0.10
                )
            )
            return drop >= 0.01, f"EAR drop {drop:.3f} (need >= 0.010)"
        if step.key == "left":
            current_yaw = float(
                np.median([item["raw_yaw_deg"] for item in current])
            )
            delta = current_yaw - neutral_yaw
            return delta <= -5.0, (
                f"signed yaw delta {delta:+.1f} deg (LEFT needs <= -5.0)"
            )
        if step.key == "right":
            if not samples["left"]:
                return False, "Left-turn reference is missing"
            left_yaw = float(
                np.median(
                    [item["raw_yaw_deg"] for item in samples["left"]]
                )
            )
            right_yaw = float(
                np.median([item["raw_yaw_deg"] for item in current])
            )
            right_delta = right_yaw - neutral_yaw
            separation = abs(right_yaw - left_yaw)
            detected = right_delta >= 5.0 and separation >= 10.0
            return detected, (
                f"yaw {right_delta:+.1f}, separation {separation:.1f} "
                "(RIGHT needs >= +5.0)"
            )
        if step.key == "down":
            current_pitch = float(
                np.median([item["raw_pitch_deg"] for item in current])
            )
            delta = current_pitch - neutral_pitch
            return delta >= 4.0, (
                f"signed pitch delta {delta:+.1f} deg (DOWN needs >= +4.0)"
            )
        if step.key == "yawn":
            current_mar = float(
                np.quantile([item["mar"] for item in current], 0.75)
            )
            delta = current_mar - neutral_mar
            return delta >= 0.03, (
                f"MAR increase {delta:.3f} (need >= 0.030)"
            )
        if step.key == "closed":
            current_ear = float(
                np.quantile([item["ear_robust"] for item in current], 0.20)
            )
            drop = neutral_ear - current_ear
            return drop >= 0.025, (
                f"EAR drop {drop:.3f} (need >= 0.025)"
            )
        return True, "Feature observed"

    def status(self, timestamp_ms: int) -> EnrollmentStatus:
        if self.complete:
            return EnrollmentStatus(
                None,
                1.0,
                True,
                0,
                0,
                len(self.steps),
                len(self.steps),
                True,
                "Enrollment complete",
            )
        if self.step_started_ms is None:
            self.step_started_ms = timestamp_ms
        step = self.steps[self.current_index]
        elapsed = max(0, timestamp_ms - self.step_started_ms)
        valid = len(self.accumulator.samples[step.key])
        time_progress = elapsed / max(1, step.minimum_duration_ms)
        sample_progress = valid / max(1, step.minimum_samples)
        semantic_ready, evidence = self._semantic_evidence(step)
        ready = (
            time_progress >= 1.0
            and sample_progress >= 1.0
            and semantic_ready
        )
        progress = min(1.0, time_progress, sample_progress)
        if not semantic_ready and progress >= 1.0:
            progress = 0.99
        return EnrollmentStatus(
            step=step,
            progress=progress,
            ready=ready,
            valid_samples=valid,
            elapsed_ms=elapsed,
            step_number=self.current_index + 1,
            total_steps=len(self.steps),
            action_detected=semantic_ready,
            evidence=evidence,
        )

    def observe(self, row: dict[str, Any], timestamp_ms: int) -> bool:
        status = self.status(timestamp_ms)
        if status.step is None:
            return False
        return self.accumulator.add(status.step.key, row)

    def advance(self, timestamp_ms: int) -> bool:
        """Accept the current feature only if its quality gate is ready."""
        status = self.status(timestamp_ms)
        if status.step is None:
            return True
        if not status.ready:
            return False
        self.current_index += 1
        self.step_started_ms = timestamp_ms
        return True

    def retry_current(self, timestamp_ms: int) -> None:
        """Discard only the current feature samples and restart its gate."""
        if self.complete:
            return
        step = self.steps[self.current_index]
        self.accumulator.samples[step.key].clear()
        self.step_started_ms = timestamp_ms

    def build_profile(self, eye_closure_threshold: float) -> DriverProfile:
        return self.accumulator.build_profile(
            self.driver_id, eye_closure_threshold
        )
