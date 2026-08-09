# Evidence Summary — Fleet Dashboard + Android HMI

This package was generated from local source files. It does not replace manual screenshots/videos from the running demo.

## Evidence Status

| Evidence ID | Scope | Current status | Generated evidence | Manual evidence still needed |
|---|---|---|---|---|
| E-19 | Copilot grounded output | Pending formal audit | Source snippets for validation/fallback | Golden question set + raw Bedrock outputs |
| E-20 | Copilot latency/cost/failure | Demo sample only | Server/source snippets | Latency logs, timeout/provider-down traces |
| E-21 | Report export | Implemented DOC path | Source snippets for Word/DOC export | Exported DOC files + visual review |
| E-22 | Fleet Dashboard workflow | Implemented | FE source manifest/build checks if run | Screen recording of workflow |
| E-23 | Honest fallback | Partial/source-supported | Fallback snippets | Screenshots for API down/no trips/Bedrock fail |
| E-24 | CarSky/KUKSA/VHAL/APK path | Artifact-backed / deployment-dependent | Mapper snippets + APK hash/DEX/signing evidence | Same-event Signal Watch + bridge log + logcat + APK video |

## Report Wording

Use:

```text
Fleet Dashboard evidence is source/build backed. Android HMI evidence must be APK-artifact backed first: APK SHA-256, ZIP entries, signing metadata, DEX strings, installed APK logcat, and UI video for the same event. Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux is the verified demo transport. Custom DMS CarProperty IDs are not the final demo path.
```

Avoid:

```text
PDF export completed.
Custom DMS CarProperty fully production-ready.
Signal Watch alone proves Android HMI.
Source code alone proves the installed APK version.
Bedrock creates canonical metrics.
```
