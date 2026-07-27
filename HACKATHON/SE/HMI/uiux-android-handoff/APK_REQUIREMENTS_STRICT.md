# Yêu cầu bắt buộc cho APK Android HMI trên CarSky

File này là luật cứng cho team UI/UX khi làm APK Android HMI.

Lý do phải nghiêm: APK này không chỉ chạy trên điện thoại Android bình thường. Nó phải chạy trên CarSky Android Automotive/Skycraft HMI. Những app được convert tự động từ web sang mobile có thể chạy trên máy dev nhưng không chắc chạy được trên CarSky.

## 1. Kết luận ngắn gọn

Chỉ chấp nhận APK/source theo một trong hai dạng:

1. Native Android đơn giản giống app hiện tại của dự án.
2. Web preview để Nhân/AI port lại sang native Android sau.

Không tự ý gửi APK được convert bằng tool mobile nếu chưa được Nhân duyệt trước.

## 2. Format APK đã được chứng minh chạy trên CarSky

Dự án hiện đã chứng minh chạy được APK có đặc điểm:

```text
Language/source: Java native Android
Package: vn.fpt.dms.hmi
Activity: vn.fpt.dms.hmi/.MainActivity
Screen: landscape
Runtime target: Android Automotive / CarSky Skycraft
Install method: ADB widget trên CarSky
Data source: CarSky/KUKSA REST values hoặc mock fallback
Build output: signed debug APK
```

Folder source tương ứng trong project chính:

```text
SE/HMI/demo-live
```

File UI chính:

```text
SE/HMI/demo-live/src/vn/fpt/dms/hmi/MainActivity.java
```

Nếu team UI/UX gửi Android source khác hẳn cấu trúc này, mặc định xem là chưa tương thích.

## 3. Bắt buộc giữ nguyên

Không được đổi nếu chưa có xác nhận của Nhân:

```text
package: vn.fpt.dms.hmi
main activity: vn.fpt.dms.hmi/.MainActivity
orientation: landscape
min sdk: >= 23, khuyến nghị 29
target sdk: tương thích Android hiện tại, khuyến nghị 35
network: INTERNET permission nếu app còn poll CarSky
install: cài bằng ADB widget
```

Manifest tối thiểu phải tương tự:

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="vn.fpt.dms.hmi">
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:theme="@style/AppTheme"
        android:label="DMS Safety HMI"
        android:usesCleartextTraffic="true"
        android:resizeableActivity="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="landscape">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

## 4. Nghiêm cấm tự ý dùng tool/framework convert

Không gửi APK/source dùng các hướng sau nếu chưa hỏi Nhân trước:

- React Native.
- Flutter.
- Ionic.
- Capacitor.
- Cordova.
- Expo.
- Tauri mobile.
- Electron Android wrapper.
- PWA-to-APK online converter.
- Website-to-APK converter online.
- Android Studio template lạ không theo package/activity yêu cầu.
- APK build từ service online không rõ cấu hình.

Lý do:

- Có thể cần runtime/dependency CarSky không có.
- Có thể không chạy trên Android Automotive.
- Có thể sai package/activity nên script cài không launch được.
- Có thể không hỗ trợ landscape đúng.
- Có thể bị WebView/CORS/network/audio hạn chế.
- Có thể sinh APK target SDK sai và bị từ chối install.

Nếu muốn dùng tool convert, phải hỏi trước và ghi rõ:

```text
Tool/framework:
Android package:
Main activity:
Min SDK:
Target SDK:
Runtime dependency:
APK size:
Network/data flow:
Đã test trên CarSky chưa:
```

Nếu không có các thông tin này, Nhân/AI sẽ reject output.

## 5. WebView APK bị hạn chế như thế nào

WebView APK không bị cấm tuyệt đối, nhưng không được tự ý coi là output cuối nếu chưa test trên CarSky.

WebView chỉ được chấp nhận khi:

- Có source Android wrapper rõ ràng.
- Package vẫn là `vn.fpt.dms.hmi`.
- Activity vẫn là `.MainActivity`.
- Load local web assets, không phụ thuộc CDN.
- Có mock fallback.
- Không hardcode API key.
- Đã ghi rõ rủi ro CORS/network.
- Nhân đồng ý test trên CarSky.

Nếu team chỉ làm web UI, hãy gửi ở dạng preview web. Đừng tự convert thành APK rồi nói là xong.

## 6. APK/source output phải có gì

Nếu gửi Android APK source, bắt buộc có:

```text
android/
├── AndroidManifest.xml
├── build_demo_apk.sh hoặc hướng dẫn build rõ ràng
├── res/
│   └── values/
│       └── styles.xml
└── src/
    └── vn/fpt/dms/hmi/
        ├── MainActivity.java
        └── Config.example.java
```

Bắt buộc có thêm:

```text
README.md
DESIGN_NOTES.md
MERGE_NOTES.md
preview/
screenshots/
```

## 7. Data flow bắt buộc

APK phải hỗ trợ một trong hai mode:

```text
Mode 1: CarSky/KUKSA values → APK poll/read → render UI
Mode 2: Sample states/mock fallback → render UI
```

Không được tự ý yêu cầu Backend mới, server mới, Firebase, Supabase, cloud riêng, login, OAuth, database riêng hoặc API riêng nếu chưa được Nhân duyệt.

## 8. UI state bắt buộc

APK phải render được:

- SAFE.
- WARNING.
- CRITICAL.

Bắt buộc có:

- AI status.
- Severity title.
- Recommended action.
- Driver state.
- Risk score.
- Speed.
- Alertness.
- TTC.
- Voice status.
- ECU status.

## 9. Build/install compatibility

APK phải tránh các lỗi đã từng gặp:

```text
INSTALL_FAILED_DEPRECATED_SDK_VERSION
INSTALL_FAILED_VERSION_DOWNGRADE
```

Vì vậy:

- `minSdkVersion` không được quá thấp.
- `targetSdkVersion` phải hợp lý.
- Mỗi lần build phải tăng `versionCode`.
- APK phải signed.

## 10. Điều kiện reject output

Nhân/AI sẽ reject nếu output:

- Chỉ gửi file APK mà không có source.
- Dùng framework/tool convert chưa được duyệt.
- Đổi package/activity mà không báo.
- Không có preview.
- Không có 3 screenshot state.
- Không có `MERGE_NOTES.md`.
- Không ghi cách build.
- Có API key thật.
- Phụ thuộc internet/CDN để render UI.
- Không thể map về `SE/HMI/demo-live`.

## 11. Nếu chưa chắc, gửi web preview thôi

Nếu team UI/UX chưa chắc APK có chạy trên CarSky không, cách an toàn là:

```text
Chỉ làm preview web + screenshot + design notes.
Không tự convert APK.
```

Sau đó Nhân/AI sẽ port sang APK native đã được chứng minh chạy trên CarSky.
