# Source Report - E-04 Golden End-to-End Event Trace

| Evidence | Source | Ghi chú |
|---|---|---|
| `derived/golden_event.jsonl` | `tests/test_ai_alerts.py`, `carsky_phase05.py`, HMI bridge/APK source | Golden trace values, runtime command result and mapping path |
| `raw/backend_to_carsky_unit_trace.log` | `pytest` targeted tests | Verifies Backend creates expected CarSky speed-mux payloads |
| `raw/carsky_scenario_critical_command.json` | `scripts/carsky_phase05.py scenario critical` | Real runtime command output. If failed, file records failure honestly |
| `raw/source_snippets/golden_event_sources.log` | Source grep | Locates critical scenario, speed mux, bridge mapping and Android read path |
| `reports/trace_index.md` | Generated from artifacts | Reviewer map for what is verified vs missing |

## Kết quả

- Backend deterministic tests passed: `True`.
- CarSky runtime command returned ok: `True`.
- Screenshot evidence present: `False`.
- Video evidence present: `False`.

## Trạng thái

**PARTIAL / TEST AND RUNTIME COMMAND TRACE CREATED; VIDEO-SCREENSHOT SYNC STILL REQUIRED**

## Chưa làm

- Chưa có MP4 60-90s đặt trong `video/`.
- Chưa có screenshot đồng bộ đặt trong `screenshots/`.
- Chưa chứng minh cùng một event xuất hiện đồng thời trên Signal Watch, HMI Bridge log và Android HMI UI bằng file capture trong evidence folder này.
