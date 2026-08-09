# Manual Capture TODO

## E-21 Word/DOC Export

- [ ] Export Safety Detail DOC.
- [ ] Export Safety Overview DOC.
- [ ] Export Maintenance Detail or Overview DOC.
- [ ] Open exported DOC and screenshot readable content.
- [ ] Confirm PDF is not claimed as final demo scope.

## E-22 Fleet Dashboard Workflow

- [ ] Record Dashboard list/map.
- [ ] Open Trip Detail.
- [ ] Open Ranking / Ranking Analysis.
- [ ] Open Performance Insights.
- [ ] Open Copilot Report.
- [ ] Export Word/DOC.
- [ ] Capture that saved trips display when JSON exists.

## E-23 Honest Fallback

- [ ] Bedrock token expired/wrong: report keeps JSON/local AI baseline.
- [ ] API down/no trips: UI shows degraded/empty state, not fake SAFE.
- [ ] Camera/live frame offline: UI shows waiting/offline state.

## E-24 CarSky/KUKSA/VHAL/APK Same-Event Chain

- [ ] Confirm installed APK package/version/hash before the scenario:

```bash
pm path vn.fpt.dms.hmi
dumpsys package vn.fpt.dms.hmi | grep -E "versionName|versionCode|firstInstallTime|lastUpdateTime"
sha256sum /data/app/*/vn.fpt.dms.hmi*/base.apk 2>/dev/null || true
```

- [ ] Backend publish payload with `Vehicle.Speed` mux values.
- [ ] Signal Watch screenshot shows `Vehicle.Speed` values in `41.xxx` to `50.xxx`.
- [ ] HMI Bridge log shows forwarding to `PERF_VEHICLE_SPEED`.
- [ ] Android logcat:

```bash
logcat -d -s DMS_HMI:I AndroidRuntime:E CarPropertyManager:E | tail -160
```

- [ ] APK UI video/screenshot shows risk/severity/TTC/action/speed/safe score update.

Expected log patterns:

```text
Registered DMS VHAL transport with speed-mux
mux decimal raw=41.xxx group=41 payload=...
prop 0x11600207=...
```
