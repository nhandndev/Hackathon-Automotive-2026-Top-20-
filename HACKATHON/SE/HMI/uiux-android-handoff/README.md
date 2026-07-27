# DMS Android HMI UI/UX Handoff

Folder này là gói bàn giao cho team UI/UX thiết kế lại APK Android HMI của dự án DMS Driver Safety.

Team UI/UX chỉ cần làm trong folder này hoặc dựa đúng cấu trúc này để trả lại. Nhân sẽ là người build/cài APK lên CarSky sau.

Folder này có thể tách thành một repo riêng. Nếu làm repo riêng, vẫn phải giữ đúng cấu trúc output để AI bên máy Nhân quét lại và merge vào project chính.

## 1. Mục tiêu

Thiết kế lại giao diện Android HMI cho đẹp, dễ demo, dễ hiểu với giám khảo.

Màn hình HMI cần trả lời nhanh 4 câu hỏi:

1. Tình huống hiện tại có an toàn không?
2. Driver đang bị gì?
3. Driver cần làm gì ngay?
4. Hệ thống/ECU đã phản ứng gì?

## 2. Có thể chuyển web UI thành APK Android không?

Có, có 3 hướng:

### Hướng A — Native Android

Viết UI bằng Android native Java/Kotlin.

Ưu điểm:

- Nhẹ.
- Ít dependency.
- Phù hợp CarSky/AAOS demo.
- Dễ cài bằng ADB.

Nhược điểm:

- Team web UI/UX sẽ hơi lạ tay nếu chưa quen Android.

### Hướng B — WebView APK

Đóng UI web HTML/CSS/JS vào một Android WebView.

Ưu điểm:

- Team UI/UX web làm nhanh.
- Có thể dùng HTML/CSS.
- Dễ preview trên browser.

Nhược điểm:

- Cần Android wrapper WebView.
- Nếu gọi API CarSky trực tiếp trong WebView có thể gặp CORS/network.
- Cần kiểm tra kỹ trên CarSky Android VM.

### Hướng C — Capacitor/Ionic/React Native

Build web app thành Android app bằng framework.

Ưu điểm:

- Hợp với team web.

Nhược điểm:

- Nặng.
- Nhiều dependency.
- Không nên dùng cho demo gấp nếu chưa setup sẵn.

## 3. Khuyến nghị cho dự án này

Khuyến nghị: dùng hướng A hoặc B.

Luật cứng: nếu chưa được Nhân duyệt trước, không tự ý dùng tool convert web thành APK như React Native, Flutter, Ionic, Capacitor, Cordova, Expo hoặc website-to-APK converter. Những hướng này có thể chạy trên máy dev nhưng chưa chắc chạy trên CarSky Android Automotive.

Nếu team chỉ quen web, hãy làm web preview trước. Nhân/AI sẽ port sang Android native đã được chứng minh chạy trên CarSky.

Nếu chỉ cần làm đẹp nhanh và ít rủi ro, dùng native Android hiện tại:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

Nếu team UI/UX muốn làm bằng web cho quen tay, hãy làm trước UI ở:

```text
preview/index.html
```

Sau đó Nhân/AI sẽ port layout đó sang Android native hoặc WebView APK.

## 4. Folder này gồm gì

```text
uiux-android-handoff/
├── README.md
├── STRUCTURE_REQUIRED.md
├── HMI_DATA_CONTRACT.md
├── UI_ACCEPTANCE_CHECKLIST.md
├── APK_REQUIREMENTS_STRICT.md
├── APK_MERGE_COMPATIBILITY.md
├── WEB_PREVIEW_GUIDE.md
├── preview/
│   ├── index.html
│   └── sample-states.json
└── android-output-template/
    └── README.md
```

Ý nghĩa:

- `README.md`: file đang đọc.
- `STRUCTURE_REQUIRED.md`: cấu trúc folder bắt buộc khi team UI/UX gửi lại.
- `HMI_DATA_CONTRACT.md`: dữ liệu/state UI phải hỗ trợ.
- `UI_ACCEPTANCE_CHECKLIST.md`: checklist nghiệm thu.
- `APK_REQUIREMENTS_STRICT.md`: luật cứng về APK được phép gửi để tránh app không chạy trên CarSky.
- `APK_MERGE_COMPATIBILITY.md`: quy tắc để APK/folder Android merge được với dự án Nhân.
- `WEB_PREVIEW_GUIDE.md`: cách chạy demo web preview khi folder này nằm ở repo riêng.
- `preview/index.html`: demo giao diện bằng browser để UI/UX xem nhanh.
- `android-output-template/README.md`: mô tả folder Android mà team UI/UX phải trả lại.

