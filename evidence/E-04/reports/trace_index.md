# Trace Index - E-04 Golden Event Trace

| Stage | Artifact | Status | Ghi chú |
|---|---|---|---|
| Deterministic Backend event | `raw/backend_to_carsky_unit_trace.log` | PASS | Verifies critical live snapshot and DecisionEvent forwarding tests |
| Golden event JSONL | `derived/golden_event.jsonl` | CREATED | Contains verified mux values and runtime command result |
| Runtime CarSky publish | `raw/carsky_scenario_critical_command.json` | PASS | Real command output, not fabricated |
| Signal Watch screenshot | `screenshots/` | MISSING | Needs Vehicle.Speed + timestamp capture |
| MP4 synchronized trace | `video/` | MISSING | Needs 60-90s same-event evidence |
| Android HMI UI | `screenshots/` or `video/` | MISSING | Needs same event displayed on APK |

## Golden Values

- Risk mux: `41.088` means risk score 88.
- Critical alert mux: `42.002` means critical state.
- Driver state mux: `43.004` means microsleep.
- TTC mux: `45.012` means TTC 1.2s.
- Speed mux: `49.xxx` carries speed value.
- Safe score mux: `50.012` means safe score 12.

## Trạng thái

**PARTIAL / TEST AND RUNTIME COMMAND TRACE CREATED; VIDEO-SCREENSHOT SYNC STILL REQUIRED**
