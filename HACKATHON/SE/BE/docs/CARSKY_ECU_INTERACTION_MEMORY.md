# CarSky ECU interaction memory/runbook

File này lưu lại hướng xử lý feature “tương tác với 1 ECU” cho DMS Driver Safety HMI. Mục tiêu là để lần sau AI Agent hoặc thành viên SE đọc vào là biết nên làm mức nào, cần sửa VSS gì, deploy ra sao, và tránh lặp lại lỗi KUKSA/VSS.

## 1. Mentor nói “thêm tương tác với 1 ECU” nghĩa là gì

Không chỉ hiển thị cảnh báo trên HMI, hệ thống nên có thêm một output/command gửi tới một ECU hoặc ECU giả lập.

Luồng mong muốn:

```text
AI phát hiện nguy hiểm
  ↓
Backend normalize risk/driver/TTC
  ↓
Backend publish DMS signal
  ↓
HMI hiển thị cảnh báo
  ↓
ECU/ECU giả lập nhận command
```

Ví dụ ECU có thể là:

- Brake Assist ECU.
- Body ECU/Hazard Light.
- Cabin Warning/Buzzer ECU.
- Seatbelt/Haptic ECU.

Với hackathon/demo, ECU có thể là simulated ECU bằng KUKSA signal hoặc Script Node log. Không bắt buộc phải có ECU vật lý.

## 2. Nên làm sau hay làm ngay?

Khuyến nghị hiện tại: làm sau khi demo HMI đã ổn định.

Lý do:

- HMI + KUKSA + CarSky deploy đã từng mất nhiều thời gian do lỗi VSS artifact và Android custom VHAL.
- Nếu thêm VSS signal mới, có thể phải upload artifact mới và deploy lại Blueprint.
- Deploy lại có rủi ro làm hỏng trạng thái đang Running `3/3`.
- Bản nhanh hiện tại đã có thể nói “simulated ECU action” trên HMI dựa vào `RecommendedActionCode` và `CriticalAlert`.

Nên làm theo thứ tự:

```text
1. Giữ demo HMI đang chạy.
2. Ghi nhận ECU interaction hiện tại ở mức UI + existing signal.
3. Nếu còn thời gian, nâng lên ECU signals riêng.
4. Nếu còn rất nhiều thời gian, thêm Simulated ECU node/log riêng.
```

## 3. Ba mức chứng minh ECU interaction

### Mức 1 — Nhanh nhất, không deploy lại VSS

Dùng signal hiện có:

```text
Vehicle.ADAS.RecommendedActionCode = BRAKE_SAFE
Vehicle.ADAS.CriticalAlert = true
Vehicle.ADAS.DisplaySeverity = CRITICAL
```

HMI suy ra:

```text
ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

Chứng minh khi demo:

- Signal Watch bên phải có:
  - `Vehicle.ADAS.RecommendedActionCode = BRAKE_SAFE`
  - `Vehicle.ADAS.CriticalAlert = true`
  - `Vehicle.ADAS.DisplaySeverity = CRITICAL`
- HMI hiển thị ECU action tương ứng.

Cách giải thích:

```text
Trong demo hiện tại, RecommendedActionCode đóng vai trò ADAS/ECU command.
Khi AI phát hiện critical, Backend không chỉ đổi UI mà còn publish command BRAKE_SAFE.
HMI và Signal Watch cùng xác nhận command này.
```

Ưu điểm:

- Không cần sửa VSS.
- Không cần deploy lại.
- Ít rủi ro nhất.

Nhược điểm:

- Mentor có thể nói đây vẫn là “command signal”, chưa phải ECU riêng biệt.

### Mức 2 — Nên làm nếu còn thời gian: thêm ECU command signals riêng

Thêm các VSS path riêng:

```text
Vehicle.ADAS.BrakeAssistRequest
Vehicle.Cabin.WarningBuzzer
Vehicle.Body.HazardLight
Vehicle.Cabin.SeatbeltHapticWarning
```

Khi `WARNING`:

```text
Vehicle.Cabin.WarningBuzzer = true
Vehicle.Cabin.SeatbeltHapticWarning = true
Vehicle.ADAS.BrakeAssistRequest = false
Vehicle.Body.HazardLight = false
```

Khi `CRITICAL`:

```text
Vehicle.Cabin.WarningBuzzer = true
Vehicle.Cabin.SeatbeltHapticWarning = true
Vehicle.ADAS.BrakeAssistRequest = true
Vehicle.Body.HazardLight = true
```

Khi `SAFE/RECOVERY END`:

```text
Vehicle.Cabin.WarningBuzzer = false
Vehicle.Cabin.SeatbeltHapticWarning = false
Vehicle.ADAS.BrakeAssistRequest = false
Vehicle.Body.HazardLight = false
```

Chứng minh khi demo:

- Signal Watch thấy ECU command signals đổi `true/false`.
- HMI hiển thị ECU action.
- Backend log/audit ghi đã publish ECU command.

Ưu điểm:

- Rõ hơn mức 1.
- Mentor khó bắt bẻ hơn vì có signal ECU riêng.

Nhược điểm:

- Cần sửa VSS artifact.
- Cần upload artifact mới lên CarSky.
- Có thể cần deploy lại Blueprint.

### Mức 3 — Đẹp nhất: thêm Simulated ECU node/log

Tạo thêm node giả lập:

```text
DMS Signal Broker
  ↓ KUKSA