## 5. Input Nhân gửi cho team UI/UX

Gửi nguyên folder:

```text
SE/HMI/uiux-android-handoff
```

Nếu team cần xem source APK đang chạy thật, gửi thêm:

```text
SE/HMI/demo-live
```

Nhưng nếu không muốn họ đụng code thật, chỉ cần gửi `uiux-android-handoff`.

Nếu team làm trên repo riêng, họ có thể copy nguyên folder này thành repo mới:

```text
dms-hmi-uiux-design/
├── README.md
├── STRUCTURE_REQUIRED.md
├── HMI_DATA_CONTRACT.md
├── UI_ACCEPTANCE_CHECKLIST.md
├── APK_REQUIREMENTS_STRICT.md
├── APK_MERGE_COMPATIBILITY.md
├── WEB_PREVIEW_GUIDE.md
├── preview/
└── android-output-template/
```

Sau đó họ làm preview/design trong repo riêng và gửi lại folder output.

## 6. Output team UI/UX phải gửi lại

Team UI/UX gửi lại một folder Android hoàn chỉnh, ví dụ:

```text
dms-hmi-android-uiux/
├── README.md
├── DESIGN_NOTES.md
├── android/
│   ├── AndroidManifest.xml
│   ├── build_demo_apk.sh
│   ├── res/
│   └── src/
├── preview/
│   ├── index.html
│   └── sample-states.json
└── screenshots/
    ├── safe.png
    ├── warning.png
    └── critical.png
```

Bắt buộc có:

- README giải thích họ đã làm gì.
- Source Android đầy đủ.
- Preview HTML hoặc screenshot.
- 3 state Safe/Warning/Critical.
- Không hardcode API key thật.
- Không đổi package nếu không cần.
- Có ghi rõ đây là Native Android hay WebView APK.
- Có hướng dẫn merge về `SE/HMI/demo-live`.
- Tuân thủ `APK_REQUIREMENTS_STRICT.md`.

## 7. Package Android phải giữ

Để Nhân cài đè app hiện tại dễ, giữ:

```text
package: vn.fpt.dms.hmi
activity: vn.fpt.dms.hmi/.MainActivity
orientation: landscape
```

Nếu đổi package/activity, phải ghi thật rõ trong README.

## 8. Cách UI/UX xem demo nhanh

Mở file này bằng browser:

```text
preview/index.html
```

Trong preview có nút chuyển state:

- SAFE
- WARNING
- CRITICAL

Preview này không phải APK thật. Nó chỉ giúp designer xem layout và state trước khi port qua Android.

## 9. Cách Nhân/AI merge lại sau này

Khi nhận folder output từ team UI/UX:

1. AI đọc `README.md`.
2. AI đọc `DESIGN_NOTES.md`.
3. AI so sánh `preview/index.html` với source Android.
4. AI map layout sang `SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java`.
5. AI tăng version APK.
6. AI build lại APK.
7. Nhân cài lên CarSky bằng ADB widget.

Chi tiết quy tắc merge nằm trong:

```text
APK_MERGE_COMPATIBILITY.md
```

## 10. Quy tắc quan trọng

Không được làm mất các field quan trọng:

- severity.
- recommended action.
- driver state.
- speed.
- risk.
- alertness.
- TTC.
- AI status.
- ECU status.
- voice status.

Không được phụ thuộc internet để render UI.

Không được để API key thật trong file preview/screenshot.

Không được làm UI chỉ đẹp trên web nhưng không thể port sang Android landscape 1920x1080.

## 11. Kích thước màn hình mục tiêu

CarSky Android Screen đang dùng:

```text
1920 x 1080
landscape
DPI khoảng 320
```

Preview HTML cũng set layout theo tỉ lệ 16:9.

## 12. Gợi ý style

Nên làm kiểu automotive HMI:

- Nền tối.
- Chữ lớn.
- Cảnh báo rõ.
- Ít chữ.
- Card bo góc.
- Màu theo severity:
  - Safe: xanh/navy.
  - Warning: vàng/cam.
  - Critical: đỏ.
- Dùng icon đơn giản, không cần ảnh nặng.

## 13. Ghi chú cho AI sau này

Nếu AI bên máy Nhân đọc folder output này, hãy ưu tiên:

1. Giữ data flow CarSky/KUKSA hiện tại.
2. Chỉ merge UI nếu source Android build được.
3. Không thay BE/CarSky script nếu task chỉ là UI.
4. Nếu output là web-only, port sang Android native hoặc WebView tùy độ phức tạp.
5. Luôn giữ khả năng demo 3 state bằng mock signal.
