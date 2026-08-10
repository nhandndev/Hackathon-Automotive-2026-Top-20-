# Source Report - E-05 Alert Orchestrator State/Policy

| Evidence | Source | Note |
|---|---|---|
| `derived/policy_summary.json` | `HACKATHON/AI/configs/decision_engine.yaml`, `AI/core/decision_engine/*` | Summarizes real source files, thresholds and file hashes |
| `derived/policy_config.yaml` | `HACKATHON/AI/configs/decision_engine.yaml` | Frozen copy of current policy config |
| `derived/state_trace.jsonl` | Existing static trace evidence | Source/lifecycle trace, not a full replay |
| `derived/orchestrator_junit.xml` | Existing static test marker | Does not claim a full pytest run without runtime logs |
| `commands/commands.log` | Read-only source checks | How to re-check evidence files |

## Current conclusion

E-05 has source-level evidence for Decision Engine: policy config, schema, engine lifecycle and integration script are present in the repo.

## Not claimed

- No measured false-alarm reduction is claimed.
- No full runtime replay/test-suite pass is claimed without logs.
- No final SE/product-owner policy approval is claimed.
