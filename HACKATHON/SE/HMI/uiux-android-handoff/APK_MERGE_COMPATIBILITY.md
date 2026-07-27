# Quy tắc để folder Android UI/UX merge được với dự án Nhân

File này là phần quan trọng nhất nếu team UI/UX làm ở repo riêng.

Mục tiêu: team UI/UX gửi lại một folder Android mà AI bên máy Nhân đọc vào là hiểu ngay cần merge vào đâu, không phải đoán package, data flow, build flow.

Trước khi làm Android APK, phải đọc thêm:

```text
APK_REQUIREMENTS_STRICT.md
```

Nếu `APK_REQUIREMENTS_STRICT.md` và file này xung đột, ưu tiên `APK_REQUIREMENTS_STRICT.md`.

## 1. Project chính đang dùng gì

Project chính của Nhân đang có APK live demo tại:

```text
SE/HMI/demo-live
```

File UI chính:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

Build script chính:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

Manifest:

```text
SE/HMI/demo-live/AndroidManifest.xml
```

Styles:

```text
SE/HMI/demo-live/res/values/styles.xml
```

## 2. Output phải tương thích các giá trị này

Giữ nguyên nếu không có lý do cực kỳ rõ:

```text
package: vn.fpt.dms.hmi
main activity: vn.fpt.dms.hmi/.MainActivity
orientation: landscape
min sdk: 29 hoặc thấp hơn nhưng không dưới 23
target sdk: 35 hoặc tương thích Android hiện tại
```

Lý do:

- Nhân đang cài app bằng ADB lên CarSky Android Screen.
- Nếu đổi package/activity, script cài và lệnh launch sẽ phải sửa.
- Nếu target/min SDK sai, Android VM có thể từ chối install.

## 3. Không hardcode credential

Không được hardcode API key thật trong source output.

Nếu cần config, dùng file mẫu:

```text
Config.example.java
```

Ví dụ:

```java
package vn.fpt.dms.hmi;

final class Config {
    static final String CARSKY_VALUES_URL = "https://example.invalid/api/v1/signals/ROOM/NODE/values";
    static final String CARSKY_API_KEY = "";
}
```

Khi merge về project chính, Nhân/AI sẽ generate `Config.java` từ:

```text
SE/BE/.env
```

## 4. Data flow phải giữ

Flow demo đang chạy:

```text
Backend/mock sender
→ CarSky/KUKSA signal
→ Android HMI app đọc CarSky values
→ render lên Android Screen
```

Không tự ý đổi sang flow khác nếu chưa báo.

Không quay lại đọc custom Android `CarPropertyManager` cho DMS custom signal, vì custom DMS property chưa expose ổn định trên Android Car Service.

## 5. Nếu team làm Native Android

Output nên có:

```text
android/
├── AndroidManifest.xml
├── build_demo_apk.sh
├── res/
│   └── values/
│       └── styles.xml
└── src/
    └── vn/fpt/dms/hmi/
        ├── MainActivity.java
        └── Config.example.java
```

AI merge bằng cách:

```text
android/src/vn/fpt/dms/hmi/MainActivity.java
→ SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java

android/AndroidManifest.xml
→ SE/HMI/demo-live/AndroidManifest.xml

android/res/
→ SE/HMI/demo-live/res/
```

Sau đó tăng version trong:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

## 6. Nếu team làm WebView APK

Output phải ghi rõ:

```text
Implementation: WebView APK
```

Và cần có:

```text
web/
├── index.html
├── styles.css
└── app.js

android/
├── AndroidManifest.xml
└── src/.../MainActivity.java
```

Yêu cầu WebView:

- Load local file/assets, không phụ thuộc CDN.
- Có mock fallback nếu không gọi được CarSky values.
- Landscape 16:9.
- Không hardcode API key thật.

Lưu ý: WebView có thể gặp CORS/network nếu gọi trực tiếp CarSky REST. Vì vậy nếu chưa chắc, ưu tiên mock preview rồi để Nhân/AI quyết định port sang native.

## 7. Nếu team chỉ làm web preview

Nếu team chỉ làm HTML/CSS/JS preview, vẫn được, nhưng output phải ghi:

```text
Implementation: Web preview only
Android APK source: not included
```

Khi đó Nhân/AI sẽ port UI sang Android native sau.

Output tối thiểu:

```text
preview/
├── index.html
├── styles.css
├── app.js
└── sample-states.json
```

## 8. Quy tắc version APK

Mỗi lần build APK mới, phải tăng:

```text
--version-code
--version-name
```

Trong project chính hiện nằm ở:

```text
SE/HMI/demo-live/build_demo_apk.sh
```

Nếu không tăng version, Android có thể báo:

```text
INSTALL_FAILED_VERSION_DOWNGRADE
```

## 9. Tiêu chuẩn để merge được

AI bên máy Nhân chỉ merge nếu folder output có đủ:

- README rõ ràng.
- Source Android hoặc preview web rõ ràng.
- State Safe/Warning/Critical.
- Data contract không bị mất field quan trọng.
- Không chứa API key thật.
- Không chứa build cache.
- Không đổi package/activity âm thầm.

## 10. Những thứ tuyệt đối tránh

Không gửi:

```text
.gradle/
build/
node_modules/
.DS_Store
local.properties có path máy cá nhân
API key thật
```

Không đổi âm thầm:

```text
vn.fpt.dms.hmi
.MainActivity
landscape
CarSky/KUKSA data flow
```

## 11. Handoff note bắt buộc

Trong README output, team UI/UX phải có mục này:

```md
## Merge note for Nhân/AI

- Implementation type: Native Android | WebView APK | Web preview only
- Package changed: no/yes
- Activity changed: no/yes
- Data flow changed: no/yes
- Files to merge:
  - ...
- Known risks:
  - ...
```

Thiếu phần này thì AI vẫn có thể merge, nhưng sẽ chậm hơn và dễ sai hơn.