Simulated ECU Script Node
  ↓ log/action
HMI/Signal Watch
```

Node này subscribe ECU command signals:

```lua
pins.kuksa:subscribe({
  "Vehicle.ADAS.BrakeAssistRequest",
  "Vehicle.Cabin.WarningBuzzer",
  "Vehicle.Body.HazardLight",
  "Vehicle.Cabin.SeatbeltHapticWarning"
})

pins.kuksa:on_change(function(ev)
  log(string.format("SIM_ECU received %s=%s", ev.path, tostring(ev.value)))
end)
```

Chứng minh khi demo:

- HMI đổi cảnh báo.
- Signal Watch đổi command.
- Logs của Simulated ECU node hiện:

```text
SIM_ECU received Vehicle.ADAS.BrakeAssistRequest=true
SIM_ECU received Vehicle.Body.HazardLight=true
```

Ưu điểm:

- Thuyết phục nhất.
- Có “ECU consumer” riêng, không chỉ HMI text.

Nhược điểm:

- Tốn thời gian hơn.
- Cần tạo/sửa Blueprint.
- Có rủi ro deploy lại.

## 4. VSS cần thêm nếu làm mức 2/3

File đang dùng:

```text
SE/BE/carsky/dms-vss-signals.json
```

Quan trọng: KUKSA Databroker cần VSS dạng object/map `{...}`, không dùng array `[...]`.

Đã từng gặp lỗi:

```text
ParseError("invalid type: sequence, expected a map at line 1 column 1")
```

Nguyên nhân:

```json
[
  {"path": "Vehicle.Speed"}
]
```

Sai cho KUKSA.

Dạng đúng phải là:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {}
  }
}
```

### VSS proposal cho ECU signals

Thêm dưới `Vehicle.ADAS.children`:

```json
"BrakeAssistRequest": {
  "type": "actuator",
  "datatype": "boolean",
  "description": "Simulated Brake Assist ECU request from DMS critical alert."
}
```

Thêm dưới `Vehicle.Cabin.children`:

```json
"WarningBuzzer": {
  "type": "actuator",
  "datatype": "boolean",
  "description": "Simulated cabin buzzer request from DMS warning/critical alert."
},
"SeatbeltHapticWarning": {
  "type": "actuator",
  "datatype": "boolean",
  "description": "Simulated seatbelt/haptic warning request from DMS warning/critical alert."
}
```

Thêm dưới `Vehicle.Body.children`:

```json
"HazardLight": {
  "type": "actuator",
  "datatype": "boolean",
  "description": "Simulated body ECU hazard light request from DMS critical alert."
}
```

Nếu `Vehicle.Cabin` hoặc `Vehicle.Body` chưa tồn tại thì tạo branch:

```json
"Cabin": {
  "type": "branch",
  "description": "Cabin actuator signals for DMS demo.",
  "children": {}
}
```

```json
"Body": {
  "type": "branch",
  "description": "Body control actuator signals for DMS demo.",
  "children": {}
}
```

