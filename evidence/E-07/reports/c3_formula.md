# E-07 - Challenge 3 Formula / Thresholds

Nguồn code: `HACKATHON/AI/core/challenge3_fusion/risk_engine.py`

Challenge 3 không train model ML. Nó tính điểm theo công thức BTC-style safe driving score.

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

## Thresholds

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

## Output meaning

- `safe_driving_score`: càng cao càng an toàn.
- `risk_score`: `100 - safe_driving_score`, càng cao càng rủi ro.
- `predicted_risk_score` trong CSV là risk tích lũy tại frame đó.

## Source note

Tailgating không nằm trong công thức CSV hiện tại vì BTC CSV contract không có `predicted_headway_sec`; code ghi rõ evaluator public cũng bỏ term này.
