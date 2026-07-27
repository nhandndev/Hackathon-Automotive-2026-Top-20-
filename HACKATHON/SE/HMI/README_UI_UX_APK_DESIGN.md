# README cho team UI/UX làm lại giao diện APK Android HMI

File này dành cho thành viên UI/UX trước giờ làm web nhưng muốn phụ thiết kế lại APK Android HMI cho dự án DMS Driver Safety. Mục tiêu là làm giao diện đẹp hơn, rõ hơn, demo tốt hơn trên CarSky Android Screen, nhưng không phá luồng dữ liệu đang chạy.

## 1. APK này dùng để làm gì

APK HMI là màn hình trong xe cho driver. Nó nhận dữ liệu từ hệ thống DMS/AI qua CarSky/KUKSA rồi hiển thị:

- Xe đang an toàn hay nguy hiểm.
- Tài xế đang tỉnh táo, mất tập trung, buồn ngủ, microsleep...
- Điểm rủi ro.
- Tốc độ.
- Alertness.
- TTC.
- Hành động khuyến nghị.
- Trạng thái AI.
- Trạng thái tương tác ECU mô phỏng.
- Nút bật/tắt voice warning.

Đây là màn hình để demo cho giám khảo nhìn vào là hiểu: “AI đang theo dõi tài xế và tình huống lái xe, sau đó cảnh báo lên HMI”.

## 2. File UI chính cần sửa

Source APK live demo hiện tại nằm ở:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

Build script:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

APK sau khi build:

```text
SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk
```

Script dùng để paste vào CarSky ADB widget:

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

## 3. Team UI/UX được phép sửa gì

Nên sửa:

- Layout màn hình trong `buildUi()`.
- Font size, spacing, padding.
- Màu nền theo trạng thái Safe/Warning/Critical.
- Cách trình bày card, badge, icon text.
- Text tiếng Việt hiển thị cho driver.
- Thứ tự ưu tiên thông tin.
- Cách hiển thị voice/ECU.
- Màn hình safe/warning/critical sao cho demo dễ nhìn.

Không nên sửa nếu chưa hỏi Backend/HMI owner:

- Package name `vn.fpt.dms.hmi`.
- Activity name `.MainActivity`.
- `Config.CARSKY_VALUES_URL`.
- `Config.CARSKY_API_KEY`.
- Logic parse signal từ CarSky.
- Tên VSS signal.
- Build script phần ký APK/signing.
- Script install qua CarSky ADB.

Nói dễ hiểu: team UI/UX tập trung làm đẹp phần hiển thị, đừng đổi đường dây dữ liệu.

## 4. Những state bắt buộc phải design

Tối thiểu cần có 3 trạng thái chính.

### SAFE

Ý nghĩa: tài xế ổn, rủi ro thấp.

Gợi ý UI:

- Màu xanh/navy dịu.
- Title: `LÁI XE AN TOÀN`.
- Action: `TIẾP TỤC QUAN SÁT`.
- Driver: `Tỉnh táo`.
- Risk thấp.
- Không làm UI quá căng thẳng.

### WARNING

Ý nghĩa: có dấu hiệu nguy hiểm vừa phải, cần nhắc tài xế.

Gợi ý UI:

- Màu vàng/cam.
- Title: `CẢNH BÁO`.
- Action: `TẬP TRUNG PHÍA TRƯỚC` hoặc `HÃY NGHỈ NGƠI`.
- Hiển thị lý do: mất tập trung, buồn ngủ, TTC thấp...
- Có icon cảnh báo hoặc badge nổi bật.

### CRITICAL

Ý nghĩa: nguy hiểm cao, cần phản ứng mạnh.

Gợi ý UI:

- Màu đỏ/đỏ đậm.
- Title: `NGUY HIỂM`.
- Action: `PHANH AN TOÀN` hoặc `GIẢM TỐC ĐỘ`.
- Risk score phải nổi bật.
- TTC nếu thấp phải dễ thấy.
- ECU simulated action phải nổi bật, ví dụ `BRAKE ASSIST REQUESTED`.

## 5. Data UI đang đọc

UI hiện đọc các signal sau:

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

Mapping quan trọng:

```text
DisplaySeverity = SAFE | WARNING | CRITICAL
RecommendedActionCode = NONE | FOCUS_FORWARD | TAKE_BREAK | BRAKE_SAFE | REDUCE_SPEED
Driver.State = alert | drowsy | yawning | distracted | microsleep
AIStatus = ONLINE | DEGRADED | OFFLINE
```

