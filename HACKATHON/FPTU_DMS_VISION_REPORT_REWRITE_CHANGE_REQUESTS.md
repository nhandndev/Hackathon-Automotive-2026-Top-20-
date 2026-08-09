# FPTU DMS Vision Report Rewrite Change Requests

## Scope

This review focuses on the product/demo layers that are most likely to be challenged by reviewers:

- Fleet Dashboard
- Fleet AI Copilot / Bedrock report flow
- Saved trip JSON/local AI telemetry
- CarSky / KUKSA / VHAL / Android HMI
- Connected-car boundary status

The scored AI submission flow for C1/C2/C3 should stay separate from the product demonstration flow.

## Executive Summary

Several current report sections still describe an older CarSky/HMI architecture based on custom VSS/custom Android CarProperty paths. The runtime implementation has moved to a safer verified path:

```text
Backend/AI
  -> CarSky REST Signal API
  -> KUKSA / DMS Signal Broker
  -> DMS HMI Bridge
  -> VHAL PERF_VEHICLE_SPEED speed-mux
  -> Android CarPropertyManager
  -> DMS Android HMI APK
```

The report should not claim that custom DMS Android CarProperty IDs are fully exposed. The accurate statement is:

```text
The connected-car HMI demo is verified through PERF_VEHICLE_SPEED speed-mux.
Custom DMS CarProperty IDs are avoided because the current AAOS runtime does not reliably expose them.
```

## 1. Core Report Terms To Change

| Old wording | Replace with |
|---|---|
| `custom signals` as the main HMI path | `Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux transport` |
| `VHAL custom properties fully implemented` | `VHAL speed-mux implemented and verified for demo` |
| `Android HMI partial / blocked` | `Verified for demo / deployment-dependent` |
| `Backend -> KUKSA -> HMI` | `Backend -> CarSky REST Signal API -> KUKSA -> HMI Bridge -> VHAL speed-mux -> Android CarProperty -> APK` |
| `HMI reads custom DMS properties` | `HMI decodes DMS state multiplexed through PERF_VEHICLE_SPEED` |
| `AI Copilot uses FE .env.local` | `AI Copilot reads Bedrock config from SE/BE/.env` |
| `PDF export` | `Word/DOC export` |
| `all reports are AI generated` | `JSON/local AI renders deterministic report first; Bedrock only adds validated insight` |

## 2. Section 2.7: AI Output To System Demonstration

### Current issue

The report may currently say:

```text
DecisionEvent -> Backend/REST -> CarSky/KUKSA -> HMI Bridge -> Android HMI
```

This is too vague and hides the real VHAL transport.

### Recommended replacement

```text
DecisionEvent -> Backend/REST -> CarSky Signal API -> KUKSA/DMS Signal Broker
-> DMS HMI Bridge -> VHAL PERF_VEHICLE_SPEED speed-mux
-> Android CarPropertyManager -> DMS Android HMI APK
```

### Explanation to add

```text
The connected-car branch is a product demonstration branch. It does not modify
the scored C1/C2/C3 CSV. It consumes the same AI output after the Decision Engine
has normalized frame-level predictions into runtime DecisionEvents and telemetry
snapshots.
```

## 3. Section 2.8: Component Boundaries

### Current issue

The table may still describe Android HMI as:

```text
Android HMI | VHAL/vehicle property | Driver alert | Partial implementation
```

This is outdated.

### Recommended row

| Component | Input | Output | Role / status |
|---|---|---|---|
| Android HMI | `PERF_VEHICLE_SPEED` speed-mux via Android `CarPropertyManager` | Driver alert, risk, TTC, AI status, action, speed, safe score | Verified for demo / deployment-dependent |

### Recommended paragraph after the table

```text
Implementation boundary: AI -> Decision Engine, Decision Engine -> Backend,
Backend -> Fleet Dashboard, Backend -> CarSky Signal API, CarSky -> KUKSA,
and KUKSA -> HMI Bridge are implemented/verified. The Android HMI path is
verified for demo through VHAL `PERF_VEHICLE_SPEED` speed-mux. Custom DMS
Android CarProperty IDs are not used as the primary path because the current
AAOS runtime does not reliably expose them.
```

