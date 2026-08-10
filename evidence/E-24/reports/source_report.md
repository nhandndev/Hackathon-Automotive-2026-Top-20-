# E-24 - CarSky/KUKSA/VHAL/APK Same-Event Trace

Generated: `2026-08-10T04:39:09+00:00`  
Commit: `d41b8e168afb046da1cf26946e987246f42d7a14`

## Status

**PARTIAL / RUNTIME COMMAND AND SOURCE-APK PATH VERIFIED; SAME-EVENT MEDIA CAPTURE PENDING**

## Evidence Table

| Evidence | Source | Result |
|---|---|---|
| `raw/carsky_scenario_critical_command.json` | Copied from E-04 real command log | `returncode=0`, stdout contains `ok=true`, `mode=vehicle-speed-mux`, `sent=14` |
| `raw/carsky_scenario_critical_parsed.json` | Copied from E-04 parsed output | Confirms final CarSky demo path uses `Vehicle.Speed` speed-mux |
| `raw/source_locators.log` | Repo source grep | Locates mapper, scenario script, Lua bridge and Android CarProperty code |
| `raw/hmi_apk_static_scan.log` | Copied from E-15 APK static scan | APK contains `PERF_VEHICLE_SPEED` and `CarPropertyManager` runtime strings |
| `derived/mapping.csv` | Generated from verified artifacts | Maps each boundary and status |
| `derived/speed_mux_values.csv` | Generated from script/source constants | Documents critical scenario mux groups |
| `derived/manifest.json` | Generated evidence metadata | Captures claimed/not-claimed boundaries |
| `derived/carsky_trace_bundle.zip` | Generated archive | Bundle of E-24 evidence files |

## What Can Be Claimed

- Backend/CarSky critical scenario command ran successfully in the recorded evidence: `ok=true`, `mode=vehicle-speed-mux`, `sent=14`.
- The demo reuses CarSky Signal API/KUKSA path through `Vehicle.Speed` instead of calling the APK directly.
- The HMI bridge and APK are aligned to standard AAOS `PERF_VEHICLE_SPEED` / Android `CarPropertyManager` path.

## What Must Not Be Claimed Yet

- Do not claim custom DMS VSS paths are production-ready.
- Do not claim physical vehicle actuation.
- Do not mark same-event UI trace DONE until screenshots/video/logcat are attached in `screenshots/` or `video/`.
