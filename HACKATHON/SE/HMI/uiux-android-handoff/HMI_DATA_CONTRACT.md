# HMI data contract cho UI/UX

File này mô tả dữ liệu mà HMI cần hiển thị. Team UI/UX không cần hiểu toàn bộ Backend/AI, chỉ cần design đủ các field dưới đây.

## 1. State nội bộ của màn hình

Mỗi lần render, HMI sẽ có state dạng:

```json
{
  "aiStatus": "ONLINE",
  "severity": "WARNING",
  "driverState": "distracted",
  "recommendedAction": "FOCUS_FORWARD",
  "speedKmh": 75,
  "speedLimitKmh": 80,
  "riskScore": 55,
  "alertnessScore": 0.45,
  "minTtcSec": 3.0,
  "criticalAlert": false,
  "alertReasonCode": "DRIVER_DISTRACTED",
  "dataAgeMs": 40,
  "voiceEnabled": true,
  "ecuState": "WARNING_BUZZER_ON"
}
```

## 2. Severity

```text
SAFE
WARNING
CRITICAL
```

UI phải đổi màu/rõ trạng thái theo severity.

## 3. Driver state

```text
alert       → Tỉnh táo
drowsy      → Buồn ngủ
yawning     → Ngáp
distracted  → Mất tập trung
microsleep  → Vi ngủ
```

## 4. Recommended action

```text
NONE          → TIẾP TỤC QUAN SÁT
FOCUS_FORWARD → TẬP TRUNG PHÍA TRƯỚC
TAKE_BREAK    → HÃY NGHỈ NGƠI
BRAKE_SAFE    → PHANH AN TOÀN
REDUCE_SPEED  → GIẢM TỐC ĐỘ
```

## 5. AI status

```text
ONLINE
DEGRADED
OFFLINE
```

Gợi ý hiển thị:

- `AI ONLINE`: xanh.
- `AI DEGRADED`: vàng.
- `AI OFFLINE`: xám/đỏ nhẹ.

## 6. ECU state mô phỏng

Hiện tại ECU là mô phỏng để chứng minh HMI không chỉ hiển thị, mà có logic phản ứng hệ thống.

Mapping đề xuất:

```text
SAFE
→ ECU: STANDBY

WARNING
→ ECU: DRIVER WARNING BUZZER ON

CRITICAL
→ ECU: BRAKE ASSIST REQUESTED • HAZARD ON
```

UI nên có một dòng/card cho ECU.

## 7. VSS signal hiện dùng trong CarSky

Các signal hiện đã có trong KUKSA/CarSky:

```text
Vehicle.Speed
Vehicle.SpeedLimit
Vehicle.Driver.State
Vehicle.Driver.AlertnessScore
Vehicle.ADAS.MinTTC
Vehicle.ADAS.FinalRiskScore
Vehicle.ADAS.DisplaySeverity
Vehicle.ADAS.RecommendedActionCode
Vehicle.ADAS.AIStatus
Vehicle.ADAS.CriticalAlert
Vehicle.ADAS.AlertReasonCode
Vehicle.ADAS.DataAgeMs
```

UI không cần hiển thị hết. Nhưng không được làm mất các field quan trọng:

- severity.
- action.
- driver state.
- risk.
- speed.
- alertness.
- TTC.
- AI status.
- ECU state.

## 8. Sample states

### Safe

```json
{
  "aiStatus": "ONLINE",
  "severity": "SAFE",
  "driverState": "alert",
  "recommendedAction": "NONE",
  "speedKmh": 60,
  "speedLimitKmh": 80,
  "riskScore": 5,
  "alertnessScore": 0.95,
  "minTtcSec": 10,
  "criticalAlert": false,
  "alertReasonCode": "NONE",
  "dataAgeMs": 30,
  "voiceEnabled": true,
  "ecuState": "STANDBY"
}
```

### Warning

```json
{
  "aiStatus": "DEGRADED",
  "severity": "WARNING",
  "driverState": "distracted",
  "recommendedAction": "FOCUS_FORWARD",
  "speedKmh": 75,
  "speedLimitKmh": 80,
  "riskScore": 55,
  "alertnessScore": 0.45,
  "minTtcSec": 3,
  "criticalAlert": false,
  "alertReasonCode": "DRIVER_DISTRACTED",
  "dataAgeMs": 40,
  "voiceEnabled": true,
  "ecuState": "WARNING_BUZZER_ON"
}
```

### Critical

```json
{
  "aiStatus": "ONLINE",
  "severity": "CRITICAL",
  "driverState": "microsleep",
  "recommendedAction": "BRAKE_SAFE",
  "speedKmh": 80,
  "speedLimitKmh": 80,
  "riskScore": 88,
  "alertnessScore": 0.15,
  "minTtcSec": 1.2,
  "criticalAlert": true,
  "alertReasonCode": "TTC_CRITICAL",
  "dataAgeMs": 40,
  "voiceEnabled": true,
  "ecuState": "BRAKE_ASSIST_REQUESTED"
}
```