## 4. Section 2.9: Runtime / Replay / Partial Table

### Current issue

The row may still say:

```text
Android HMI realtime | VHAL -> Android | Hiển thị alert trên HMI | Blocked / partial
```

### Recommended row

| Mode | Data source | Purpose | Status |
|---|---|---|---|
| Android HMI realtime | VHAL `PERF_VEHICLE_SPEED` speed-mux -> Android `CarPropertyManager` -> APK | Show driver alert, risk, TTC, AI status, recommended action, real speed and safe score on HMI | Verified for demo / deployment-dependent |

### Note to add

```text
Because the current CarSky AAOS runtime exposes `PERF_VEHICLE_SPEED` reliably
but does not reliably expose custom DMS CarProperty IDs, the HMI demo uses
speed-mux over `Vehicle.Speed`. APK V2.2 decodes multiplex groups for risk,
severity, driver state, alertness, TTC, AI status, recommended action, real
speed and safe score.
```

## 5. CarSky / Android HMI Section

### Replace the architecture summary

Use:

```text
CarSky Blueprint uses three nodes:
1. DMS Signal Broker: KUKSA / signal node receiving backend-published values.
2. DMS HMI Bridge: subscribes KUKSA and forwards encoded DMS state to VHAL.
3. DMS Android HMI: AAOS APK reading Android CarPropertyManager.
```

### Replace the signal claim

Avoid saying:

```text
KUKSA custom signals: Vehicle.ADAS.FinalRiskScore, Vehicle.Driver.State, ...
```

Use:

```text
The backend can publish multiple logical DMS values. For the HMI demo, these
values are transported through `Vehicle.Speed` / `PERF_VEHICLE_SPEED` speed-mux
because that property is reliably available in Android CarPropertyService.
```

### Mux table to include

| Mux group | Meaning |
|---:|---|
| `41.xxx` | Risk score |
| `42.xxx` | Severity |
| `43.xxx` | Driver state |
| `44.xxx` | Alertness score |
| `45.xxx` | Min TTC |
| `46.xxx` | Critical alert |
| `47.xxx` | AI status |
| `48.xxx` | Recommended action |
| `49.xxx` | Real speed km/h |
| `50.xxx` | Safe driving score |

## 6. Important Code Consistency Warning

There is a source-level mismatch that should be fixed or documented before final report freeze:

- `SE/BE/app/integrations/carsky/mapper.py` emits decimal mux groups `41.xxx` to `50.xxx`.
- `SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java` decodes decimal mux groups `41.xxx` to `50.xxx`.
- `SE/BE/carsky/dms_hmi_bridge.lua` still contains an older `10000 + value` encoding table.

### Required action

Before claiming full HMI verification in the final report, make sure the deployed CarSky bridge script matches the APK/backend contract.

Correct report wording if this remains deployment-specific:

```text
The verified APK/backend contract uses decimal speed-mux groups `41.xxx` to
`50.xxx`. The CarSky bridge script used in deployment must match this contract;
older `10000 + value` bridge scripts are legacy and should not be used for the
final demo.
```

## 7. Fleet Dashboard Section

### Current accurate features

The report can claim these features:

- Map / fleet overview.
- Trip detail.
- Live camera/dashboard panel.
- Performance insights.
- Driver ranking and ranking analysis.
- Safety report detail and overview.
- Maintenance report detail and overview.
- AI Copilot drawer.
- Word/DOC report export.
- Saved trip loading from `src/data/saved_trips`.
- JSON/local AI deterministic reporting before Bedrock insight.

### Change ranking wording

Avoid:

```text
Ranking is sorted by BTC safe score.
```

Use:

```text
Ranking uses the dashboard's canonical Ranking Score derived from JSON/local AI
risk and behavior fields. Average Risk is displayed for audit but does not
decide rank position.
```

### Change insights wording

Avoid:

