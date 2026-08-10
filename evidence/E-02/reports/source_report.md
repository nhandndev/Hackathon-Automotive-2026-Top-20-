# Source Report - E-02 AS-IS Architecture

| Evidence | Source | Ghi chú |
|---|---|---|
| `source_map.csv` | Repo source files listed per arrow | Maps each architecture arrow to file/function/status/caveat |
| `commands.log` | Commands run from `HACKATHON/` | Reproducible commands to inspect each arrow |
| `raw/source_snippets/*.log` | Command outputs from actual repo | Raw source/log evidence, not mock |
| `as_is_architecture.pdf` | Generated from verified source map | AS-IS diagram for report attachment |
| `manifest.json` | Generated at 2026-08-10T03:43:31Z, commit `44e6cb32` | Evidence metadata and not-claimed boundaries |

## AS-IS Flow Verified

```text
AI/local Decision Engine
  -> canonical DecisionEvent
  -> Backend /api/v1/alerts and live snapshot boundary
  -> Fleet Dashboard / AI Copilot Report
  -> CarSky mapper and REST Signal API
  -> KUKSA Vehicle.Speed speed-mux
  -> DMS HMI Bridge Script Node
  -> VHAL PERF_VEHICLE_SPEED 0x11600207
  -> Android CarPropertyManager
  -> DMS Android HMI APK
```

## Source Map Summary

| Arrow | Status | Evidence output |
|---|---|---|
| AI/local Decision Engine -> canonical DecisionEvent | SOURCE_VERIFIED | `raw/source_snippets/01_decision_event_schema.log` |
| DecisionEvent -> Backend REST ingestion boundary | SOURCE_AND_TEST_VERIFIED | `raw/source_snippets/02_backend_alert_boundary.log` |
| Backend alert boundary -> Fleet Dashboard live/saved context | SOURCE_VERIFIED | `raw/source_snippets/03_fleet_dashboard_flow.log` |
| Backend alert/live snapshot -> CarSky mapper | SOURCE_AND_TEST_VERIFIED | `raw/source_snippets/04_carsky_mapper.log` |
| CarSky mapper -> CarSky REST Signal API | SOURCE_AND_TEST_VERIFIED | `raw/source_snippets/05_carsky_rest_api.log` |
| CarSky Signal Broker/KUKSA Vehicle.Speed -> HMI Bridge Script Node | SOURCE_VERIFIED_RUNTIME_SCREENSHOT_PENDING | `raw/source_snippets/06_hmi_bridge.log` |
| HMI Bridge -> Android VHAL PERF_VEHICLE_SPEED | SOURCE_VERIFIED_RUNTIME_SCREENSHOT_PENDING | `raw/source_snippets/07_vhal_perf_vehicle_speed.log` |
| Android VHAL -> Android HMI APK UI | SOURCE_AND_APK_ARTIFACT_VERIFIED | `raw/source_snippets/08_android_hmi_carproperty.log` |
| Backend/FE -> AI Copilot Report -> Word/DOC artifact | SOURCE_VERIFIED | `raw/source_snippets/09_copilot_report_export.log` |

## Không Claim Trong E-02

- Không claim custom DMS CarProperty IDs là production-ready.
- Không claim automatic actuator control.
- Không claim multi-instance durable deployment.
- Không claim ROI/pilot/business validation.
- Không claim Bedrock là nguồn canonical metric; Bedrock/Copilot chỉ là explanation layer.

## Cần Bổ Sung Sign-Off

- Owner Nhân: xác nhận flow AS-IS đúng với phần Backend/Fleet/CarSky/HMI đã demo.
- Supporting Hùng: xác nhận AI/DecisionEvent boundary đúng với AI core.
- Nếu có runtime screenshot/video, attach vào E-04/E-24 và cross-link ở đây.

## Chưa Làm

- `as_is_architecture.pdf` đã generate từ source map, nhưng owner sign-off vẫn để pending.
- Chưa attach video same-event vào E-02; video thuộc E-04 golden trace.


## Audit correction - 2026-08-10T04:27:21Z

Hai arrow CarSky/HMI bridge trước đó dùng wording `SOURCE_AND_RUNTIME_SCREENSHOT_VERIFIED`. Audit lại folder `E-02/` cho thấy chưa có screenshot/runtime media nằm trực tiếp trong E-02, nên status đã được hạ xuống `SOURCE_VERIFIED_RUNTIME_SCREENSHOT_PENDING`. Runtime screenshot/video nếu có phải attach/link qua E-04 hoặc E-24 trước khi nâng status.
