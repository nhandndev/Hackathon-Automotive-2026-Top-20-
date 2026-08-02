"""BTC Challenge 3 trip-level Fleet Safe Driving Score.

This mirrors the public evaluator's BehaviorScorer reconstruction exactly:

safe = 100 - (
    harsh_brake_count * 3
    + harsh_accel_count * 2
    + harsh_corner_count * 2
    + near_miss_count * 5
    + speeding_pct_time * 0.15
)

The original tailgating term is intentionally absent because the BTC CSV
contract has no predicted_headway_sec field and the public evaluator omits it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

HARSH_BRAKE_G = 0.40
HARSH_ACCEL_G = 0.35
HARSH_LATERAL_G = 0.30
G_MS2 = 9.81
NEAR_MISS_TTC_SEC = 1.5
SPEEDING_TOLERANCE_KMH = 5.0

HARSH_BRAKE_PENALTY = 3.0
HARSH_ACCEL_PENALTY = 2.0
HARSH_CORNER_PENALTY = 2.0
NEAR_MISS_PENALTY = 5.0
SPEEDING_MAX_PENALTY = 15.0


@dataclass(frozen=True)
class FleetScoreSnapshot:
    """Causal aggregate after all frames observed so far."""

    frames_seen: int
    harsh_brake_count: int
    harsh_accel_count: int
    harsh_corner_count: int
    near_miss_count: int
    speeding_frames: int
    speeding_pct_time: float
    penalty_points: float
    safe_driving_score: float
    risk_score: float


class FleetSafeDrivingScorer:
    """Incrementally reconstruct the BTC Challenge 3 score for one trip."""

    def __init__(self, speed_limit_kmh: float) -> None:
        self.speed_limit_kmh = float(speed_limit_kmh)
        if not math.isfinite(self.speed_limit_kmh):
            raise ValueError("speed_limit_kmh must be finite")
        self.reset()

    def reset(self) -> None:
        self.frames_seen = 0
        self.harsh_brake_count = 0
        self.harsh_accel_count = 0
        self.harsh_corner_count = 0
        self.near_miss_count = 0
        self.speeding_frames = 0

    def update(
        self,
        predicted_ttc: float,
        speed_kmh: float,
        longitudinal_accel: float,
        lateral_accel: float,
    ) -> FleetScoreSnapshot:
        """Consume one frame in timestamp order and return the running score."""
        self.frames_seen += 1
        if longitudinal_accel < -HARSH_BRAKE_G * G_MS2:
            self.harsh_brake_count += 1
        if longitudinal_accel > HARSH_ACCEL_G * G_MS2:
            self.harsh_accel_count += 1
        if abs(lateral_accel) > HARSH_LATERAL_G * G_MS2:
            self.harsh_corner_count += 1
        if (
            math.isfinite(predicted_ttc)
            and predicted_ttc < NEAR_MISS_TTC_SEC
        ):
            self.near_miss_count += 1
        if speed_kmh > self.speed_limit_kmh + SPEEDING_TOLERANCE_KMH:
            self.speeding_frames += 1
        return self.snapshot()

    def snapshot(self) -> FleetScoreSnapshot:
        speeding_pct = (
            100.0 * self.speeding_frames / self.frames_seen
            if self.frames_seen
            else 0.0
        )
        penalties = (
            self.harsh_brake_count * HARSH_BRAKE_PENALTY
            + self.harsh_accel_count * HARSH_ACCEL_PENALTY
            + self.harsh_corner_count * HARSH_CORNER_PENALTY
            + self.near_miss_count * NEAR_MISS_PENALTY
            + (speeding_pct / 100.0) * SPEEDING_MAX_PENALTY
        )
        safe_score = max(0.0, min(100.0, 100.0 - penalties))
        return FleetScoreSnapshot(
            frames_seen=self.frames_seen,
            harsh_brake_count=self.harsh_brake_count,
            harsh_accel_count=self.harsh_accel_count,
            harsh_corner_count=self.harsh_corner_count,
            near_miss_count=self.near_miss_count,
            speeding_frames=self.speeding_frames,
            speeding_pct_time=round(speeding_pct, 3),
            penalty_points=round(penalties, 3),
            safe_driving_score=round(safe_score, 3),
            risk_score=round(100.0 - safe_score, 3),
        )
