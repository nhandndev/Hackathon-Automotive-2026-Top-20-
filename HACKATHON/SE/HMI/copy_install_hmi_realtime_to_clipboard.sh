#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APK="${1:-$ROOT/SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk}"

if [ ! -f "$APK" ]; then
  echo "APK not found: $APK" >&2
  echo "Build first:" >&2
  echo "  cd $ROOT" >&2
  echo "  SE/HMI/demo-live/build_demo_apk.sh" >&2
  exit 1
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

{
  echo "rm -f /data/local/tmp/dms-hmi-vhal-mux.b64 /data/local/tmp/dms-hmi-vhal-mux.apk"
  echo "cat > /data/local/tmp/dms-hmi-vhal-mux.b64 <<'DMS_HMI_VHAL_MUX_APK'"
  base64 < "$APK"
  echo "DMS_HMI_VHAL_MUX_APK"
  echo "base64 -d /data/local/tmp/dms-hmi-vhal-mux.b64 > /data/local/tmp/dms-hmi-vhal-mux.apk"
  echo "wc -c /data/local/tmp/dms-hmi-vhal-mux.apk"
  echo "pm install -r -d -t /data/local/tmp/dms-hmi-vhal-mux.apk"
  echo "pm grant vn.fpt.dms.hmi android.car.permission.CAR_SPEED"
  echo "am force-stop vn.fpt.dms.hmi"
  echo "am start -n vn.fpt.dms.hmi/.MainActivity"
  echo "logcat -d -s DMS_HMI:I AndroidRuntime:E | tail -80"
} > "$TMP"

if command -v pbcopy >/dev/null 2>&1; then
  pbcopy < "$TMP"
elif command -v wl-copy >/dev/null 2>&1; then
  wl-copy < "$TMP"
elif command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard < "$TMP"
elif command -v clip.exe >/dev/null 2>&1; then
  clip.exe < "$TMP"
else
  echo "No clipboard tool found (pbcopy, wl-copy, xclip or clip.exe)." >&2
  echo "Installer generated at: $TMP" >&2
  trap - EXIT
  exit 1
fi

echo "Copied fresh VHAL multiplex APK installer to clipboard."
echo "APK: $APK"
echo "Open CarSky Devices -> your device -> DMS Android ADB, paste once, then press Enter."
