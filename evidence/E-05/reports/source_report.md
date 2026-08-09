# Source Report - E-05 Alert Orchestrator

| Evidence | Source | Ghi chú |
|---|---|---|
| `policy_config.yaml` | `HACKATHON/AI/configs/decision_engine.yaml` | Snapshot rút gọn các ngưỡng chính |
| `state_trace.jsonl` | `HACKATHON/AI/core/decision_engine/`, `HACKATHON/AI/integrations/se_client.py` | Trace nguồn state/event/transport |
| `orchestrator_junit.xml` | Static source evidence | JUnit-style placeholder evidence |

## Chưa làm

- Chưa có dynamic test thật bắn event qua backend trong CI.
- Owner/Tâm cần review policy có đúng ý đồ thiết kế không.
