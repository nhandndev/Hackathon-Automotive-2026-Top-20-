# Android output template

Team UI/UX có thể copy folder này thành folder output thật.

Trước khi tạo APK/source Android, bắt buộc đọc:

```text
../APK_REQUIREMENTS_STRICT.md
../APK_MERGE_COMPATIBILITY.md
```

Không dùng tool convert web thành APK nếu chưa được Nhân duyệt trước.

Tên folder output đề xuất:

```text
dms-hmi-android-uiux
```

## Cấu trúc nên trả lại

```text
dms-hmi-android-uiux/
├── README.md
├── DESIGN_NOTES.md
├── MERGE_NOTES.md
├── android/
│   ├── AndroidManifest.xml
│   ├── build_demo_apk.sh
│   ├── res/
│   │   └── values/
│   │       └── styles.xml
│   └── src/
│       └── vn/
│           └── fpt/
│               └── dms/
│                   └── hmi/
│                       ├── MainActivity.java
│                       └── Config.example.java
├── preview/
│   ├── index.html
│   └── sample-states.json
└── screenshots/
    ├── safe.png
    ├── warning.png
    └── critical.png
```

## README output cần ghi

Copy checklist này vào README output:

```md
# DMS HMI Android UI/UX Output

## Package

- package: vn.fpt.dms.hmi
- activity: vn.fpt.dms.hmi/.MainActivity
- orientation: landscape

## Cách build

\`\`\`bash
cd android
./build_demo_apk.sh
\`\`\`

## Cách preview

Mở:

\`\`\`text
preview/index.html
\`\`\`

## Những gì đã đổi

- ...

## State đã hỗ trợ

- SAFE
- WARNING
- CRITICAL

## Lưu ý khi merge

- ...
```

## MERGE_NOTES.md bắt buộc

Tạo file:

```text
MERGE_NOTES.md
```

Nội dung mẫu:

```md
# Merge notes for Nhân/AI

## Implementation type

Native Android

## Package/activity

- Package changed: no
- Activity changed: no
- Package: vn.fpt.dms.hmi
- Activity: vn.fpt.dms.hmi/.MainActivity

## Data flow

- Data flow changed: no
- Still uses CarSky/KUKSA values.

## Files to merge

- android/src/vn/fpt/dms/hmi/MainActivity.java
- android/AndroidManifest.xml
- android/res/
- preview/
- screenshots/

## Known risks

- ...
```

## Config.example.java

Không commit API key thật.

Ví dụ:

```java
package vn.fpt.dms.hmi;

final class Config {
    static final String CARSKY_VALUES_URL = "https://example.invalid/api/v1/signals/ROOM/NODE/values";
    static final String CARSKY_API_KEY = "";
}
```

Khi merge vào repo chính, AI/Nhân sẽ generate `Config.java` từ `.env`.
