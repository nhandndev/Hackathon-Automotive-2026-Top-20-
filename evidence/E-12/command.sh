#!/usr/bin/env bash
set -euo pipefail

export CARLA_ROOT="/home/student/Workspace/hungplt2/carla/"

if [[ -e "/home/student/Workspace/hungplt2/carla//evidence/E-12/clean_run_20260810T070042Z" ]]; then
  echo "[FAIL] Clean output đã tồn tại: /home/student/Workspace/hungplt2/carla//evidence/E-12/clean_run_20260810T070042Z" >&2
  exit 2
fi

python3 "/home/student/Workspace/hungplt2/carla/PythonAPI/examples/carla_project_scripts/carla_project_scripts/script_carla//collect.py"   --output-root "/home/student/Workspace/hungplt2/carla//evidence/E-12/clean_run_20260810T070042Z"   --maps Town10HD_Opt   --trips-per-map 1   --start-index 1   --seed 20260801   --lighting-profile v2-exact   --driver-skill low   --baseline-probability 0.02   --accident-probability 0.55   --traffic-speed-scale-min 1.30   --traffic-speed-scale-max 1.85   --vehicle-min 35   --vehicle-max 70   --walker-min 15   --walker-max 55   --frames 600   --fps 20   --render-width 1280   --render-height 720   --output-width 640   --output-height 360   --depth-step 5   --camera-preflight-frames 5   --camera-sanity-min-day-sky-luma 5   --camera-sanity-max-day-sky-dark-ratio 0.95   --runtime-blocked-depth-ratio 0.20   --runtime-blocked-consecutive-frames 20   --runtime-max-blocked-frame-ratio 0.05   --camera-near-plane-m 0.10   --camera-max-intersection-frames 0   --trip-stationary-speed-kmh 0.5   --trip-max-stationary-fraction 0.60   --trip-max-stationary-run-s 10   --min-mapped-labels-per-trip 1   --occlusion-dynamic-partial 0.20   --occlusion-dynamic-heavy 0.55   --require-observed-event   --event-min-observed-frames 3   --event-max-lateral-m 8   --event-lead-max-lateral-m 3.5   --event-min-lateral-motion-m 1.0   --event-min-speed-drop-kmh 5   --event-stopped-max-speed-kmh 2   --event-slow-max-speed-kmh 25   --event-min-speed-gain-kmh 5   --event-min-approach-m 5   --event-min-stopped-frames 2   --downgrade-invalid-event-to-none   --salvage-invalid-frames   --max-invalid-frames 300   --delete-invalid-existing-trips   --no-instance-debug-on-unmapped   --no-save-runner-log   --run-retries 4   --max-consecutive-failures 0   --pause-seconds 40   --map-pause-seconds 120   --min-free-gb 35   --min-free-vram-gb 1.0