```text
Performance Insights is only for one trip.
```

Use:

```text
Performance Insights can explain a selected trip while preserving fleet context
from all loaded saved/live trips.
```

### Change saved trip wording

Add:

```text
Saved trip JSON is loaded as completed trip context. Legacy saved JSON may
contain `Infinity` for no-collision TTC; the FE server normalizes this to valid
JSON before serving it to the browser.
```

## 8. Fleet AI Copilot / Bedrock Section

### Current issue

Some report text says the AI Copilot uses `SE/FE/.env.local`.

This is outdated.

### Recommended replacement

```text
Fleet AI Copilot reads Bedrock configuration from `SE/BE/.env`. Frontend-local
AI env files are not the source of truth. This avoids stale token mismatch
between BE and FE.
```

### Bedrock behavior to describe

Use:

```text
The report renders deterministic JSON/local AI content first. Bedrock is called
as a lazy explanation layer when the user opens/requests a report. If Bedrock
returns a validated payload, the UI updates to AI Copilot insight and keeps it
cached by input signature. If Bedrock fails, times out or returns invalid
content, the UI keeps the JSON/local AI report and does not show fake AI
insight.
```

### Four report types to list

```text
1. Safety detail report: one selected trip.
2. Safety overview report: fleet-level aggregate over selected trips.
3. Maintenance detail report: one selected trip, rule-based inspection triage.
4. Maintenance overview report: fleet-level maintenance/inspection summary.
```

### Validation rules to mention

```text
Bedrock is not allowed to recalculate canonical scores, risk levels, event
counts, TTC, maintenance priority or cost. It only explains the supplied
JSON/local AI fields. Payloads that mix safety and maintenance report types or
describe zero-valued events as active risks are rejected.
```

## 9. Export Report Section

### Current issue

Some text still mentions PDF export or PDF A4.

Current user requirement changed to:

```text
Drop PDF; keep Word/DOC export.
```

### Recommended replacement

```text
The report page exports a Word-compatible DOC file containing summary metrics,
trip details, event evidence, KPI context and validated Bedrock insight when
available. PDF export is intentionally not listed in the final demo scope.
```

## 10. KPI / Benchmark Section

### Items to update or soften

Avoid hard claims if not re-measured on final environment:

| Claim to avoid | Safer claim |
|---|---|
| `Bedrock latency < 1.8s / 100% success` | `Bedrock integration verified with current token; latency depends on provider/token and report size` |
| `CarSky HMI fully production ready` | `CarSky HMI verified for demo through speed-mux; deployment-specific VHAL route may require init/hotfix` |
| `PDF export passed` | `DOC export supported` |
| `Custom DMS properties are registered` | `Custom DMS values are encoded through PERF_VEHICLE_SPEED speed-mux` |
| `All reports are AI-generated` | `Reports are JSON/local AI first, Bedrock explanation second` |

## 11. Troubleshooting Section

### Update Bedrock troubleshooting

Replace:

```text
Check token in SE/FE/.env.local
```

With:

```text
Check token in SE/BE/.env. FE server loads AI provider config from BE env.
Restart FE after changing Bedrock token because the Express server reads env at startup.
```

### Update HMI troubleshooting

Replace:

```text
HMI không update nhưng Signal Watch có data -> Android CarProperty/VHAL bridge chưa map đúng property
```

With:

```text
HMI does not update but Signal Watch changes:
1. Confirm `Vehicle.Speed` receives mux values in the 41.xxx-50.xxx range.
2. Confirm HMI Bridge forwards to `PERF_VEHICLE_SPEED` 0x11600207.
3. Confirm APK logcat shows `Registered DMS VHAL transport with speed-mux`.
4. Confirm the installed APK is V2.2 or newer.
5. If a new CarSky deployment was created, rerun the required VHAL route/relay/init steps.
```

## 12. Boundary Status Table To Use

