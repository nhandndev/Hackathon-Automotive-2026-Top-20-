#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APK="$ROOT_DIR/SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk"
REMOTE_B64="/data/local/tmp/dms-hmi-vhal-mux.b64"
REMOTE_APK="/data/local/tmp/dms-hmi-vhal-mux.apk"
CHUNK_SIZE=4000

if [[ ! -f "$APK" ]]; then
  echo "APK not found: $APK" >&2
  echo "Build first: ./SE/HMI/demo-live/build_demo_apk.sh" >&2
  exit 1
fi

copy_text() {
  if command -v pbcopy >/dev/null 2>&1; then
    pbcopy
  else
    cat
  fi
}

encoded="$(base64 < "$APK" | tr -d '\n')"
total_len="${#encoded}"
chunk_count=$(( (total_len + CHUNK_SIZE - 1) / CHUNK_SIZE ))

cmd="${1:-help}"

case "$cmd" in
  count)
    echo "APK: $APK"
    wc -c "$APK"
    echo "base64 chars: $total_len"
    echo "chunks: $chunk_count"
    ;;
  init)
    {
      echo "rm -f $REMOTE_B64 $REMOTE_APK"
      echo ": > $REMOTE_B64"
    } | copy_text
    echo "Copied INIT to clipboard. Paste into CarSky ADB, then Enter."
    ;;
  chunk)
    index="${2:-}"
    if [[ -z "$index" || ! "$index" =~ ^[0-9]+$ ]]; then
      echo "Usage: $0 chunk <1..$chunk_count>" >&2
      exit 1
    fi
    if (( index < 1 || index > chunk_count )); then
      echo "Chunk index out of range. Valid: 1..$chunk_count" >&2
      exit 1
    fi
    start=$(( (index - 1) * CHUNK_SIZE ))
    chunk="${encoded:start:CHUNK_SIZE}"
    {
      echo "cat >> $REMOTE_B64 <<'DMS_HMI_CHUNK_$index'"
      echo "$chunk"
      echo "DMS_HMI_CHUNK_$index"
    } | copy_text
    echo "Copied chunk $index/$chunk_count to clipboard. Paste into CarSky ADB, then Enter."
    ;;
  finish)
    {
      echo "base64 -d $REMOTE_B64 > $REMOTE_APK"
      echo "wc -c $REMOTE_APK"
      echo "pm install -r -d -t $REMOTE_APK"
      echo "pm grant vn.fpt.dms.hmi android.car.permission.CAR_SPEED"
      echo "logcat -c"
      echo "am force-stop vn.fpt.dms.hmi"
      echo "am start -n vn.fpt.dms.hmi/.MainActivity"
      echo "logcat -d -s DMS_HMI:I AndroidRuntime:E | tail -80"
    } | copy_text
    echo "Copied FINISH to clipboard. Paste into CarSky ADB, then Enter."
    ;;
  *)
    echo "Usage:"
    echo "  $0 count"
    echo "  $0 init"
    echo "  $0 chunk <1..$chunk_count>"
    echo "  $0 finish"
    ;;
esac