## 6. Thông tin nên ưu tiên hiển thị cho driver

Driver không cần nhìn toàn bộ JSON. Driver chỉ cần biết nhanh:

1. Mức nguy hiểm hiện tại.
2. Phải làm gì ngay.
3. Vì sao bị cảnh báo.
4. Rủi ro/tốc độ/TTC nếu cần.
5. AI còn online không.
6. ECU/hệ thống đã phản ứng gì.

Layout đề xuất:

```text
[AI ONLINE]                         [VOICE ON]

             CẢNH BÁO
        TẬP TRUNG PHÍA TRƯỚC

   Tài xế: Mất tập trung • TTC 3.0s

   Speed 75 km/h     Risk 55     Alertness 45%

   ECU: DRIVER WARNING BUZZER ON • HAPTIC ALERT ON
```

Nếu làm đẹp hơn, có thể chia thành:

- Center hero alert.
- Bottom telemetry strip.
- Right/left mini card cho AI và ECU.
- Voice button nhỏ, không chiếm quá nhiều diện tích.

## 7. Những hàm trong `MainActivity.java` cần biết

### `buildUi()`

Nơi tạo layout Android bằng Java code.

Dùng để:

- Thêm TextView.
- Tạo LinearLayout.
- Đổi padding.
- Đổi vị trí component.
- Thêm card.
- Thêm button.

### `render(State s)`

Nơi render dữ liệu ra màn hình.

Dùng để:

- Đổi màu nền theo severity.
- Set title/action/evidence.
- Format risk/speed/alertness.
- Hiển thị ECU text.
- Gọi voice.

### `actionText(String action)`

Mapping action code sang tiếng Việt.

Ví dụ:

```text
FOCUS_FORWARD → TẬP TRUNG PHÍA TRƯỚC
TAKE_BREAK    → HÃY NGHỈ NGƠI
BRAKE_SAFE    → PHANH AN TOÀN
REDUCE_SPEED  → GIẢM TỐC ĐỘ
NONE          → TIẾP TỤC QUAN SÁT
```

### `driverText(String driver)`

Mapping driver state sang tiếng Việt.

```text
alert       → Tỉnh táo
drowsy      → Buồn ngủ
yawning     → Ngáp
distracted  → Mất tập trung
microsleep  → Vi ngủ
```

### `ecuText(int severity, String action)`

Text mô phỏng tương tác ECU.

Hiện tại:

```text
SAFE
→ ECU: STANDBY • ALL DRIVER ALERT ACTUATORS OFF

WARNING
→ ECU: DRIVER WARNING BUZZER ON • HAPTIC ALERT ON

CRITICAL hoặc BRAKE_SAFE
→ ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

## 8. Quy tắc design cho demo hackathon

Nên:

- Ưu tiên đọc được từ xa.
- Font lớn, ít chữ.
- Màu severity rõ ràng.
- Một màn hình nhìn 3 giây là hiểu.
- Dùng tiếng Việt ngắn gọn.
- Giữ thông tin kỹ thuật ở mức vừa đủ.
- Làm đẹp nhưng đừng rối.

Không nên:

- Nhồi quá nhiều field.
- Hiển thị JSON raw cho driver.
- Dùng text nhỏ như dashboard web.
- Làm layout phụ thuộc internet/image bên ngoài.
- Dùng animation nặng.
- Đổi package/activity.
- Đưa API key vào screenshot/report.

## 9. Workflow làm việc đề xuất cho UI/UX

### Bước 1: Xem app hiện tại

Mở file:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

Đọc các hàm:

```text
buildUi()
render(State s)
actionText()
driverText()
ecuText()
```

### Bước 2: Design 3 màn hình

Design tối thiểu:

- Safe.
- Warning.
- Critical.

Có thể làm trên Figma hoặc vẽ nhanh bằng ảnh/mockup. Nhưng khi implement vào APK, ưu tiên layout native đơn giản bằng Java.

### Bước 3: Sửa UI trong Java

Sửa chủ yếu trong:

```text
buildUi()
render(State s)
```

Nếu cần thêm TextView mới:

1. Khai báo field ở đầu class.
2. Khởi tạo trong `buildUi()`.
3. Add vào layout.
4. Set text trong `render(State s)`.

### Bước 4: Tăng version APK

Mở:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

Tăng:

```text
--version-code
--version-name
```

Ví dụ nếu đang là:

```text
--version-code 3
--version-name 0.0.3
```

thì đổi thành:

```text
--version-code 4
--version-name 0.0.4
```

Việc này tránh lỗi Android không cho cài bản thấp hơn.

### Bước 5: Build APK

Chạy ở root project:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/HMI/demo-live/build_demo_apk.sh
```

