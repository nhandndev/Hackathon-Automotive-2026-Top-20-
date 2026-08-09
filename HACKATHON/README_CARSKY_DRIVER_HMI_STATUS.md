# 16. Connected-Car, CarSky and Driver HMI

## 16.1 Integration Status Summary

This section describes the current connected-car integration between the AI runtime, Fleet Dashboard backend, CarSky/KUKSA, the HMI Bridge, Android VHAL/CarProperty, and the Driver HMI APK.

The implemented runtime path is:

```text
AI / Local Model Runtime
        |
        v
Decision Engine
        |
        v
Backend Alert + Telemetry API
        |
        v
CarSky REST Signal API
        |
        v
KUKSA / DMS Signal Broker
        |
        v
DMS HMI Bridge
        |
        v
VHAL PERF_VEHICLE_SPEED speed-mux
        |
        v
Android CarPropertyManager
        |
        v
DMS Android HMI APK
```

## 16.2 Boundary Status

| Boundary | Current Status | Meaning |
|---|---:|---|
| AI -> Decision Engine | IMPLEMENTED | Local AI/model output is converted into decision events and live telemetry snapshots. |
| Decision Engine -> Backend | IMPLEMENTED | Backend receives normalized alert/snapshot data through the project API contract and tests. |
| Backend -> Fleet Dashboard | IMPLEMENTED | Dashboard receives live state through REST/WebSocket and renders map, trip detail, ranking, insights and reports. |
| Backend -> CarSky REST Signal API | VERIFIED | Backend can publish DMS multiplex values into the CarSky signal node; Signal Watch/API response confirms updates. |
| CarSky REST -> KUKSA / DMS Signal Broker | VERIFIED | CarSky signal node stores the published `Vehicle.Speed` values and exposes them to the bridge. |
| KUKSA / Signal Broker -> DMS HMI Bridge | VERIFIED | HMI Bridge subscribes to `Vehicle.Speed` and logs speed-mux forwarding when backend publishes telemetry. |
| DMS HMI Bridge -> Android VHAL | IMPLEMENTED WITH SPEED-MUX | Bridge forwards data through `PERF_VEHICLE_SPEED` (`0x11600207`) because the AAOS image reliably exposes this property. Custom DMS CarProperty IDs are not relied on. |
| Android VHAL -> Android CarPropertyManager | VERIFIED WITH HOTFIX | APK receives updates from `CarPropertyManager` using callback plus polling fallback. Runtime depends on the current CarSky/AAOS deployment and VHAL relay/route configuration. |
| Android CarPropertyManager -> DMS Android HMI APK | VERIFIED | APK V2.2 decodes speed-mux groups and updates the HMI UI for risk, severity, driver state, alertness, TTC, AI status, action, speed and safe score. |

## 16.3 Why Speed-Mux Is Used

The original plan was to expose several custom Android CarProperty IDs for DMS values:

| DMS Value | Intended Custom Property |
|---|---|
| Final Risk Score | Custom INT/FLOAT property |
| Critical Alert | Custom BOOLEAN property |
| Alertness Score | Custom FLOAT property |
| Min TTC | Custom FLOAT property |
| AI Status | Custom INT property |
| Recommended Action | Custom INT property |
| Severity | Custom INT property |
| Driver State | Custom INT property |

In the current CarSky AAOS runtime, these custom DMS properties are not reliably exposed through `CarPropertyService`.

Therefore the project uses a verified transport workaround:

```text
All DMS values are multiplexed through Vehicle.Speed / PERF_VEHICLE_SPEED.
```

The APK decodes the integer group before the decimal part:

| Mux Group | Meaning | Example |
|---:|---|---|
| `41.xxx` | Risk Score | `41.088` means risk score 88 |
| `42.xxx` | Severity | `42.002` means critical/high severity state |
| `43.xxx` | Driver State | `43.004` means microsleep or mapped driver state |
| `44.xxx` | Alertness Score | `44.075` means alertness 75 |
| `45.xxx` | Min TTC | `45.025` means TTC 2.5s, depending on encoder scale |
| `46.xxx` | Critical Alert | boolean encoded as numeric state |
| `47.xxx` | AI Status | AI status enum |
| `48.xxx` | Recommended Action | action enum |
| `49.xxx` | Real Speed | actual km/h shown by HMI |
| `50.xxx` | Safe Driving Score | local AI safe score |

This is why the table should not say “custom VHAL fully implemented”. The accurate status is:

```text
VHAL speed-mux transport implemented and verified.
Custom DMS CarProperty exposure is not required for the current demo path.
```

## 16.4 Verified Evidence

Current verification evidence:

- CarSky Signal Watch shows `Vehicle.Speed` changing after backend publishes telemetry.
- DMS HMI Bridge logs show the bridge receiving KUKSA updates and forwarding them to VHAL.
- VHAL relay/runtime logs show client connection to the VHAL target in the deployed CarSky environment.
- Android logcat shows the APK registering `PERF_VEHICLE_SPEED`.
- APK V2.2 updates UI values from speed-mux data.
- Backend tests cover CarSky mapping and AI alert publishing paths.

## 16.5 Current Limitations

| Limitation | Impact | Current Handling |
|---|---|---|
| Custom DMS CarProperty IDs are not exposed reliably by AAOS | Direct reads for custom risk/TTC/status properties may stay empty | Use `PERF_VEHICLE_SPEED` speed-mux transport |
| VHAL relay/route can be deployment-specific | New CarSky deploy may require re-running relay/init steps | Keep deployment checklist and init script |
| `Vehicle.Speed` is overloaded for DMS transport | Signal Watch value may look like encoded speed instead of pure km/h | APK decodes mux groups; group `49.xxx` carries real speed |
| Callback can be unstable in AAOS runtime | APK may miss some CarProperty events | APK uses polling fallback in addition to callback |

## 16.6 Corrected One-Line Status

The connected-car HMI path is implemented and verified for demo through a `Vehicle.Speed` / `PERF_VEHICLE_SPEED` speed-mux transport. Backend, KUKSA, HMI Bridge and Android APK are connected end-to-end; custom DMS CarProperty IDs remain avoided because the current AAOS runtime does not reliably expose them.
