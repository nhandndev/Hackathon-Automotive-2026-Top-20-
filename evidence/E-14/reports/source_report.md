# Source Report - E-14 Backend Reliability Boundary

| Evidence | Source | Ghi chú |
|---|---|---|
| `raw/backend_contract.log` | FastAPI TestClient script | Captures dedup, recent alerts, WebSocket broadcast and simulated restart |
| `derived/websocket_trace.jsonl` | `/api/v1/alerts/live` TestClient websocket | Same event broadcast evidence |
| `reports/restart_test.md` | Fresh app instance after alert ingestion | Documents in-memory state loss after restart |
| `raw/source_snippets/backend_reliability_boundary.log` | `router.py`, tests, app startup | Source locator for memory store and WebSocket boundary |

## Kết quả

- Idempotency/dedup verified: `True`.
- WebSocket broadcast verified: `True`.
- Restart in-memory state limitation verified: `True`.

## Trạng thái

**DONE / CONTRACT, DEDUP, WEBSOCKET, RESTART LIMIT VERIFIED**

## Caveat

Backend currently keeps recent alerts/live trips in process memory. This is acceptable for demo evidence but not a durable production reliability claim.