Nếu thành công sẽ in ra:

```text
SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk
```

### Bước 6: Cài APK lên CarSky Android Screen

Copy script install:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
pbcopy < SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

Sau đó vào CarSky:

1. Mở device đang chạy.
2. Chọn widget `DMS Android ADB`.
3. Đợi thấy prompt:

```text
trout_arm64:/ $
```

4. Paste script vừa copy.
5. Đợi kết quả:

```text
Success
Starting: Intent { cmp=vn.fpt.dms.hmi/.MainActivity }
```

Nếu thấy lỗi `INSTALL_FAILED_VERSION_DOWNGRADE`, tăng `version-code` rồi build lại.

Nếu thấy lỗi `Connection closed`, bấm reconnect ADB rồi paste lại.

### Bước 7: Gửi mock signal để xem state đổi

Chạy từ Backend:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
.venv/bin/python scripts/carsky_phase05.py send-critical
```

Kết quả mong muốn:

```json
{
  "ok": true,
  "sent": 14
}
```

Sau đó nhìn Android Screen xem UI đổi sang warning/critical.

## 10. Checklist nghiệm thu UI

Trước khi báo hoàn thành, kiểm tra:

- APK build được.
- APK cài được lên CarSky Android Screen.
- App mở đúng package `vn.fpt.dms.hmi`.
- Safe state đọc dễ.
- Warning state đọc dễ.
- Critical state nổi bật.
- Speed/risk/alertness hiển thị đúng format.
- Driver state hiển thị tiếng Việt.
- Recommended action hiển thị rõ.
- AI status có hiển thị.
- ECU simulated status có hiển thị.
- Voice button còn hoạt động về mặt UI.
- Không lộ API key trong screenshot.

## 11. Lưu ý về voice

APK có logic gọi Android Text-to-Speech, nhưng Android VM trong CarSky có thể chưa có TTS engine.

Nếu kiểm tra thấy:

```bash
settings get secure tts_default_synth
```

trả về:

```text
null
```

và:

```bash
cmd package list packages | grep -i tts
```

không có gì, nghĩa là VM chưa có TTS engine. Khi đó nút voice có thể đổi trạng thái nhưng không nghe âm thanh.

Vì vậy UI nên có visual feedback cho voice, ví dụ:

```text
VOICE ON
Đang phát cảnh báo: Tập trung phía trước
```

Đừng phụ thuộc 100% vào âm thanh để demo.

## 12. Lưu ý quan trọng về CarSky/KUKSA

Hiện flow demo đúng là:

```text
Backend/mock sender
→ CarSky/KUKSA signal
→ Android HMI app đọc values
→ Render lên Android Screen
```

Không dùng trực tiếp Android `CarPropertyManager` cho custom DMS signal, vì Android Car Service hiện chỉ expose một số property chuẩn như speed. Các custom signal DMS như risk, TTC, driver state đang đi qua CarSky/KUKSA REST values.

Vì vậy khi làm UI, đừng sửa app quay lại đọc custom VHAL property nếu chưa có xác nhận mới từ CarSky/BTC.

## 13. Handoff cho Nhân

Khi UI/UX làm xong, gửi lại:

- File đã sửa:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

- Nếu có đổi build version:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

- Screenshot 3 state:
  - Safe.
  - Warning.
  - Critical.

- Ghi rõ có cần Nhân build/cài lại APK không.

## 14. Nếu muốn làm đẹp hơn nữa

Ý tưởng nâng cấp:

- Card lớn ở giữa cho severity.
- Thanh màu dọc bên trái theo risk.
- Badge `AI ONLINE`.
- Badge `ECU ACTIVE`.
- Progress bar alertness.
- TTC chip màu đỏ khi thấp.
- Risk score dạng vòng tròn.
- Mini timeline: AI detected → HMI warning → ECU action.
- Chế độ demo presentation, ít chữ hơn.

Ưu tiên demo: đẹp, rõ, ít rủi ro, không phá data flow.
