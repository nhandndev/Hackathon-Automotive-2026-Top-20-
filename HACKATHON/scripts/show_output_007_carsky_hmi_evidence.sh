#!/usr/bin/env bash
set -u

ROOT="/Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON"
BE="$ROOT/SE/BE"

cd "$ROOT" || exit 1

pause() {
  printf "\n"
  read -r -p "Press Enter to continue..."
  printf "\n"
}

title() {
  printf "\n============================================================\n"
  printf "%s\n" "$1"
  printf "============================================================\n\n"
}

run_cmd() {
  printf "$ %s\n\n" "$*"
  "$@"
}

run_shell() {
  printf "$ %s\n\n" "$1"
  bash -lc "$1"
}

search_files() {
  local pattern="$1"
  shift
  if command -v rg >/dev/null 2>&1; then
    printf "$ rg -n %q" "$pattern"
    printf " %q" "$@"
    printf "\n\n"
    rg -n "$pattern" "$@"
  else
    printf "$ grep -RInE %q" "$pattern"
    printf " %q" "$@"
    printf "\n\n"
    grep -RInE "$pattern" "$@"
  fi
}

filter_stdin() {
  local pattern="$1"
  if command -v rg >/dev/null 2>&1; then
    rg "$pattern"
  else
    grep -E "$pattern"
  fi
}

title "Output #007 - Backend To CarSky To Android HMI Evidence"
cat <<'TEXT'
Goal:
Show the Backend -> CarSky/KUKSA -> HMI Bridge -> Android HMI path.

This script does not deploy, does not build APK, and does not change source code.
It only reads project files and sends a test Vehicle.Speed speed-mux signal to the current CarSky deployment.
TEXT

pause

title "1. Backend Mapper / Vehicle.Speed Source Evidence"
cat <<'TEXT'
What to say:
Backend mapper publishes DMS event values through Vehicle.Speed speed-mux so CarSky/KUKSA can receive the signal.
TEXT
search_files "vehicle-speed-mux|Vehicle.Speed" \
  SE/BE/app/integrations/carsky/mapper.py \
  SE/BE/app/integrations/carsky/client.py \
  SE/BE/app/integrations/carsky/service.py

pause

title "2. HMI Bridge / VHAL Source Evidence"
cat <<'TEXT'
What to say:
The HMI Bridge forwards Vehicle.Speed values into VHAL PERF_VEHICLE_SPEED for Android HMI.
TEXT
search_files "PERF_VEHICLE_SPEED|Vehicle.Speed|DMS_HMI" \
  SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua \
  SE/BE/carsky/dms_hmi_bridge.lua \
  SE/BE/carsky/dms_hmi_bridge_dual_push.lua

pause

title "3. Android APK Artifact Evidence"
cat <<'TEXT'
What to say:
The Android HMI APK artifact exists in the project and has hash, classes.dex, manifest, and signing metadata.
TEXT
run_cmd ls -lh SE/HMI/release/dms-hmi-realtime-vhal.apk
printf "\n"
run_cmd shasum -a 256 SE/HMI/release/dms-hmi-realtime-vhal.apk
printf "\n"
run_shell 'unzip -l SE/HMI/release/dms-hmi-realtime-vhal.apk | head -20'

pause

title "4. Android HMI Runtime Strings From APK"
cat <<'TEXT'
What to say:
The APK contains runtime strings for DMS_HMI, PERF_VEHICLE_SPEED, CarPropertyManager and HMI states.
TEXT
printf "$ unzip -p SE/HMI/release/dms-hmi-realtime-vhal.apk classes.dex | strings | grep/rg \"DMS_HMI|PERF_VEHICLE_SPEED|CarPropertyManager|SAFE|CRITICAL|TTC|km/h\"\n\n"
unzip -p SE/HMI/release/dms-hmi-realtime-vhal.apk classes.dex \
  | strings \
  | filter_stdin "DMS_HMI|PERF_VEHICLE_SPEED|CarPropertyManager|SAFE|CRITICAL|TTC|km/h"

pause

title "5. CarSky Deployment Status"
cat <<'TEXT'
What to say:
Now we check the current CarSky deployment and node list before sending a notification/signal.

