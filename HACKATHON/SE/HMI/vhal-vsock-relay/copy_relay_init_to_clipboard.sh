#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$SCRIPT_DIR/build/vhal-vsock-relay"

if [[ ! -f "$BIN" ]]; then
  echo "Missing $BIN" >&2
  echo "Build it first: $SCRIPT_DIR/build_android_relay.sh" >&2
  exit 1
fi

{
  echo "# Paste this inside the Android shell, e.g. trout_arm64:/ #"
  echo "id"
  echo "stop vendor.vehicle-hal-trout-server"
  echo "pkill -f vhal-vsock-relay || true"
  echo "cat > /data/local/tmp/vhal-vsock-relay.b64 <<'DMS_VHAL_RELAY_BIN'"
  base64 -i "$BIN"
  echo "DMS_VHAL_RELAY_BIN"
  echo "base64 -d /data/local/tmp/vhal-vsock-relay.b64 > /data/local/tmp/vhal-vsock-relay"
  echo "chmod 755 /data/local/tmp/vhal-vsock-relay"
  echo "nohup /data/local/tmp/vhal-vsock-relay --listen-cid 1 --listen-port 9210 --target-cid 2 --target-port 9300 >/data/local/tmp/vhal-vsock-relay.log 2>&1 &"
  echo "stop vendor.vehicle-hal-trout"
  echo "start vendor.vehicle-hal-trout"
  echo "stop car_service"
  echo "start car_service"
  echo "ps -A | grep vhal-vsock-relay || true"
  echo "tail -50 /data/local/tmp/vhal-vsock-relay.log || true"
} | pbcopy

echo "Relay init script copied to clipboard."
