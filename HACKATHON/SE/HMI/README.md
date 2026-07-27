# DMS CarSky Android HMI

Ứng dụng HMI tối thiểu cho `DMS Android HMI` trong Phase 05.2. App đọc các VHAL property do [`dms_hmi_bridge.lua`](../BE/carsky/dms_hmi_bridge.lua) phát, render SAFE/WARNING/CRITICAL/RECOVERY và dùng Android TTS tiếng Việt với cooldown.

Build:

```bash
./gradlew :app:assembleDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`.

App dùng reflection cho `android.car` để compile bằng Android SDK chuẩn; runtime phải là Android Automotive có Car Service/VHAL.
