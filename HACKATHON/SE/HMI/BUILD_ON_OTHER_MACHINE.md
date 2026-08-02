# Build Android HMI trên máy khác

Tài liệu này chỉ dành cho việc build ứng dụng Android HMI. Không cài đặt, chạy
hoặc thay đổi bất kỳ thành phần AI nào.

## 1. Kết quả bắt buộc phải gửi lại

Máy build phải tạo đúng thư mục:

```text
HACKATHON/SE/HMI/handoff/from_other_machine/
```

Thư mục này phải có đủ bốn file:

```text
dms-hmi-carsky-rest-v1.0.5-debug.apk
sha256.txt
build-info.txt
gradle-build.log
```

Không đổi tên hoặc gửi riêng lẻ từng file. Nén nguyên thư mục
`from_other_machine` thành ZIP khi chuyển về máy chính.

## 2. Yêu cầu môi trường

Chỉ cần:

- Git.
- JDK 17.
- Android SDK Command-line Tools.
- `platforms;android-35`.
- `build-tools;35.0.0`.
- `platform-tools`.
- Gradle 8.9.

Không cần Android Studio, Android Emulator, Python, conda hoặc thư viện AI.

## 3. Lấy đúng source

Clone hoặc cập nhật repository, sau đó vào đúng thư mục HMI:

```powershell
git pull
cd HACKATHON\SE\HMI
```

Trước khi build, file sau phải tồn tại:

```text
app/src/main/java/vn/fpt/dms/hmi/MainActivity.java
```

Source đúng phải chứa cả các chuỗi sau:

```text
CARSKY REALTIME SETUP
sdkmanager POST /values logic via HttpURLConnection
AndroidKeyStore
```

Kiểm tra nhanh trên PowerShell:

```powershell
Select-String `
  -Path app\src\main\java\vn\fpt\dms\hmi\MainActivity.java `
  -Pattern "CARSKY REALTIME SETUP","HttpURLConnection","AndroidKeyStore"
```

APK không được chứa CarSky API key. Người dùng nhập key trên màn hình setup ở
lần chạy đầu tiên; key được mã hóa bằng Android Keystore.

## 4. Cấu hình Android SDK

Tạo file `local.properties` trong `HACKATHON/SE/HMI`.

Ví dụ Windows:

```properties
sdk.dir=D:/Android/Sdk
```

Ví dụ macOS:

```properties
sdk.dir=/Users/USERNAME/Library/Android/sdk
```

Ví dụ Linux:

```properties
sdk.dir=/home/USERNAME/Android/Sdk
```

Kiểm tra Android SDK trên Windows:

```powershell
Test-Path "D:\Android\Sdk\platforms\android-35\android.jar"
Test-Path "D:\Android\Sdk\build-tools\35.0.0\aapt2.exe"
Test-Path "D:\Android\Sdk\build-tools\35.0.0\apksigner.bat"
```

Ba kết quả phải là `True`.

## 5. Build trên Windows

Từ `HACKATHON/SE/HMI`:

```powershell
$GRADLE = "D:\Android\gradle-8.9\bin\gradle.bat"

& $GRADLE `
  --no-daemon `
  clean `
  :app:assembleDebug `
  2>&1 | Tee-Object -FilePath gradle-build.log

if ($LASTEXITCODE -ne 0) {
  throw "Android build failed. Send gradle-build.log for diagnosis."
}
```

Nếu Gradle nằm ở đường dẫn khác, chỉ sửa biến `$GRADLE`.

## 6. Build trên macOS hoặc Linux

Từ `HACKATHON/SE/HMI`:

```bash
set -o pipefail
/path/to/gradle-8.9/bin/gradle \
  --no-daemon \
  clean \
  :app:assembleDebug \
  2>&1 | tee gradle-build.log
```

Không tiếp tục nếu command trả exit code khác `0`.

## 7. Thu thập output trên Windows

Từ `HACKATHON/SE/HMI`, chạy nguyên khối:

```powershell
$OUTPUT = "handoff\from_other_machine"
$APK_SOURCE = "app\build\outputs\apk\debug\app-debug.apk"
$APK_OUTPUT = "$OUTPUT\dms-hmi-carsky-rest-v1.0.5-debug.apk"

if (!(Test-Path -LiteralPath $APK_SOURCE)) {
  throw "APK not found: $APK_SOURCE"
}

New-Item -ItemType Directory -Force $OUTPUT | Out-Null
Copy-Item -LiteralPath $APK_SOURCE -Destination $APK_OUTPUT -Force
Copy-Item -LiteralPath "gradle-build.log" -Destination "$OUTPUT\gradle-build.log" -Force

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $APK_OUTPUT
"$($hash.Hash)  dms-hmi-carsky-rest-v1.0.5-debug.apk" |
  Set-Content -Encoding ascii "$OUTPUT\sha256.txt"

$javaVersion = (& java -version 2>&1) -join "`n"
$gradleVersion = (& $GRADLE --version 2>&1) -join "`n"
$gitCommit = (& git rev-parse HEAD 2>&1) -join "`n"
$apkSize = (Get-Item -LiteralPath $APK_OUTPUT).Length

@"
build_status=SUCCESS
git_commit=$gitCommit
apk_file=dms-hmi-carsky-rest-v1.0.5-debug.apk
apk_size_bytes=$apkSize
android_compile_sdk=35
android_build_tools=35.0.0
application_id=vn.fpt.dms.hmi
version_code=5
version_name=1.0.5-carsky-rest

JAVA
$javaVersion

GRADLE
$gradleVersion
"@ | Set-Content -Encoding utf8 "$OUTPUT\build-info.txt"

Compress-Archive `
  -Path "$OUTPUT\*" `
  -DestinationPath "handoff\dms-hmi-from-other-machine.zip" `
  -Force

Get-ChildItem $OUTPUT | Select-Object Name,Length
```

File cần chuyển về máy chính:

```text
HACKATHON/SE/HMI/handoff/dms-hmi-from-other-machine.zip
```

## 8. Thu thập output trên macOS hoặc Linux

Từ `HACKATHON/SE/HMI`:

```bash
set -euo pipefail
OUTPUT="handoff/from_other_machine"
APK_SOURCE="app/build/outputs/apk/debug/app-debug.apk"
APK_OUTPUT="$OUTPUT/dms-hmi-carsky-rest-v1.0.5-debug.apk"

test -f "$APK_SOURCE"
mkdir -p "$OUTPUT"
cp "$APK_SOURCE" "$APK_OUTPUT"
cp gradle-build.log "$OUTPUT/gradle-build.log"

if command -v sha256sum >/dev/null 2>&1; then
  (cd "$OUTPUT" && sha256sum dms-hmi-carsky-rest-v1.0.5-debug.apk > sha256.txt)
else
  (cd "$OUTPUT" && shasum -a 256 dms-hmi-carsky-rest-v1.0.5-debug.apk > sha256.txt)
fi

{
  echo "build_status=SUCCESS"
  echo "git_commit=$(git rev-parse HEAD)"
  echo "apk_file=dms-hmi-carsky-rest-v1.0.5-debug.apk"
  echo "apk_size_bytes=$(wc -c < "$APK_OUTPUT" | tr -d ' ')"
  echo "android_compile_sdk=35"
  echo "android_build_tools=35.0.0"
  echo "application_id=vn.fpt.dms.hmi"
  echo "version_code=5"
  echo "version_name=1.0.5-carsky-rest"
  echo
  echo "JAVA"
  java -version 2>&1
  echo
  echo "GRADLE"
  /path/to/gradle-8.9/bin/gradle --version
} > "$OUTPUT/build-info.txt"

(cd handoff && zip -r dms-hmi-from-other-machine.zip from_other_machine)
```

## 9. Checklist trước khi gửi

- Build kết thúc bằng `BUILD SUCCESSFUL`.
- APK có kích thước lớn hơn `0` byte.
- `sha256.txt` có SHA-256 của đúng APK gửi về.
- `build-info.txt` ghi `version_code=5` và
  `version_name=1.0.5-carsky-rest`.
- Không sửa `MainActivity.java`, `AndroidManifest.xml` hoặc `build.gradle` chỉ để
  làm build qua lỗi.
- Không đưa `.env`, API key hoặc credential vào ZIP.

## 10. Những gì máy chính sẽ kiểm tra

Sau khi nhận ZIP, máy chính sẽ kiểm tra:

1. SHA-256 có khớp APK không.
2. Package có đúng `vn.fpt.dms.hmi` không.
3. Version có đúng `5 / 1.0.5-carsky-rest` không.
4. Manifest có permission `android.permission.INTERNET` không.
5. APK có màn `CARSKY REALTIME SETUP` không.
6. APK không chứa CarSky API key.
7. Cài APK lên device `test`, nhập key một lần và test tuần tự
   `normal → warning → critical`.

Nếu build thất bại, không gửi APK cũ. Chỉ gửi `gradle-build.log` để chẩn đoán.