Validate local trước khi upload:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/BE/.venv/bin/python -m json.tool SE/BE/carsky/dms-vss-signals.json >/tmp/dms-vss-signals.validated.json
sed -n '1,20p' SE/BE/carsky/dms-vss-signals.json
```

Dòng đầu phải là:

```text
{
```

Không được là:

```text
[
```

## 5. Backend cần sửa gì nếu thêm ECU signals riêng

File script demo hiện tại:

```text
SE/BE/scripts/carsky_phase05.py
```

Thêm ECU signals vào các profile:

### `send-safe`

```json
{"path": "Vehicle.ADAS.BrakeAssistRequest", "value": false},
{"path": "Vehicle.Cabin.WarningBuzzer", "value": false},
{"path": "Vehicle.Body.HazardLight", "value": false},
{"path": "Vehicle.Cabin.SeatbeltHapticWarning", "value": false}
```

### `send-warning`

```json
{"path": "Vehicle.ADAS.BrakeAssistRequest", "value": false},
{"path": "Vehicle.Cabin.WarningBuzzer", "value": true},
{"path": "Vehicle.Body.HazardLight", "value": false},
{"path": "Vehicle.Cabin.SeatbeltHapticWarning", "value": true}
```

### `send-critical`

```json
{"path": "Vehicle.ADAS.BrakeAssistRequest", "value": true},
{"path": "Vehicle.Cabin.WarningBuzzer", "value": true},
{"path": "Vehicle.Body.HazardLight", "value": true},
{"path": "Vehicle.Cabin.SeatbeltHapticWarning", "value": true}
```

Sau khi gửi:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
.venv/bin/python scripts/carsky_phase05.py send-critical
```

Đọc lại:

```bash
.venv/bin/python scripts/carsky_phase05.py values
```

Mong muốn thấy:

```text
Vehicle.ADAS.BrakeAssistRequest = true
Vehicle.Cabin.WarningBuzzer = true
Vehicle.Body.HazardLight = true
Vehicle.Cabin.SeatbeltHapticWarning = true
```

## 6. CarSky deploy kinh nghiệm cần nhớ

### Trước khi deploy

- Đừng xóa device/deployment đang chạy ổn nếu chưa cần.
- Nếu phải deploy lại, nên clone blueprint hoặc tạo deployment mới để rollback.
- Kiểm tra artifact VSS bằng `json.tool`.
- Kiểm tra VSS root là object `{...}`.
- Đảm bảo KUKSA Broker chọn đúng artifact version mới.
- Đảm bảo Signal Watch trỏ đúng signal part:

```text
dms-signal-broker-signal
```

### Sau khi deploy

Chờ đủ:

```text
Running 3/3 nodes ready
```

Nếu pending quá lâu:

- mở Dashboard;
- xem node nào restart/error;
- mở log node đó.

Nếu Broker crash với parse error:

- gần như chắc là VSS artifact sai format.

Nếu HMI không đổi nhưng Signal Watch đổi:

- lỗi nằm ở HMI/app bridge, không phải Backend.

Nếu Signal Watch không đổi:

- kiểm tra `CARSKY_ROOM_ID`;
- kiểm tra `CARSKY_NODE_KEY`;
- kiểm tra signal path có tồn tại trong VSS artifact.

## 7. Cách demo với mentor khi chưa làm VSS ECU riêng

Nói như sau:

```text
Hiện tại bản demo dùng simulated ECU command layer.
Khi AI phát hiện critical, Backend publish `RecommendedActionCode=BRAKE_SAFE`
và `CriticalAlert=true` vào KUKSA.

HMI không chỉ đổi UI mà còn diễn giải command này thành ECU action:
Brake Assist Requested, Buzzer ON, Hazard ON.

Nếu cần chứng minh bằng ECU signal riêng, team đã có kế hoạch mở rộng thêm:
Vehicle.ADAS.BrakeAssistRequest,
Vehicle.Cabin.WarningBuzzer,
Vehicle.Body.HazardLight,
Vehicle.Cabin.SeatbeltHapticWarning.
```

Khi demo, mở cùng lúc:

- HMI Screen.
- Signal Watch bên phải.

Chỉ vào:

```text
Vehicle.ADAS.RecommendedActionCode = BRAKE_SAFE
Vehicle.ADAS.CriticalAlert = true
Vehicle.ADAS.DisplaySeverity = CRITICAL
```

rồi chỉ HMI:

```text
ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

## 8. Khi nào cần làm mức 2/3

Làm mức 2 nếu mentor/BTC hỏi:

```text
Signal ECU riêng đâu?
```

Làm mức 3 nếu họ hỏi:

```text
ECU consumer/node nhận command ở đâu?
```

Không nên làm mức 3 trước nếu thời gian gấp, vì dễ bị sa vào deploy/debug CarSky thêm lần nữa.

## 9. Nguyên tắc cho AI Agent sau này

- Đọc file này trước khi thêm ECU feature.
- Nếu demo đang chạy, không phá deploy đang Running.
- Ưu tiên mức 1 nếu cần demo ngay.
- Chỉ sửa VSS/upload/deploy lại khi có đủ thời gian rollback.
- Luôn validate `dms-vss-signals.json` bằng `json.tool`.
- Sau khi thêm signal mới, phải kiểm tra Signal Watch thấy path mới trước khi sửa HMI.
- Đừng gọi đây là ECU vật lý thật nếu chỉ là KUKSA simulated signal. Gọi đúng là `simulated ECU interaction`.

