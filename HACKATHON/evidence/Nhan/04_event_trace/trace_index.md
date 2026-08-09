# E-04 Golden Event Trace

## Selected Run

| Field | Value |
|---|---|
| Date/time | TBD |
| Operator | Nhân |
| Trip ID | TBD |
| Scenario | critical -> normal |
| Clock sync note | TBD |

## Expected Same-Event Chain

```text
Backend scenario critical
-> CarSky Signal Watch Vehicle.Speed
-> DMS_HMI_SPEED_MUX bridge log
-> Android HMI CRITICAL UI
```

## Evidence Files

| File | Description |
|---|---|
| `golden_event.jsonl` | Event/log lines with timestamp |
| `demo_60_90s.mp4` | Same-event runtime video |
| `screenshots/` | Signal Watch, bridge log, HMI UI |

## Caveat

TBD

