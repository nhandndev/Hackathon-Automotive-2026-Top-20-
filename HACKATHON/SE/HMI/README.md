# DMS CarSky Android HMI — realtime only

HMI chính thức chỉ đọc VHAL data do
[`dms_hmi_bridge.lua`](../BE/carsky/dms_hmi_bridge.lua) đẩy từ CarSky/KUKSA.
Không còn REST polling, sample cycle hoặc mock fallback trong APK được build từ
source chính thức.

```text
AI DecisionEvent → Backend → CarSky/KUKSA → Lua bridge → VHAL PERF_VEHICLE_SPEED multiplex → Android HMI
```

Nếu Car Service/VHAL không sẵn sàng, ứng dụng phải hiện `AI OFFLINE`; ứng dụng
không được tự sinh SAFE/WARNING/CRITICAL.

## Source of truth

```text
app/src/main/java/vn/fpt/dms/hmi/MainActivity.java
app/src/main/AndroidManifest.xml
```

Thư mục `demo-live` chỉ còn là cách đóng gói APK thủ công cho môi trường không có
Gradle wrapper; nó compile cùng `MainActivity.java` phía trên, không có một HMI
logic thứ hai.

## Build

Với Android Studio: mở folder `SE/HMI`, chọn **Build APK(s)**.

Nếu máy có Gradle và Android SDK:

```powershell
cd E:\automotive_cc\Hackathon-Automotive-2026\HACKATHON\SE\HMI
gradle :app:assembleDebug
```

APK:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Trên Linux/macOS có Android build-tools, có thể dùng:

```bash
./demo-live/build_demo_apk.sh
```

Script này không đọc `SE/BE/.env` và không nhúng CarSky credential vào APK.

## Cài qua CarSky

### Cách nhanh: copy từng lệnh vào ADB widget

Repo đã có APK VHAL realtime đã ký và raw shell script để paste một lần:

```text
release/dms-hmi-realtime-vhal.apk
release/adb_install_realtime_hmi.txt
release/install_hmi_realtime_adb.sh
```

Trên Windows PowerShell, copy đúng raw script vào clipboard:

```powershell
.\SE\HMI\copy_install_hmi_realtime_to_clipboard.ps1
```

Trên macOS/Linux:

```bash
./SE/HMI/copy_install_hmi_realtime_to_clipboard.sh
```

Sau đó mở CarSky `Devices → Connected device → DMS Android ADB`, paste đúng một
lần rồi Enter. Clipboard chỉ chứa shell script raw nhiều dòng; không chứa
`Connecting...`, prompt `trout_arm64:/ $`, Markdown hay output cũ. `pm install`
phải trả `Success`; lệnh cuối mở package `vn.fpt.dms.hmi`.

SHA-256 APK:

```text
DE9DB3A454006087D3E692733DB790C5C1119D9CA4EA401705FA2FA1B3429241
```

APK này phải có Android Car/VHAL multiplex reader, không có `demoState`, REST URL
hoặc CarSky token. Chi tiết fix nằm ở
[`ANDROID_CARSKY_SOVD_VHAL_MUX_FIX.md`](ANDROID_CARSKY_SOVD_VHAL_MUX_FIX.md).

### Cách cài qua Backend helper

Backend `.env` cần đúng room và Android node. Từ `SE/BE`:

```powershell
python scripts\carsky_phase05.py status
python scripts\carsky_phase05.py nodes
python scripts\carsky_phase05.py install-apk ..\HMI\app\build\outputs\apk\debug\app-debug.apk
```

Phải build APK mới trước khi cài; APK trong `build/` có thể là artifact cũ và bị
git-ignore.

## Kiểm tra không còn mock

1. Không gửi event: HMI giữ SAFE/OFFLINE theo VHAL hiện có, không tự chuyển state.
2. Gửi một DecisionEvent thật: Signal Watch đổi, HMI đổi theo sau.
3. Dừng Backend không làm HMI tự chạy chu kỳ cảnh báo.
4. Tìm source không được còn `demoState`, `demoTick`, `sample-states` trong runtime
   Android chính thức.

Credential từng được nhúng trong `demo-live/Config.java` phải được revoke/rotate
trên CarSky. Source mới đã xóa file này, nhưng việc thu hồi token phải thực hiện ở
CarSky portal.
