# HMI UI customization guide

> Cập nhật realtime: source of truth hiện là
> `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java`. REST polling và
> mock fallback trong `demo-live` đã bị loại bỏ. Khi mất VHAL, UI phải hiện
> `AI OFFLINE`, không tự chạy chu kỳ trạng thái.

File này dùng cho lần sau khi cần chỉnh giao diện Android HMI demo trên CarSky. Đọc file này trước khi sửa UI để không phải dò lại từ đầu.

## 1. App HMI hiện tại nằm ở đâu

Source UI live demo:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

Build script:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

APK output:

```text
SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk
```

Script paste vào CarSky ADB:

```text
SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

Package Android:

```text
vn.fpt.dms.hmi
```

Activity:

```text
vn.fpt.dms.hmi/.MainActivity
```

## 2. Giao diện hiện tại đang làm gì

HMI hiển thị các thông tin chính:

- Trạng thái AI: `AI ONLINE`, `AI DEGRADED`, `AI OFFLINE`.
- Trạng thái cảnh báo:
  - `LÁI XE AN TOÀN`
  - `CẢNH BÁO`
  - `NGUY HIỂM`
- Hành động đề xuất:
  - `TIẾP TỤC QUAN SÁT`
  - `TẬP TRUNG PHÍA TRƯỚC`
  - `HÃY NGHỈ NGƠI`
  - `PHANH AN TOÀN`
  - `GIẢM TỐC ĐỘ`
- Evidence:
  - trạng thái tài xế;
  - TTC.
- Telemetry:
  - speed;
  - risk;
  - alertness.
- Simulated ECU interaction:
  - brake assist request;
  - warning buzzer;
  - hazard alert;
  - haptic warning.
- Nút voice:
  - `VOICE ON`;
  - `VOICE MUTED`.

## 3. Những hàm cần sửa khi chỉnh UI

File chính:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

### Chỉnh layout

Sửa hàm:

```java
buildUi()
```

Dùng để:

- thêm/bớt TextView;
- thêm card;
- chỉnh padding;
- chỉnh alignment;
- đổi nút voice;
- chia layout trái/phải;
- thêm icon hoặc status badge.

### Chỉnh màu sắc, chữ hiển thị, severity

Sửa hàm:

```java
render(State s)
```

Dùng để:

- đổi background theo Safe/Warning/Critical;
- đổi tiêu đề;
- đổi format telemetry;
- đổi nội dung evidence;
- đổi logic hiển thị AI status.

### Chỉnh text hành động

Sửa hàm:

```java
actionText(String action)
```

Mapping hiện tại:

```text
FOCUS_FORWARD → TẬP TRUNG PHÍA TRƯỚC
TAKE_BREAK    → HÃY NGHỈ NGƠI
BRAKE_SAFE    → PHANH AN TOÀN
REDUCE_SPEED  → GIẢM TỐC ĐỘ
NONE          → TIẾP TỤC QUAN SÁT
```

### Chỉnh text trạng thái tài xế

Sửa hàm:

```java
driverText(String driver)
```

Mapping hiện tại:

```text
alert       → Tỉnh táo
drowsy      → Buồn ngủ
yawning     → Ngáp
distracted  → Mất tập trung
microsleep  → Vi ngủ
```

### Chỉnh voice

Sửa hàm:

```java
maybeSpeak(int severity, String act)
```

Hiện tại:

- chỉ nói khi severity đổi;
- critical nói: `Nguy hiểm. <action>`;
- warning nói action.

Nếu muốn voice nói nhiều hơn, thêm nội dung tại đây.

## 4. Data contract mà UI đang đọc

App đọc state từ CarSky REST values hoặc fallback demo cycle.

Các field quan trọng:

```text
Vehicle.Speed
Vehicle.Driver.State
Vehicle.Driver.AlertnessScore
Vehicle.ADAS.MinTTC
Vehicle.ADAS.FinalRiskScore
Vehicle.ADAS.DisplaySeverity
Vehicle.ADAS.RecommendedActionCode
Vehicle.ADAS.AIStatus
```

Simulated ECU UI hiện chưa cần thêm VSS path riêng. Nó được suy ra từ:

```text
Vehicle.ADAS.DisplaySeverity
Vehicle.ADAS.RecommendedActionCode
Vehicle.ADAS.CriticalAlert
```

Mapping hiện tại:

```text
SAFE
→ ECU: STANDBY • ALL DRIVER ALERT ACTUATORS OFF

WARNING
→ ECU: DRIVER WARNING BUZZER ON • HAPTIC ALERT ON

CRITICAL hoặc BRAKE_SAFE
→ ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

UI state nội bộ:

```java
State(
  ai,
  severity,
  driver,
  action,
  speed,
  risk,
  alertness,
  ttc,
  critical
)
```

Nếu Backend/AI thêm field mới, không cần viết lại app từ đầu. Chỉ cần:

1. Thêm regex parse field đó.
2. Thêm property vào `State`.
3. Render ra UI trong `render(State s)`.

## 5. Build lại APK sau khi chỉnh UI

Chạy:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/HMI/demo-live/build_demo_apk.sh
```

Nếu build thành công sẽ thấy:

```text
SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk
```

## 6. Tạo lại script paste ADB

Sau khi build lại, cần regenerate script base64 để paste vào CarSky ADB.

Nếu script chưa tự regenerate, chạy lại đoạn này:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
python3 - <<'PY'
from pathlib import Path
import base64
root = Path('/Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON')
apk = root/'SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk'
out = root/'SE/HMI/install_hmi_live_via_carsky_adb_widget.sh'
b64 = base64.encodebytes(apk.read_bytes()).decode('ascii')
out.write_text(
    "cat > /data/local/tmp/dms_hmi_live.b64 <<'EOF'\n"
    + b64
    + "EOF\n"
    + "base64 -d /data/local/tmp/dms_hmi_live.b64 > /data/local/tmp/dms_hmi_live.apk\n"
    + "pm install -r -d -t /data/local/tmp/dms_hmi_live.apk\n"
    + "am force-stop vn.fpt.dms.hmi\n"
    + "am start -n vn.fpt.dms.hmi/.MainActivity\n",
    encoding='utf-8'
)
print(out)
PY
```

Copy vào clipboard:

```bash
pbcopy < SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

## 7. Cài lại trên CarSky

Trong CarSky:

1. Mở device `test` hoặc device đang deploy HMI.
2. Mở widget `DMS Android ADB`.
3. Đợi thấy:

```text
trout_arm64:/ $
```

4. Paste script bằng `Cmd + V`.
5. Kết quả đúng:

```text
Success
Starting: Intent { cmp=vn.fpt.dms.hmi/.MainActivity }
```

Nếu thấy lỗi:

```text
INSTALL_FAILED_VERSION_DOWNGRADE
```

tăng version code trong:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

Dòng:

```bash
--version-code 2
```

đổi thành số lớn hơn, ví dụ:

```bash
--version-code 3
```

Nếu thấy lỗi:

```text
INSTALL_FAILED_DEPRECATED_SDK_VERSION
```

đảm bảo build script có:

```bash
--min-sdk-version 29
--target-sdk-version 35
```

## 8. Test UI sau khi cài

Gửi critical signal:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
.venv/bin/python scripts/carsky_phase05.py send-critical
```

Màn hình mong muốn:

```text
AI ONLINE
NGUY HIỂM
PHANH AN TOÀN
Tài xế: Vi ngủ • TTC 1.2s
80 km/h Risk 88 Alertness 15%
```

Nếu Android VM không gọi REST CarSky được, app sẽ chạy fallback demo cycle:

```text
SAFE → WARNING → CRITICAL
```

Đây là fallback có chủ đích để demo không chết.

## 9. Ý tưởng UI có thể làm sau

Các ý tưởng dễ chỉnh:

- Thêm vòng halo quanh màn hình:
  - xanh cho Safe;
  - vàng cho Warning;
  - đỏ nhấp nháy cho Critical.
- Thêm icon lớn:
  - mắt/tập trung;
  - phanh;
  - nghỉ ngơi;
  - tốc độ.
- Thêm thanh risk bar từ 0 đến 100.
- Thêm mini card:
  - Driver State;
  - TTC;
  - Speed;
  - Alertness.
- Tách ECU interaction thành card riêng:
  - Brake Assist;
  - Buzzer;
  - Hazard;
  - Seatbelt/Haptic.
- Nếu mentor yêu cầu ECU rõ hơn, thêm VSS path thật:
  - `Vehicle.ADAS.BrakeAssistRequest`
  - `Vehicle.Cabin.WarningBuzzer`
  - `Vehicle.Body.HazardLight`
  - `Vehicle.Cabin.SeatbeltHapticWarning`
- Thêm chữ lớn chỉ 1 hành động chính để tài xế không bị rối.
- Critical nên ưu tiên:
  - `NGUY HIỂM`;
  - `PHANH AN TOÀN`;
  - TTC/risk;
  - voice.
- Warning nên nhẹ hơn:
  - `CẢNH BÁO`;
  - action ngắn;
  - nền vàng/nâu.
- Safe nên tối giản:
  - `LÁI XE AN TOÀN`;
  - `TIẾP TỤC QUAN SÁT`.

## 10. Nguyên tắc chỉnh UI

- Không hiển thị quá nhiều số cho driver.
- Màn hình critical phải đọc được trong dưới 1 giây.
- Risk/TTC/Alertness dùng làm evidence, không lấn át action chính.
- Voice chỉ nói khi severity đổi để tránh spam.
- Nếu AI offline, không hiển thị dữ liệu cũ như dữ liệu live.
- Không commit API key/secret vào source công khai nếu sau này tách repo public.
