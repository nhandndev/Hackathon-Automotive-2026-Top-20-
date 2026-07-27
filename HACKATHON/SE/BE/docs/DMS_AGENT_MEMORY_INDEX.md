# DMS Agent Memory Index

Đây là file đầu tiên AI Agent nên đọc khi Nhân hỏi về Backend, CarSky, HMI, AI realtime, ECU interaction hoặc update phase/docs. File này giúp nhớ đúng thứ tự xử lý, tránh làm lại từ đầu hoặc phá demo đang chạy.

## 1. Quy tắc đầu tiên

Trước khi sửa bất kỳ thứ gì liên quan CarSky/HMI:

1. Đọc file này.
2. Xác định yêu cầu thuộc nhóm nào.
3. Đọc đúng file memory/runbook tương ứng.
4. Không deploy lại CarSky/VSS nếu demo hiện tại đang chạy ổn, trừ khi Nhân yêu cầu rõ.
5. Không commit hoặc in secret/API key.

Nếu yêu cầu của Nhân là “làm nhanh để demo”, ưu tiên phương án ít rủi ro, không đụng deploy đang Running.

## 2. Bản đồ đọc file theo nhu cầu

| Nhân hỏi về | Đọc file nào trước | Mục tiêu |
|---|---|---|
| Update phase Backend tổng thể | `SE/BE/docs/README.md`, rồi `SE/BE/docs/phases/*.md` | Giữ kiến trúc phase nhất quán |
| AI realtime đã có rồi, nối vào HMI sao | `SE/BE/docs/AI_REALTIME_TO_CARSKY_HMI_MEMORY.md` | Nối AI frame → Backend normalize → CarSky/HMI |
| Chỉnh UI HMI | `SE/HMI/HMI_UI_CUSTOMIZATION_GUIDE.md` | Sửa layout/màu/chữ/voice/build APK |
| Thêm ECU interaction | `SE/BE/docs/CARSKY_ECU_INTERACTION_MEMORY.md` | Chọn mức 1/2/3, tránh deploy sai VSS |
| CarSky/KUKSA bị lỗi deploy/Broker | `SE/BE/docs/CARSKY_BROKER_FIX_GUIDE.md` | Debug VSS artifact, KUKSA Broker, deployment |
| Viết report gửi BTC | `SE/BE/docs/CARSKY_BTC_SUPPORT_REPORT.md` | Tổng hợp bằng chứng/lỗi/nhờ hỗ trợ |
| Làm Phase 05 CarSky | `SE/BE/docs/phases/PHASE_05_COPILOT_AND_CARSKY.md`, `PHASE_05_1...`, `PHASE_05_2...` | Theo đúng runbook phase |

## 3. Trạng thái demo đã đạt được

Tính tới lần ghi file này:

- CarSky deployment đã từng đạt `Running 3/3`.
- KUKSA Broker chạy được sau khi sửa VSS artifact dạng object/map.
- Signal Watch thấy 19 signals.
- Backend script gửi được signal:

```json
{"ok": true, "sent": 14}
```

- Signal Watch thấy các giá trị critical:

```text
Vehicle.ADAS.DisplaySeverity = CRITICAL
Vehicle.ADAS.RecommendedActionCode = BRAKE_SAFE
Vehicle.ADAS.CriticalAlert = true
Vehicle.Driver.State = microsleep
Vehicle.ADAS.FinalRiskScore = 88
Vehicle.ADAS.AIStatus = ONLINE
```

- APK HMI live demo đã cài được qua CarSky ADB.
- HMI hiển thị Safe/Warning/Critical.
- HMI có voice button.
- HMI có simulated ECU interaction line:

```text
ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

## 4. Những sự thật kỹ thuật đã xác nhận

### 4.1 KUKSA VSS phải là object/map

Sai:

```json
[
  {"path": "Vehicle.Speed"}
]
```

Đúng:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {}
  }
}
```

Lỗi từng gặp:

```text
ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

File VSS đang dùng:

```text
SE/BE/carsky/dms-vss-signals.json
```

Validate:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/BE/.venv/bin/python -m json.tool SE/BE/carsky/dms-vss-signals.json >/tmp/dms-vss-signals.validated.json
```

### 4.2 Không dùng custom Android VHAL cho demo hiện tại

Đã kiểm tra:

```sh
dumpsys car_service | grep -iE "557843456|559940617|559940618|555746306|555746307|555746308|555746309|291504647"
```

Kết quả Android chỉ expose:

```text
291504647 = PERF_VEHICLE_SPEED
```

Các custom DMS property không expose trong `CarPropertyService`, nên app đọc `CarPropertyManager` sẽ không đổi.

Vì vậy demo hiện tại dùng APK live đọc CarSky REST hoặc fallback demo cycle, không phụ thuộc custom Android VHAL.

### 4.3 Signal Watch không phải driver HMI

Signal Watch dùng để chứng minh signal đổi. Driver HMI là Android app trong Screen widget.

Demo tốt nhất mở cùng lúc:

- Screen widget: HMI cho driver.
- Signal Watch: bằng chứng KUKSA signal/command.
- ADB/log nếu cần debug.

## 5. Thứ tự xử lý khi Nhân hỏi “AI realtime có rồi”

Đọc:

```text
SE/BE/docs/AI_REALTIME_TO_CARSKY_HMI_MEMORY.md
```

Sau đó làm theo thứ tự:

1. Xác định AI push vào Backend hay Backend pull từ AI external API.
2. Validate AI frame bằng contract Phase 01.
3. Normalize frame thành HMI signal state.
4. Derive severity/action/lifecycle.
5. Publish CarSky KUKSA signals.
6. HMI đọc state.
7. Test Safe/Warning/Critical.
8. Ghi audit log.

