# E-24 Mapping - CarSky/KUKSA/VHAL/APK Same-Event Trace

Generated: `2026-08-10T04:39:09+00:00`  
Commit: `d41b8e168afb046da1cf26946e987246f42d7a14`

## Status

**PARTIAL / RUNTIME COMMAND AND SOURCE-APK PATH VERIFIED; SAME-EVENT MEDIA CAPTURE PENDING**

## What Is Real In This Folder

- Real CarSky command output copied from E-04: `scripts/carsky_phase05.py scenario critical`.
- Parsed runtime result: `ok=True`, `mode=vehicle-speed-mux`, `sent=14`.
- Source path evidence for `Vehicle.Speed` speed-mux, Lua bridge, `PERF_VEHICLE_SPEED`, and Android `CarPropertyManager`.
- APK static evidence copied from E-15.

## Same-Event Chain

1. Backend scenario script sends critical speed-mux values to CarSky REST Signal API.
2. CarSky accepts final demo path as `Vehicle.Speed` speed-mux.
3. Lua HMI Bridge subscribes `Vehicle.Speed` and pushes VHAL property `PERF_VEHICLE_SPEED` (`291504647`, `0x11600207`).
4. Android HMI APK reads `PERF_VEHICLE_SPEED` through `CarPropertyManager` and decodes mux groups.

## Speed-Mux Values For Critical Scenario

| Value | Meaning |
|---|---|
| `41.088` | risk score 88 |
| `42.002` | critical severity/state |
| `43.004` | driver state microsleep |
| `44.015` | alertness score 15% |
| `45.012` | TTC 1.2s |
| `46.001` | critical alert flag true |
| `47.000` | AI status online/available marker |
| `48.003` | recommended action brake safely |
| `49.029` | real speed about 29 km/h |
| `50.012` | safe score 12/100 |

## Important Caveat

The runtime command proves the CarSky API path accepted the demo speed-mux flow. This folder still needs a reviewer-facing screenshot/video showing **Signal Watch value + Bridge log + Android HMI UI/logcat for the same event** before E-24 can be marked DONE.

The fallback reason about `Vehicle.Driver.State` is expected and important: it documents that custom DMS VSS paths were unavailable in that deployment, so the final demo uses `Vehicle.Speed` speed-mux intentionally.
