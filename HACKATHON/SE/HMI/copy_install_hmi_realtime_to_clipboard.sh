#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$ROOT/release/install_hmi_realtime_adb.sh"

if command -v pbcopy >/dev/null 2>&1; then
  pbcopy < "$INSTALLER"
elif command -v wl-copy >/dev/null 2>&1; then
  wl-copy < "$INSTALLER"
elif command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard < "$INSTALLER"
elif command -v clip.exe >/dev/null 2>&1; then
  clip.exe < "$INSTALLER"
else
  echo "No clipboard tool found (pbcopy, wl-copy, xclip or clip.exe)." >&2
  exit 1
fi

echo "Copied raw CarSky ADB installer to clipboard: $INSTALLER"
echo "Open DMS Android ADB, paste once, then press Enter."
