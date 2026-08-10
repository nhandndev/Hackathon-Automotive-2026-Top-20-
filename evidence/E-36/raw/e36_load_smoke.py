from __future__ import annotations
import json, os, resource, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'HACKATHON'
sys.path.insert(0, str(ROOT / 'SE' / 'BE'))
os.environ.setdefault('CARSKY_ENABLED', '0')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
out = Path(__file__).resolve().parents[1]
raw = out / 'raw'
derived = out / 'derived'
raw.mkdir(parents=True, exist_ok=True)
derived.mkdir(parents=True, exist_ok=True)
trace = raw / 'load_smoke_trace.jsonl'
start = time.perf_counter()
errors = 0
frames = 1200
with trace.open('w', encoding='utf-8') as f:
    for i in range(frames):
        payload = {
            'schema_version': '1.0',
            'trip_id': 'E36-Load-Smoke',
            'frame_id': i,
            'trip_timestamp_ms': i * 50,
            'speed_kmh': 40 + (i % 20),
            'predicted_ttc_sec': 1.2 if i % 50 == 0 else 10.0,
            'risk_score': 88 if i % 50 == 0 else 20,
            'safe_driving_score': 12 if i % 50 == 0 else 80,
            'driver_state': 'microsleep' if i % 100 == 0 else 'alert',
            'driver_confidence': 0.9,
            'alertness_score': 0.2 if i % 100 == 0 else 1.0,
        }
        t0 = time.perf_counter()
        r = client.post('/api/v1/alerts/snapshot', json=payload)
        dt = (time.perf_counter() - t0) * 1000
        if r.status_code != 202:
            errors += 1
        if i % 100 == 0 or r.status_code != 202:
            f.write(json.dumps({
                'ts': datetime.now(timezone.utc).isoformat(),
                'frame_id': i,
                'status_code': r.status_code,
                'latency_ms': round(dt, 3),
                'rss_mb': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024*1024 if sys.platform == 'darwin' else 1024), 2),
            }) + '\n')
end = time.perf_counter()
snapshot = client.get('/api/v1/alerts/snapshot?trip_id=E36-Load-Smoke')
trips = client.get('/api/v1/alerts/trips')
summary = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'duration_sec': round(end-start, 3),
    'frames_sent': frames,
    'errors': errors,
    'effective_fps': round(frames/(end-start), 2),
    'latest_snapshot_status': snapshot.status_code,
    'latest_frame_id': snapshot.json().get('frame_id') if snapshot.status_code == 200 else None,
    'trip_count': trips.json().get('count') if trips.status_code == 200 else None,
    'rss_mb_final': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024*1024 if sys.platform == 'darwin' else 1024), 2),
    'scope': 'short in-process load smoke, not 4-8h long-run'
}
(derived / 'load_smoke_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