| Boundary | Status | Evidence / meaning |
|---|---|---|
| AI -> Decision Engine | IMPLEMENTED | AI outputs become runtime event/telemetry inputs. |
| Decision Engine -> Backend | IMPLEMENTED | Backend receives normalized events/snapshots through API contract. |
| Backend -> Fleet Dashboard | IMPLEMENTED | REST/WebSocket dashboard views and reports render from live/saved trip data. |
| Backend -> CarSky REST Signal API | VERIFIED | Backend publisher sends speed-mux values to CarSky signal endpoint. |
| CarSky REST -> KUKSA / Signal Broker | VERIFIED | Signal Watch/API shows `Vehicle.Speed` values changing. |
| KUKSA / Signal Broker -> HMI Bridge | VERIFIED | Bridge subscribes KUKSA and logs mux forwarding. |
| HMI Bridge -> Android VHAL | VERIFIED FOR DEMO WITH SPEED-MUX | Bridge forwards through `PERF_VEHICLE_SPEED`. |
| Android VHAL -> CarPropertyManager | VERIFIED WITH DEPLOYMENT HOTFIX | APK reads property callback + polling fallback. |
| CarPropertyManager -> Android HMI APK | VERIFIED | APK V2.2 decodes mux groups and renders HMI state. |

## 13. Final Recommended Connected-Car Paragraph

```text
For the connected-car demonstration, FPTU DMS Vision uses CarSky as the vehicle
runtime bridge between backend AI decisions and the in-car Android HMI. The
backend publishes DMS telemetry through the CarSky signal API into KUKSA. The
DMS HMI Bridge subscribes to these values and forwards the HMI state through
Android VHAL using the standard `PERF_VEHICLE_SPEED` property. Because the
current AAOS runtime exposes this property reliably while custom DMS
CarProperty IDs are not consistently visible, the demo uses a speed-mux
transport. APK V2.2 decodes mux groups for risk, severity, driver state,
alertness, TTC, AI status, recommended action, real speed and safe score. This
path is verified for demo and remains separate from the scored C1/C2/C3
submission flow.
```

## 14. Final Recommended AI Copilot Paragraph

```text
Fleet AI Copilot is implemented as a report explanation layer, not as the source
of canonical metrics. The dashboard first renders deterministic values from
JSON/local AI telemetry, including ranking score, risk, TTC, event counts and
maintenance triage. Bedrock is requested lazily only for the report the user is
viewing. If Bedrock returns a validated payload, the UI updates with AI
explanation and keeps the result cached. If Bedrock is unavailable, slow or
invalid, the report remains usable with JSON/local AI and does not display mock
AI insight.
```

## 15. Files That Should Be Cross-Checked Before Final Submission

| File | Why it matters |
|---|---|
| `README.md` | Contains outdated FE env, custom signal and CarSky status wording. |
| `README_TECHNICAL_BUSINESS_FULL.md` | Contains outdated custom signal wording and possibly over-strong Bedrock claims. |
| `README_BTC_TECHNICAL_FEATURE_C.md` | Contains outdated PDF, FE env and custom VSS signal claims. |
| `reportbtc/README_TONG_QUAT_DU_AN_VA_HUONG_DAN_TEST.md` | Likely mirrors old README claims. |
| `reportbtc/C2_PROGRESS_REPORT_FPTU_DMS_VISION.md` | Still says VHAL -> Android APK was blocked/partial. |
| `SE/HMI/ANDROID_CARSKY_SOVD_VHAL_MUX_FIX.md` | Needs mux contract aligned with current backend/APK decimal groups if used as evidence. |
| `SE/BE/carsky/dms_hmi_bridge.lua` | Must match current mux contract before final live demo. |

## 16. Priority Before Final Report Freeze

1. Fix the written report boundary/status wording.
2. Align mux contract across backend mapper, bridge script and APK documentation.
3. Replace `SE/FE/.env.local` references with `SE/BE/.env`.
4. Remove PDF export claims; describe DOC export only.
5. Soften benchmark claims that were not re-measured on final environment.
6. Keep scored AI flow separate from Fleet Dashboard/CarSky demo flow.
7. Explicitly state that Bedrock explains validated canonical data and does not create canonical metrics.
