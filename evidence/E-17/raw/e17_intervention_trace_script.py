
from __future__ import annotations
import json, pathlib, sys, tempfile
sys.path.insert(0, "/Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE")
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings
client=TestClient(create_app(Settings(APP_ENV="test", DATASET_DIR=pathlib.Path(tempfile.mkdtemp())/"dataset", OUTPUT_SUBMISSION_DIR=pathlib.Path(tempfile.mkdtemp())/"submissions", AI_SOURCE_MODE="file", _env_file=None)))
rows=[]
payload={"type":"stop","trip_id":"T02-Sample","message":"Operator requests safety stop review at next safe location","timestamp_ms":123456}
r=client.post('/api/v1/alerts/interventions',json=payload); rows.append({'step':'post_intervention','status_code':r.status_code,'body':r.json()})
r=client.get('/api/v1/alerts/interventions/pending?trip_id=T02-Sample'); rows.append({'step':'poll_pending_first','status_code':r.status_code,'body':r.json()})
r=client.get('/api/v1/alerts/interventions/pending?trip_id=T02-Sample'); rows.append({'step':'poll_pending_second_consumed','status_code':r.status_code,'body':r.json()})
# Probe common actuator-like paths: these should not exist as Backend vehicle-control APIs.
for path in ['/api/v1/vehicle/brake','/api/v1/vehicle/actuate','/api/v1/alerts/actuate']:
    r=client.post(path,json={})
    rows.append({'step':'probe_no_vehicle_actuator_endpoint','path':path,'status_code':r.status_code,'body':r.json() if r.headers.get('content-type','').startswith('application/json') else r.text})
print('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows))
