# Source Report - E-16 Failure Handling

| Evidence | Source | Ghi chú |
|---|---|---|
| `raw/failure_trace.jsonl` | FastAPI TestClient | Malformed payload, idempotency mismatch, missing snapshot and recovery path |
| `raw/carsky_failure_tests.log` | `tests/test_carsky.py` | Auth failure/no retry and finite AI value preservation |
| `raw/carsky_runtime_fallback_command.json` | `carsky_phase05.py scenario critical` | Real CarSky fallback command evidence |
| `derived/fault_matrix.csv` | Generated from observed traces | Reviewer-friendly fault matrix |
| `raw/source_snippets/failure_handling_sources.log` | BE/FE/HMI source | Bedrock fallback, offline camera/saved telemetry and VHAL fallback locators |
| `screenshots/*.png` | Headless Chrome attempt | UI fallback screenshots if environment allowed capture |

## Kết quả

- API rejects malformed input: `True`.
- API recovers and accepts valid event after rejected errors: `True`.
- CarSky failure tests passed: `True`.
- UI screenshot captured: `True`.

## Trạng thái

**PARTIAL / API, CARSKY, FALLBACK SOURCES VERIFIED; UI SCREENSHOT CAPTURED**

## Caveat

This evidence demonstrates failure handling paths and safe fallback behavior. It does not claim exhaustive chaos testing, long-run reliability, or production-grade provider SLA.
