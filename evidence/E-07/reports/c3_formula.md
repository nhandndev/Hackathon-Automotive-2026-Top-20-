# E-07 - Challenge 3 Formula / Thresholds

Source code: `HACKATHON/AI/core/challenge3_fusion/risk_engine.py`

Challenge 3 does not train an ML model. It computes a safe-driving score from the current source formula:

```text
safe_score = 100 - penalty
risk_score = 100 - safe_score

penalty =
  harsh_brake_count  * 3
+ harsh_accel_count  * 2
+ harsh_corner_count * 2
+ near_miss_count    * 5
+ speeding_pct_time  * 0.15
```

## Thresholds from source

| Event | Condition |
|---|---|
| Harsh brake | `longitudinal_accel < -0.40g` |
| Harsh accel | `longitudinal_accel > 0.35g` |
| Harsh corner | `abs(lateral_accel) > 0.30g` |
| Near miss | finite `predicted_ttc < 1.5s` |
| Speeding | `speed_kmh > speed_limit_kmh + 5.0` |

Constants:

```text
g = 9.81 m/s^2
HARSH_BRAKE_G = 0.40
HARSH_ACCEL_G = 0.35
HARSH_LATERAL_G = 0.30
NEAR_MISS_TTC_SEC = 1.5
SPEEDING_TOLERANCE_KMH = 5.0
```

## Source note

Tailgating is not included in the current CSV formula because the source notes that the BTC CSV contract has no `predicted_headway_sec`, and the public evaluator omits that term.
