# AI Output Contract, Compatibility và Change Log

> Đây là nguồn context chuẩn cho Backend, Frontend, CarSky và AI coding agent. Đọc file này trước khi sửa schema, mapper, WebSocket hoặc HMI. Phase CarSky liên quan: [`PHASE_05_2`](phases/PHASE_05_2_CARSKY_HMI_ACTION_CHECKLIST.md).

File này là **decision memory** của contract, không phải runtime log. Khi AI output thay đổi,
agent phải đọc file này và chỉ sửa phần bị ảnh hưởng; không triển khai lại toàn bộ các phase.

## 1. Contract version hiện hành

```text
AI_CONTRACT_VERSION=1.0.0
COMPATIBILITY_POLICY=additive
OWNER=AI team + Backend owner
```

Payload canonical là một trip:

```json
{
  "trip_id": "T01d",
  "metadata": {
    "trip_id": "T01d",
    "description": "DEBUG 30s: highway evening",
    "duration_sec": 90,
    "fps": 20,
    "map": "Town01",
    "driver_profile": "normal",
    "carla_version": "0.9.15",
    "random_seed": 1001,
    "speed_limit_kmh": 80
  },
  "frames": [
    {
      "frame_id": 0,
      "timestamp": 0.0,
      "ego": {
        "speed_kmh": 0.0,
        "longitudinal_accel": 0.0,
        "lateral_accel": 0.0,
        "geolocation": {"lat": -0.00123, "lon": -0.000485, "alt": 0.16}
      },
      "driver": {
        "state": "distracted",
        "alertness_score": 0.45,
        "eye_state": "open",
        "head_pose": "side",
        "mouth_state": "normal",
        "nthu_subject_id": "14"
      },
      "min_ttc": "Infinity",
      "headway_sec": "Infinity",
      "behavior_flags": {
        "harsh_brake": false,
        "harsh_accel": false,
        "harsh_corner": false,
        "speeding": false,
        "tailgating": false
      },
      "risk": {
        "base_risk": 0.0,
        "driver_factor": 2.2,
        "final_risk_score": 0.0
      }
    }
  ]
}
```

JSON boundary phải dùng chuỗi `"Infinity"`; literal JavaScript `Infinity` không phải JSON hợp lệ.

## 2. Phân loại field

### Bắt buộc ở trip

- `trip_id`
- `metadata.trip_id`
- `metadata.duration_sec`
- `metadata.fps`
- `metadata.speed_limit_kmh`
- `frames`

### Bắt buộc ở mỗi frame

- `frame_id`
- `timestamp`
- `ego.speed_kmh`
- `driver.state`
- `driver.alertness_score`
- `risk.final_risk_score`

### Optional/degradable

- `ego.longitudinal_accel`, `ego.lateral_accel`, `ego.geolocation`
- `driver.eye_state`, `driver.head_pose`, `driver.mouth_state`, `driver.nthu_subject_id`
- `min_ttc`, `headway_sec`
- từng `behavior_flags`
- `risk.base_risk`, `risk.driver_factor`
- metadata mô tả simulator

Schema Python Phase 01 hiện còn strict hơn danh sách compatibility này. Khi AI bắt đầu gửi thiếu optional field, Backend phải nới schema bằng default `None` trước khi nhận production payload.

## 3. Quy tắc thay đổi tương thích

| AI thay đổi | Backend xử lý | Có cần làm lại CarSky? |
|---|---|---|
| Thêm field, không đổi tên field cũ | Giữ nguyên nhờ `extra=allow`, ghi audit | Không |
| Thiếu optional field | Nhận frame, đặt unavailable, ẩn widget tương ứng | Không |
| Thiếu required field | Từ chối frame, giữ last-known-good có TTL, báo DEGRADED | Không |
| Đổi kiểu nhưng chuyển đổi an toàn được | Normalize ở adapter, ghi warning | Không |
| Đổi tên field | Breaking change; thêm alias/versioned mapper | Chỉ sửa mapping bị ảnh hưởng |
| Thêm field cần hiển thị | Thêm mapping, VSS path/version và HMI component | Update artifact/Blueprint, không dựng lại từ đầu |
| Bỏ field đang hiển thị | HMI ẩn giá trị, Backend báo unavailable | Không nếu VSS path vẫn giữ |

Field mới mặc định không tự xuất hiện trên HMI. Chỉ đưa lên HMI khi có quyết định UX rõ ràng.

## 4. Quy tắc dữ liệu đặc biệt

- `driver.state`: `alert|drowsy|yawning|distracted|microsleep`.
- `alertness_score`: `0..1`.
- risk scores: `0..100`.
- `min_ttc`/`headway_sec`: số không âm hoặc `"Infinity"`/`"inf"` khi input.
- Từ chối `NaN` và `-Infinity`.
- Không bao giờ biến Infinity thành `0`.
- Không tính lại hoặc ghi đè `risk.final_risk_score`.
- Root `trip_id` phải bằng `metadata.trip_id`.
- Extra fields phải được giữ khi round-trip.

