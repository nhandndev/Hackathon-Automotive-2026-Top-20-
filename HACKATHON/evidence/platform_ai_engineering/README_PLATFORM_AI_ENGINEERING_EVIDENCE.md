# Platform Utilization + AI Engineering Evidence Package

File này là evidence thật được collect từ source code, tests và artifact trong repo. Mục tiêu là chứng minh phần **AI Engineering capability được external consumer sử dụng qua interface hoặc artifact**, đồng thời nối với CarSky/HMI path.

## Evidence Summary

| Evidence | Chứng minh điều gì? | File output |
|---|---|---|
| DecisionEvent schema | AI capability có contract canonical, không phải text tự do | `raw/01_decision_event_schema.txt` |
| Backend boundary | SE Backend consume AI event qua API boundary | `raw/02_ai_backend_boundary_router.txt` |
| Backend -> CarSky mapper | CarSky integration consume AI/DMS state qua mapper | `raw/03_backend_to_carsky_mapper.txt` |
| CarSky script | Demo operator có script để push scenario critical/normal | `raw/04_carsky_phase05_script.txt` |
| Copilot Report API | User/report consume AI explanation qua `/api/copilot/report` | `raw/05_copilot_report_api.txt` |
| Word/DOC export | Report artifact được tạo để reviewer/business user consume | `raw/06_copilot_doc_export.txt` |
| Fleet Dashboard consumers | FE có views consume DecisionEvent/saved/local AI data | `raw/07_fleet_dashboard_consumers.txt` |
| Contract docs | AI/SE maintainer có docs làm contract và ownership boundary | `raw/08_contract_docs.txt` |
| Test source | Consumer flow có test source, không chỉ README | `raw/09_test_source_proves_consumers.txt` |
| Pytest result | Contract/alerts/CarSky tests chạy được trên source hiện tại | `raw/10_pytest_contract_carsky_alerts.txt` |
| Android HMI APK artifact | APK thật có CarProperty/HMI runtime strings | `raw/11_apk_hmi_artifact.txt` |

## External Consumer Proof

| External consumer | Interface / artifact họ consume | Evidence thật |
|---|---|---|
| SE Backend engineer | `/api/v1/alerts`, `/api/v1/alerts/snapshot`, `DecisionEventPayload` | `raw/02_ai_backend_boundary_router.txt`, `raw/10_pytest_contract_carsky_alerts.txt` |
| CarSky integration engineer | `CarSkySignalMapper`, `vehicle-speed-mux`, `carsky_phase05.py` | `raw/03_backend_to_carsky_mapper.txt`, `raw/04_carsky_phase05_script.txt`, `raw/10_pytest_contract_carsky_alerts.txt` |
| Fleet Manager | Fleet Dashboard views, saved/live trip context, DecisionEvent display | `raw/07_fleet_dashboard_consumers.txt` |
| AI Copilot report user | `/api/copilot/report`, validated/pending/unavailable fallback | `raw/05_copilot_report_api.txt` |
| Reviewer / business user | Word-compatible DOC report artifact | `raw/06_copilot_doc_export.txt` |
| AI/SE maintainer | AI contract docs + contract tests | `raw/08_contract_docs.txt`, `raw/09_test_source_proves_consumers.txt`, `raw/10_pytest_contract_carsky_alerts.txt` |
| Driver HMI / CarSky runtime | Android HMI APK reads CarProperty path | `raw/11_apk_hmi_artifact.txt` |

## Copy-Ready Claim

AI Engineering capability trong FPTU DMS Vision được external consumer sử dụng qua interface/artifact thật. AI core phát `DecisionEvent` và local telemetry contract; SE Backend consume qua `/api/v1/alerts`; CarSky integration consume qua `CarSkySignalMapper` và `carsky_phase05.py`; Fleet Manager consume qua Fleet Dashboard; AI Copilot report user consume qua `/api/copilot/report`; reviewer/business user consume qua Word/DOC export; AI/SE maintainer consume qua contract docs và pytest contract suite. Evidence nằm trong source, tests và APK artifact, không chỉ là mô tả trong slide.

## Caveat Đúng Sự Thật

Evidence này chứng minh source/test/artifact path. Với CarSky runtime, cần quay thêm same-event video nếu muốn claim full runtime chain: Backend publish -> Signal Watch `Vehicle.Speed` -> Bridge log -> Android logcat -> APK UI đổi cùng một event.
