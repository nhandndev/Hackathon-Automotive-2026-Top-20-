# E-36 - Long-Run Load Test

Generated: `2026-08-10T04:20:05Z`  
Commit: `44e6cb3224a58fc0a5d804fc8fab5e233f89e477`

## Status

**PARTIAL / SHORT LOAD SMOKE EXECUTED; 4-8H LONG-RUN NOT EXECUTED**

## What Was Run

A real in-process FastAPI `TestClient` replay sent `1200` `/api/v1/alerts/snapshot` payloads into the backend and verified the latest snapshot endpoint afterward.

## Observed Result

```json
{
  "generated_at": "2026-08-10T04:20:05.078383+00:00",
  "duration_sec": 1.191,
  "frames_sent": 1200,
  "errors": 0,
  "effective_fps": 1007.53,
  "latest_snapshot_status": 200,
  "latest_frame_id": 1199,
  "trip_count": 1,
  "rss_mb_final": 99.05,
  "scope": "short in-process load smoke, not 4-8h long-run"
}
```

## Evidence Files

- `raw/e36_load_smoke.py`
- `raw/load_smoke_command.log`
- `raw/load_smoke_trace.jsonl`
- `derived/load_smoke_summary.json`

## Limitation

This is not the requested 4-8 hour long-run. It is useful smoke evidence for throughput and state handling, but final E-36 requires a real controlled replay over 4-8 hours with memory, queue, drops, reconnect, and restart logs.