## 5. Mapping AI → CarSky HMI v1

| AI/Backend source | VSS path | Khi thiếu/Infinity |
|---|---|---|
| `driver.state` | `Vehicle.Driver.State` | frame invalid nếu thiếu |
| `driver.alertness_score` | `Vehicle.Driver.AlertnessScore` | frame invalid nếu thiếu |
| `ego.speed_kmh` | `Vehicle.Speed` | frame invalid nếu thiếu |
| `metadata.speed_limit_kmh` | `Vehicle.SpeedLimit` | unavailable |
| `min_ttc` | `Vehicle.ADAS.MinTTC` | không publish value; HMI ẩn TTC |
| `headway_sec` | `Vehicle.ADAS.Headway` | không publish value; HMI ẩn headway |
| `risk.final_risk_score` | `Vehicle.ADAS.FinalRiskScore` | frame invalid nếu thiếu |
| enrichment | `Vehicle.ADAS.CriticalAlert` | `false` khi no active episode |
| enrichment | `Vehicle.ADAS.DisplaySeverity` | `SAFE|WARNING|CRITICAL|RECOVERY` |
| enrichment | `Vehicle.ADAS.AlertReasonCode` | enum deterministic |
| enrichment | `Vehicle.ADAS.RecommendedActionCode` | enum deterministic |
| enrichment | `Vehicle.ADAS.EventTransition` | `NONE|START|UPDATE|END` |
| source state | `Vehicle.ADAS.AIStatus` | `ONLINE|DEGRADED|OFFLINE` |
| receive time | `Vehicle.ADAS.DataAgeMs` | integer không âm |

CarSky không nhận toàn bộ raw AI frame. Backend chỉ gửi signal dành cho người lái và lifecycle cảnh báo.

## 6. Runtime audit log

Audit chạy thật dùng JSON Lines, không dùng Markdown:

```json
{"timestamp":"2026-07-25T12:00:00Z","trip_id":"T01d","frame_id":0,"contract_version":"1.0.0","missing_optional_fields":[],"extra_fields":[],"invalid_fields":[],"status":"accepted","carsky_publish_status":"not_requested"}
```

Các status:

- `accepted`
- `accepted_with_warnings`
- `rejected_required_field`
- `rejected_invalid_value`
- `carsky_queued`
- `carsky_delivered`
- `carsky_degraded`

Không ghi ảnh cabin, secret, access token hoặc payload chứa dữ liệu không cần thiết vào audit log.

## 7. Checklist khi AI output thay đổi

1. Lưu một fixture payload mới đã ẩn dữ liệu nhạy cảm.
2. So với contract v1 và liệt kê added/removed/type-changed fields.
3. Xác định required hay optional.
4. Sửa `app/domain/schemas/ai_contract.py` nếu schema nhận dữ liệu thay đổi.
5. Sửa CarSky mapper chỉ khi field dùng cho HMI thay đổi.
6. Thêm VSS artifact version nếu có path/type mới.
7. Sửa HMI chỉ khi người lái cần thấy field mới.
8. Chạy contract round-trip, invalid value và mapper tests.
9. Ghi một dòng trong Change Log dưới đây.

Không xoá Blueprint/Deployment chỉ vì payload thêm field.

### Phạm vi sửa tối thiểu

- Chỉ thêm field mới nhưng HMI không dùng: cập nhật fixture, contract test và Change Log.
- Optional field bị thiếu: cập nhật schema/default, audit warning và test degraded behavior.
- Field HMI đang dùng thay đổi kiểu/ý nghĩa: cập nhật adapter, mapper và test liên quan.
- Có signal mới cần đưa lên HMI: cập nhật mapper, VSS artifact, bridge và Android UI.
- Field cũ đổi tên: giữ alias tương thích trong ít nhất một contract version; không sửa trực tiếp mọi consumer.

Không cần chạy lại quy trình cài CarSky/Android cho thay đổi chỉ nằm trong payload raw. Chỉ
redeploy khi VSS, bridge hoặc APK thực sự thay đổi. Dù phạm vi sửa nhỏ, vẫn chạy toàn bộ test
Backend để phát hiện regression.

### Thông tin cần AI team cung cấp khi đổi output

```text
Ngày thay đổi:
Payload mẫu mới:
Field added:
Field removed/không còn bảo đảm:
Field đổi type/range/meaning:
Field nào cần hiển thị trên HMI:
Thời điểm payload mới bắt đầu được dùng:
```

## 8. Change Log

### 1.0.0 — 2026-07-25

- Khóa cấu trúc trip/metadata/frames được AI team cung cấp.
- Chốt Infinity string tại JSON boundary.
- Chốt additive compatibility và extra-field preservation.
- Chốt 14 VSS paths cho CarSky HMI v1.
- Chốt `risk.final_risk_score` là dữ liệu AI nguyên gốc.
