# Evidence Outputs - Short Copy Version

---

# Output #004 - FleetDashBoard & Saved Trips

## Claim / outcome

Fleet Dashboard hiển thị saved trips, trip detail, ranking và insights từ JSON/local AI.

## Điều kiện xác định đạt

Dashboard load được saved trips, mở được các view chính và build/lint pass.

## Kết quả quan sát

Saved trips T01-T06 hiển thị được trên dashboard. Trip detail, insights và ranking hoạt động trong demo.

## Trạng thái

`IMPLEMENTED / VERIFIED IN DEMO`

## Evidence locator

[Video Evidence](https://drive.google.com/file/d/1O3Rkv2RfXXw1Pzmy1Oqb-5R3nWzQNbtv/view)

## Video timestamp

`00:20 - 00:30` Saved Trips  
`01:22 - 01:27` Insights  
`01:28 - 01:40` Ranking

## Caveat / giới hạn

Saved trips là demo/replay data, chưa thay thế live field pilot data. Hiện chưa chạy đồng thời full tất cả trip vì giới hạn phần cứng.

---

# Output #005 - AI Copilot Report, Fallback & Export

## Claim / outcome

AI Copilot Report hiển thị safety/maintenance report, giữ local baseline khi Bedrock chưa hợp lệ và hỗ trợ Word/DOC export.

## Điều kiện xác định đạt

Report mở được, fallback không hiển thị insight giả, và export report tải được.

## Kết quả quan sát

Report hiển thị được từ JSON/local AI. Khi Bedrock chưa hợp lệ, UI vẫn giữ số liệu local. Export report hoạt động trong demo.

## Trạng thái

`IMPLEMENTED WITH FALLBACK / DOC EXPORT VERIFIED IN DEMO`

## Evidence locator

[Video Evidence](https://drive.google.com/file/d/1O3Rkv2RfXXw1Pzmy1Oqb-5R3nWzQNbtv/view)

## Video timestamp

`01:41 - 02:41` Report  
`02:42 - 02:50` Export Report

## Caveat / giới hạn

Bedrock factual accuracy cần được audit thêm bằng golden-set. PDF không nằm trong final demo claim.

---

# Output #006 - Backend To CarSky To Android HMI

## Claim / outcome

Backend gửi DMS event sang CarSky/KUKSA, bridge qua VHAL và Android HMI hiển thị trạng thái tài xế.

## Điều kiện xác định đạt

Signal Watch nhận signal, bridge forward được dữ liệu và APK HMI đổi UI theo cùng event.

## Kết quả quan sát

Backend mapper, bridge script và Android APK artifact đã có. Runtime demo cần quay cùng một event từ Signal Watch đến APK UI.

## Trạng thái

`IMPLEMENTED / RUNTIME CHAIN EVIDENCE REQUIRED`

## Evidence locator

`SE/BE/app/integrations/carsky/mapper.py`  
`SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua`  
`SE/HMI/release/dms-hmi-realtime-vhal.apk`

## Video timestamp

`TBD`

## Caveat / giới hạn

Signal Watch đơn lẻ chưa chứng minh Android HMI end-to-end. Cần video cùng event gồm Signal Watch, bridge log, Android logcat và APK UI.

