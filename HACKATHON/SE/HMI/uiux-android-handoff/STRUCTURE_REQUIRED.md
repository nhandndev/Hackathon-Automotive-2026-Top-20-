# Cấu trúc folder output bắt buộc

Khi team UI/UX làm xong, gửi lại một folder theo cấu trúc này.

Tên folder đề xuất:

```text
dms-hmi-android-uiux
```

## 1. Cấu trúc tối thiểu

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

## 2. File bắt buộc

Trước khi làm Android APK, phải đọc:

```text
APK_REQUIREMENTS_STRICT.md
APK_MERGE_COMPATIBILITY.md
```

Nếu output không tuân thủ hai file này, Nhân/AI có quyền reject.

### `README.md`

Phải ghi:

- App làm gì.
- Cách build.
- Package/activity.
- Có đổi gì so với bản cũ.
- Có cần dependency gì không.

### `DESIGN_NOTES.md`

Phải ghi:

- Ý tưởng design.
- Màu từng state.
- Component chính.
- Cách xử lý Safe/Warning/Critical.
- Có animation hay không.
- Có asset/icon custom hay không.

### `MERGE_NOTES.md`

Phải ghi rõ để AI bên máy Nhân merge nhanh:

```text
Implementation type: Native Android | WebView APK | Web preview only
Package changed: no/yes
Activity changed: no/yes
Data flow changed: no/yes
Files to merge:
Known risks:
```

### `android/src/.../MainActivity.java`

Source chính của APK.

Yêu cầu:

- Có thể build được.
- Hỗ trợ landscape.
- Hỗ trợ 3 state.
- Không hardcode API key thật.

### `preview/index.html`

File để Nhân mở bằng browser xem demo nhanh.

Yêu cầu:

- Không cần backend.
- Không cần internet.
- Có nút SAFE/WARNING/CRITICAL.
- Layout gần giống APK dự kiến.
- Chạy được khi folder này nằm trong repo riêng.

### `screenshots/`

Cần có ảnh:

- `safe.png`
- `warning.png`
- `critical.png`

Nếu chưa có APK thật, screenshot từ preview cũng được.

## 3. Những thứ không gửi

Không gửi:

- `.gradle/`
- `build/`
- file APK nếu chưa được yêu cầu.
- API key thật.
- file local máy cá nhân.
- `.DS_Store`.
- `node_modules/`.

Không gửi APK/source sinh từ tool convert mobile chưa được duyệt như:

- React Native.
- Flutter.
- Ionic.
- Capacitor.
- Cordova.
- Expo.
- online website-to-APK converter.

## 4. Nếu làm bằng WebView

Nếu output là WebView APK, cấu trúc được phép là:

```text
dms-hmi-android-uiux/
├── README.md
├── DESIGN_NOTES.md
├── android/
│   ├── AndroidManifest.xml
│   ├── build.gradle hoặc build_demo_apk.sh
│   └── src/
│       └── ...
├── web/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── preview/
│   └── index.html
└── screenshots/
```

Nhưng phải ghi rõ app lấy dữ liệu thế nào:

- Poll CarSky REST.
- Nhận WebSocket từ Backend.
- Dùng mock fallback.

## 5. Nếu chỉ làm web preview

Nếu team UI/UX chưa làm Android source, vẫn có thể gửi folder preview trước.

Cấu trúc:

```text
dms-hmi-android-uiux/
├── README.md
├── DESIGN_NOTES.md
├── MERGE_NOTES.md
├── preview/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── sample-states.json
└── screenshots/
    ├── safe.png
    ├── warning.png
    └── critical.png
```

Trong `MERGE_NOTES.md` ghi:

```text
Implementation type: Web preview only
Android APK source: not included
```

Khi đó Nhân/AI sẽ port preview sang Android APK sau.

## 6. Tiêu chuẩn để AI merge dễ

Folder output tốt là folder mà AI đọc xong biết ngay:

- File nào là source chính.
- File nào là preview.
- File nào là sample data.
- Package Android là gì.
- Build bằng lệnh gì.
- Những điểm đã thay đổi.
- Có rủi ro gì.

Nếu thiếu README hoặc cấu trúc lung tung, AI merge sẽ chậm và dễ sai.
