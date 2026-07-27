#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HMI_DIR="$ROOT_DIR/HMI/demo-live"
BE_ENV="$ROOT_DIR/BE/.env"
OUT_DIR="$HMI_DIR/build"
SDK_DIR="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
BT_DIR="$SDK_DIR/build-tools/37.0.0"
ANDROID_JAR="$SDK_DIR/platforms/android-35/android.jar"

if [ ! -f "$ANDROID_JAR" ]; then
  ANDROID_JAR="$(find "$SDK_DIR/platforms" -name android.jar | sort | tail -1)"
fi

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/gen" "$OUT_DIR/classes" "$OUT_DIR/dex" "$OUT_DIR/dist" "$HMI_DIR/src/vn/fpt/dms/hmi"

CARSKY_BASE_URL="$(grep '^CARSKY_BASE_URL=' "$BE_ENV" | cut -d= -f2-)"
CARSKY_API_KEY="$(grep '^CARSKY_API_KEY=' "$BE_ENV" | cut -d= -f2-)"
CARSKY_ROOM_ID="$(grep '^CARSKY_ROOM_ID=' "$BE_ENV" | cut -d= -f2-)"
CARSKY_NODE_KEY="$(grep '^CARSKY_NODE_KEY=' "$BE_ENV" | cut -d= -f2-)"
VALUES_URL="$CARSKY_BASE_URL/api/v1/signals/$CARSKY_ROOM_ID/$CARSKY_NODE_KEY/values"

cat > "$HMI_DIR/src/vn/fpt/dms/hmi/Config.java" <<EOF
package vn.fpt.dms.hmi;
final class Config {
    static final String CARSKY_VALUES_URL = "$VALUES_URL";
    static final String CARSKY_API_KEY = "$CARSKY_API_KEY";
}
EOF

"$BT_DIR/aapt2" compile --dir "$HMI_DIR/res" -o "$OUT_DIR/compiled.zip"
"$BT_DIR/aapt2" link -I "$ANDROID_JAR" \
  --manifest "$HMI_DIR/AndroidManifest.xml" \
  --java "$OUT_DIR/gen" \
  --version-code 3 \
  --version-name 0.0.3 \
  --min-sdk-version 29 \
  --target-sdk-version 35 \
  -o "$OUT_DIR/base-unsigned.apk" \
  "$OUT_DIR/compiled.zip"

javac -source 8 -target 8 \
  -bootclasspath "$ANDROID_JAR" \
  -classpath "$OUT_DIR/gen" \
  -d "$OUT_DIR/classes" \
  $(find "$OUT_DIR/gen" "$HMI_DIR/src" -name '*.java')

"$BT_DIR/d8" --min-api 29 --output "$OUT_DIR/dex" $(find "$OUT_DIR/classes" -name '*.class')
cp "$OUT_DIR/base-unsigned.apk" "$OUT_DIR/unsigned.apk"
(cd "$OUT_DIR/dex" && zip -q "$OUT_DIR/unsigned.apk" classes.dex)
"$BT_DIR/zipalign" -f 4 "$OUT_DIR/unsigned.apk" "$OUT_DIR/aligned.apk"
"$BT_DIR/apksigner" sign \
  --ks "$HOME/.android/debug.keystore" \
  --ks-key-alias androiddebugkey \
  --ks-pass pass:android \
  --key-pass pass:android \
  --out "$OUT_DIR/dist/dms-hmi-live-debug.apk" \
  "$OUT_DIR/aligned.apk"

echo "$OUT_DIR/dist/dms-hmi-live-debug.apk"
