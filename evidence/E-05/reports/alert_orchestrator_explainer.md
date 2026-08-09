# E-05 - Alert Orchestrator là gì?

E-05 không phải là accuracy của Challenge 1/2/3.

Nó là bằng chứng cho tầng **Decision Engine / Alert Orchestrator**: tầng quyết định khi nào một prediction/risk thật sự được gửi thành cảnh báo cho Fleet Dashboard / CarSky / AI Desktop.

## Input của Orchestrator

Từ AI pipeline:

- `predicted_ttc`
- `driver_state`
- `alertness_score`
- `continuous_eye_closure_ms`
- `perclos_30s`
- speed/accel
- C3 risk/safe score

## Orchestrator làm gì?

Nó lọc cảnh báo bằng:

- persistence: nguy hiểm phải kéo dài đủ lâu,
- cooldown: tránh spam cảnh báo liên tục,
- recovery: chỉ resolve khi trạng thái an toàn đủ lâu,
- severity: watch / warning / critical,
- policy thresholds từ `AI/configs/decision_engine.yaml`.

## Evidence trong folder này

| File | Ý nghĩa |
|---|---|
| `policy_config.yaml` | Snapshot ngưỡng chính |
| `state_trace.jsonl` | Trace nguồn state/event/transport |
| `orchestrator_junit.xml` | JUnit-style static evidence |
| `source_report.md` | Evidence lấy từ đâu |

## Cần owner review

Tâm/owner cần xác nhận policy có đúng ý đồ demo/sản phẩm không, ví dụ:

- microsleep cần critical ngay hay cần persistence,
- drowsy warning sau bao lâu,
- TTC critical cooldown bao lâu,
- có cho alert khi xe đang đứng yên không.