Không làm:

- Không tính đè `risk.final_risk_score`.
- Không biến `Infinity` thành `0`.
- Không quay lại custom VHAL nếu chưa có bằng chứng `dumpsys car_service` expose đủ property.

## 6. Thứ tự xử lý khi Nhân hỏi “chỉnh UI”

Đọc:

```text
SE/HMI/HMI_UI_CUSTOMIZATION_GUIDE.md
```

Sau đó:

1. Sửa `SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java`.
2. Nếu chỉ đổi layout/màu/chữ: sửa `buildUi()` và `render(State s)`.
3. Nếu đổi action text: sửa `actionText(...)`.
4. Nếu đổi driver text: sửa `driverText(...)`.
5. Nếu đổi voice: sửa `maybeSpeak(...)`.
6. Tăng version code trong:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

7. Build:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/HMI/demo-live/build_demo_apk.sh
```

8. Regenerate/copy ADB script nếu cần:

```bash
pbcopy < SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

9. Nhờ Nhân paste vào CarSky ADB.

Expected:

```text
Success
Starting: Intent { cmp=vn.fpt.dms.hmi/.MainActivity }
```

## 7. Thứ tự xử lý khi Nhân hỏi “thêm ECU”

Đọc:

```text
SE/BE/docs/CARSKY_ECU_INTERACTION_MEMORY.md
```

Chọn mức theo thời gian:

### Nếu cần nhanh/demo ngay

Dùng mức 1:

```text
RecommendedActionCode = BRAKE_SAFE
CriticalAlert = true
DisplaySeverity = CRITICAL
```

HMI hiển thị simulated ECU:

```text
ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

Không sửa VSS, không deploy lại.

### Nếu mentor yêu cầu signal ECU riêng

Dùng mức 2:

Thêm VSS:

```text
Vehicle.ADAS.BrakeAssistRequest
Vehicle.Cabin.WarningBuzzer
Vehicle.Body.HazardLight
Vehicle.Cabin.SeatbeltHapticWarning
```

Cần:

1. Sửa `dms-vss-signals.json`.
2. Validate JSON.
3. Upload artifact mới.
4. Deploy lại/clone Blueprint.
5. Update `carsky_phase05.py` gửi thêm ECU signals.
6. Signal Watch xác nhận path mới.

### Nếu mentor yêu cầu ECU consumer/node

Dùng mức 3:

- Thêm Simulated ECU Script Node.
- Subscribe ECU signals.
- Log command nhận được.
- Demo bằng HMI + Signal Watch + ECU logs.

## 8. Thứ tự xử lý khi CarSky deploy lỗi

Đọc:

```text
SE/BE/docs/CARSKY_BROKER_FIX_GUIDE.md
```

Checklist:

1. Deployment có `Running 3/3` không?
2. Node nào fail/pending?
3. Broker log có parse error không?
4. VSS artifact là object `{...}` chưa?
5. Signal Watch có thấy paths chưa?
6. Backend `send-critical` có `ok=true` không?
7. Signal Watch có đổi value không?
8. HMI có đổi không?

Nếu:

```text
Signal Watch đổi nhưng HMI không đổi
```

thì lỗi nằm ở HMI/app, không phải Backend/KUKSA.

Nếu:

```text
send-critical ok=false hoặc Signal Watch không đổi
```

kiểm tra:

- `CARSKY_ROOM_ID`
- `CARSKY_NODE_KEY`
- path có tồn tại trong VSS không
- token/base URL

## 9. Những lệnh hay dùng

### Copy script cài HMI live

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
pbcopy < SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

### Gửi critical

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
.venv/bin/python scripts/carsky_phase05.py send-critical
```

### Đọc values

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
.venv/bin/python scripts/carsky_phase05.py values
```

### Check Android package

```sh
dumpsys package vn.fpt.dms.hmi | grep -iE "Activity|MainActivity|permission|version"
```

### Check Android custom VHAL

```sh
dumpsys car_service | grep -iE "557843456|559940617|559940618|555746306|555746307|555746308|555746309|291504647"
```

## 10. Cách nói với mentor/BTC

### Khi nói về HMI

```text
HMI không chỉ là Signal Watch. Signal Watch là công cụ debug.
Driver HMI là Android app chạy trong Skycraft Screen widget.
```

### Khi nói về ECU hiện tại

```text
Bản hiện tại dùng simulated ECU interaction.
AI critical làm Backend publish RecommendedActionCode=BRAKE_SAFE và CriticalAlert=true.
HMI diễn giải command này thành Brake Assist, Buzzer và Hazard action.
Nếu cần mức chứng minh cao hơn, team sẽ thêm VSS ECU command signals riêng hoặc Simulated ECU node.
```

### Khi nói về custom VHAL

```text
Team đã thử bridge KUKSA sang Android CarProperty, nhưng Android CarPropertyService hiện chỉ expose PERF_VEHICLE_SPEED, không expose custom DMS properties.
Vì vậy hướng demo nhanh là HMI đọc CarSky/Backend signal trực tiếp thay vì custom VHAL.
```

## 11. Không được quên

- Không xóa folder structure của Nhân.
- Không xóa code/docs khi chưa được yêu cầu rõ.
- Không thêm auth/security vào Backend nếu project đang chốt no-auth cho demo.
- Không làm mất deploy đang chạy ổn.
- Không commit/paste API key ra docs public.
- Khi bị lỗi, debug theo lớp:

```text
AI frame → Backend normalize → CarSky Signal Watch → HMI render → ADB/log
```

