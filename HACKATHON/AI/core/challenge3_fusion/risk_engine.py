"""Deterministic frame-level fusion used by CSV and demo inference."""
from __future__ import annotations

import math

DRIVER_RISK = {
    "alert": 0.0,
    "yawning": 30.0,
    "drowsy": 50.0,
    "distracted": 60.0,
    "microsleep": 90.0,
}


def predicted_risk_score(ttc: float, driver_state: str) -> float:
    if math.isfinite(ttc):
        ttc_risk = 100.0 * math.exp(-max(0.0, float(ttc)) / 3.0)
    else:
        ttc_risk = 0.0
    return round(max(ttc_risk, DRIVER_RISK.get(driver_state, 0.0)), 3)
