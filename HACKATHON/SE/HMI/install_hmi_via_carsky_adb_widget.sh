#!/usr/bin/env bash
set -euo pipefail

echo "Deprecated: embedded APK installers can reinstall stale/mock HMI code." >&2
echo "Build SE/HMI/app, then run from SE/BE:" >&2
echo "python scripts/carsky_phase05.py install-apk ../HMI/app/build/outputs/apk/debug/app-debug.apk" >&2
exit 2
