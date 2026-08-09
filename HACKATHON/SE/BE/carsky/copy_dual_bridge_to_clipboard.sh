#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_FILE="$SCRIPT_DIR/dms_hmi_bridge_dual_push.lua"

if command -v pbcopy >/dev/null 2>&1; then
  pbcopy < "$SCRIPT_FILE"
elif command -v wl-copy >/dev/null 2>&1; then
  wl-copy < "$SCRIPT_FILE"
elif command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard < "$SCRIPT_FILE"
elif command -v clip.exe >/dev/null 2>&1; then
  clip.exe < "$SCRIPT_FILE"
else
  echo "No clipboard tool found (pbcopy, wl-copy, xclip or clip.exe)." >&2
  echo "Open and copy this file manually: $SCRIPT_FILE" >&2
  exit 1
fi

echo "Copied DMS HMI dual-push bridge script to clipboard."
echo "Paste it into CarSky: DMS HMI Bridge > Edit Script, save, then redeploy/restart."