After this command finishes:
1. Switch to CarSky UI.
2. Open the deployment/blueprint view.
3. Show these 3 nodes are Running:
   - DMS Signal Broker
   - DMS HMI Bridge
   - DMS Android HMI
4. Then return to this terminal and press Enter.
TEXT
cd "$BE" || exit 1
run_cmd .venv/bin/python scripts/carsky_phase05.py status
printf "\n"
run_cmd .venv/bin/python scripts/carsky_phase05.py nodes

pause

title "6. Prepare CarSky UI Before Sending Critical"
cat <<'TEXT'
Do this now in CarSky UI before pressing Enter:

1. Open Signal Watch / Browse Signals.
2. Search or watch:
   Vehicle.Speed
3. Keep Vehicle.Speed visible on screen.
4. Open Logs: DMS HMI Bridge in another panel/tab if possible.
5. Keep Android HMI screen visible if possible.

When CarSky UI is ready, return to this terminal and press Enter.
TEXT

pause

title "7. Send Critical Notification / Vehicle.Speed Speed-Mux"
cat <<'TEXT'
What to say:
The first custom VSS publish can fail because current CarSky does not expose Vehicle.Driver.State.
That is expected. The script then falls back to Vehicle.Speed speed-mux.
Pass condition: ok=true, mode=vehicle-speed-mux, sent=14.

After this command finishes:
1. Do NOT press Enter immediately.
2. Switch to CarSky Signal Watch and show Vehicle.Speed.
3. Show Logs: DMS HMI Bridge.
4. Show Android HMI screen or Android logcat.
5. Then return to this terminal and press Enter.
TEXT
run_shell '.venv/bin/python scripts/carsky_phase05.py scenario critical 2>&1 | tee /tmp/carsky-critical.log'

pause

title "8. Show Saved Critical Publish Log"
cat <<'TEXT'
What to say:
This log shows the critical signal publish result. If fallback_reason appears, it documents why speed-mux was used.
TEXT
run_cmd cat /tmp/carsky-critical.log

pause

title "9. What To Show In CarSky UI"
cat <<'TEXT'
Open CarSky UI and show:

1. Signal Watch:
   Watch Vehicle.Speed.
   Expected values during critical scenario:
   41.088 = risk 88
   42.002 = CRITICAL
   43.004 = microsleep
   44.015 = alertness 15%
   45.012 = TTC 1.2s
   46.001 = critical alert true
   48.003 = BRAKE_SAFE
   49.029 = real speed 29 km/h

2. Logs: DMS HMI Bridge:
   Expected log patterns:
   DMS_HMI_SPEED_MUX Vehicle.Speed=41.088 -> 0x11600207=41.088
   DMS_HMI_SPEED_MUX Vehicle.Speed=42.002 -> 0x11600207=42.002
   DMS_HMI_SPEED_MUX Vehicle.Speed=49.029 -> 0x11600207=49.029

3. Android shell logcat:
   Run:
   logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160

   Expected log patterns:
   DMS_HMI ... mux raw=41.088
   DMS_HMI ... mux raw=42.002
   DMS_HMI ... mux speed=49.029
TEXT

pause

title "10. Reset To Normal"
cat <<'TEXT'
What to say:
After the critical notification test, we reset the signal state to normal.

After reset, you can switch back to Signal Watch to show Vehicle.Speed returned to normal mux.
TEXT
run_cmd .venv/bin/python scripts/carsky_phase05.py scenario normal

title "Done"
cat <<'TEXT'
Report timestamp suggestion:

00:00 - 00:30 Backend mapper / Vehicle.Speed source evidence
00:30 - 01:00 HMI Bridge / VHAL source evidence
01:00 - 01:30 Android APK artifact/hash evidence
01:30 - 02:00 APK runtime strings evidence
02:00 - 02:30 CarSky status/nodes
02:30 - 03:00 Critical speed-mux publish result
03:00 - 03:40 Signal Watch / Bridge log / Android logcat evidence

Caveat:
Custom VSS paths are not available in the current CarSky deployment, so runtime correctly falls back to Vehicle.Speed speed-mux. Same-event Android UI proof should include Signal Watch, bridge log, Android logcat and APK UI in the same recording.
TEXT
