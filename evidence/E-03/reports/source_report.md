# Source Report - E-03 Canonical DecisionEvent Contract

| Evidence | Source | Ghi chú |
|---|---|---|
| `decision_event_api_payload.schema.json` | `SE/BE/app/modules/ai_alerts/router.py` | API payload contract cho `/api/v1/alerts` |
| `live_snapshot_payload.schema.json` | `SE/BE/app/modules/ai_alerts/router.py` | Live snapshot contract cho `/api/v1/alerts/snapshot` |
| `openapi_alerts_subset.json` | FastAPI `app.openapi()` | OpenAPI subset chỉ chứa alerts boundary |
| `golden_payloads/*.json` | TestClient payload thật | Valid, invalid và live snapshot critical payload |
| `raw/api_trace.jsonl` | FastAPI TestClient | Ghi status/body thật cho accepted, duplicate, mismatch, validation error, snapshot |
| `raw/pytest_contract_ai_alerts.log` | `pytest tests/test_contract.py tests/test_ai_alerts.py` | Regression tests cho AI contract và alert API |

## Kết quả

- Valid DecisionEvent accepted: `True`.
- Duplicate idempotency preserved: `True`.
- Invalid payload/header rejected: `True`.
- Live snapshot accepted: `True`.
- Test suite passed: `True`.

## Trạng thái

**DONE / SOURCE, SCHEMA, API TRACE, TEST VERIFIED**

## Chưa làm

- Chưa có reviewer sign-off độc lập cho schema version freeze.
- Chưa export full public OpenAPI bundle cho toàn bộ Backend; artifact này chỉ scope alerts/DecisionEvent boundary.
