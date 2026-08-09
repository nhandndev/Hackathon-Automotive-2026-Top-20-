#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/evidence/platform_ai_engineering"
RAW_DIR="$OUT_DIR/raw"
REPORT="$OUT_DIR/README_PLATFORM_AI_ENGINEERING_EVIDENCE.md"
HTML="$OUT_DIR/platform_ai_engineering_evidence.html"

mkdir -p "$RAW_DIR"

run_capture() {
  local name="$1"
  shift
  local outfile="$RAW_DIR/$name.txt"
  {
    echo "\$ $*"
    echo
    "$@" 2>&1
  } | tee "$outfile"
}

capture_shell() {
  local name="$1"
  local cmd="$2"
  local outfile="$RAW_DIR/$name.txt"
  {
    echo "\$ $cmd"
    echo
    bash -lc "$cmd"
  } 2>&1 | tee "$outfile"
}

cd "$ROOT_DIR"

echo "Collecting Platform + AI Engineering evidence into: $OUT_DIR"

capture_shell "01_decision_event_schema" \
  "nl -ba AI/core/decision_engine/schemas.py | sed -n '90,150p'"

capture_shell "02_ai_backend_boundary_router" \
  "nl -ba SE/BE/app/modules/ai_alerts/router.py | sed -n '1,230p'"

capture_shell "03_backend_to_carsky_mapper" \
  "nl -ba SE/BE/app/integrations/carsky/mapper.py | sed -n '1,245p'"

capture_shell "04_carsky_phase05_script" \
  "nl -ba SE/BE/scripts/carsky_phase05.py | sed -n '1,230p'"

capture_shell "05_copilot_report_api" \
  "nl -ba SE/FE/server.ts | sed -n '390,430p'; nl -ba SE/FE/server.ts | sed -n '720,760p'; nl -ba SE/FE/server.ts | sed -n '925,990p'"

capture_shell "06_copilot_doc_export" \
  "nl -ba SE/FE/src/components/CopilotFleetReportPage.tsx | sed -n '1080,1235p'"

capture_shell "07_fleet_dashboard_consumers" \
  "grep -RInE 'Decision events|No DecisionEvent|VehicleLiveView|TripDetailView|ranking-analysis|performance insights|saved_trips' SE/FE/src SE/FE/server.ts | head -120"

capture_shell "08_contract_docs" \
  "nl -ba SE/BE/docs/AI_CONTRACT_AND_CHANGELOG.md | sed -n '1,180p'; nl -ba AI/core/decision_engine/README.md | sed -n '1,95p'"

capture_shell "09_test_source_proves_consumers" \
  "nl -ba SE/BE/tests/test_ai_alerts.py | sed -n '1,260p'; nl -ba SE/BE/tests/test_carsky.py | sed -n '1,180p'; nl -ba SE/BE/tests/test_contract.py | sed -n '1,220p'"

if [ -x "SE/BE/.venv/bin/python" ]; then
  capture_shell "10_pytest_contract_carsky_alerts" \
    "cd SE/BE && .venv/bin/python -m pytest tests/test_contract.py tests/test_ai_alerts.py tests/test_carsky.py"
else
  capture_shell "10_pytest_contract_carsky_alerts" \
    "cd SE/BE && python3 -m pytest tests/test_contract.py tests/test_ai_alerts.py tests/test_carsky.py"
fi

capture_shell "11_apk_hmi_artifact" \
  "ls -lh SE/HMI/release/dms-hmi-realtime-vhal.apk; shasum -a 256 SE/HMI/release/dms-hmi-realtime-vhal.apk; unzip -p SE/HMI/release/dms-hmi-realtime-vhal.apk classes.dex | strings | grep -E 'DMS_HMI|PERF_VEHICLE_SPEED|CarPropertyManager|SAFE|CRITICAL|TTC|km/h' | head -80"

cat > "$REPORT" <<'MARKDOWN'
# Platform Utilization + AI Engineering Evidence Package

File này là evidence thật được collect từ source code, tests và artifact trong repo. Mục tiêu là chứng minh phần **AI Engineering capability được external consumer sử dụng qua interface hoặc artifact**, đồng thời nối với CarSky/HMI path.

## Evidence Summary

| Evidence | Chứng minh điều gì? | File output |
|---|---|---|
| DecisionEvent schema | AI capability có contract canonical, không phải text tự do | `raw/01_decision_event_schema.txt` |
| Backend boundary | SE Backend consume AI event qua API boundary | `raw/02_ai_backend_boundary_router.txt` |
| Backend -> CarSky mapper | CarSky integration consume AI/DMS state qua mapper | `raw/03_backend_to_carsky_mapper.txt` |
| CarSky script | Demo operator có script để push scenario critical/normal | `raw/04_carsky_phase05_script.txt` |
| Copilot Report API | User/report consume AI explanation qua `/api/copilot/report` | `raw/05_copilot_report_api.txt` |
| Word/DOC export | Report artifact được tạo để reviewer/business user consume | `raw/06_copilot_doc_export.txt` |
| Fleet Dashboard consumers | FE có views consume DecisionEvent/saved/local AI data | `raw/07_fleet_dashboard_consumers.txt` |
| Contract docs | AI/SE maintainer có docs làm contract và ownership boundary | `raw/08_contract_docs.txt` |
| Test source | Consumer flow có test source, không chỉ README | `raw/09_test_source_proves_consumers.txt` |
| Pytest result | Contract/alerts/CarSky tests chạy được trên source hiện tại | `raw/10_pytest_contract_carsky_alerts.txt` |
| Android HMI APK artifact | APK thật có CarProperty/HMI runtime strings | `raw/11_apk_hmi_artifact.txt` |

## External Consumer Proof

| External consumer | Interface / artifact họ consume | Evidence thật |
|---|---|---|
| SE Backend engineer | `/api/v1/alerts`, `/api/v1/alerts/snapshot`, `DecisionEventPayload` | `raw/02_ai_backend_boundary_router.txt`, `raw/10_pytest_contract_carsky_alerts.txt` |
| CarSky integration engineer | `CarSkySignalMapper`, `vehicle-speed-mux`, `carsky_phase05.py` | `raw/03_backend_to_carsky_mapper.txt`, `raw/04_carsky_phase05_script.txt`, `raw/10_pytest_contract_carsky_alerts.txt` |
| Fleet Manager | Fleet Dashboard views, saved/live trip context, DecisionEvent display | `raw/07_fleet_dashboard_consumers.txt` |
| AI Copilot report user | `/api/copilot/report`, validated/pending/unavailable fallback | `raw/05_copilot_report_api.txt` |
| Reviewer / business user | Word-compatible DOC report artifact | `raw/06_copilot_doc_export.txt` |
| AI/SE maintainer | AI contract docs + contract tests | `raw/08_contract_docs.txt`, `raw/09_test_source_proves_consumers.txt`, `raw/10_pytest_contract_carsky_alerts.txt` |
| Driver HMI / CarSky runtime | Android HMI APK reads CarProperty path | `raw/11_apk_hmi_artifact.txt` |

## Copy-Ready Claim

AI Engineering capability trong FPTU DMS Vision được external consumer sử dụng qua interface/artifact thật. AI core phát `DecisionEvent` và local telemetry contract; SE Backend consume qua `/api/v1/alerts`; CarSky integration consume qua `CarSkySignalMapper` và `carsky_phase05.py`; Fleet Manager consume qua Fleet Dashboard; AI Copilot report user consume qua `/api/copilot/report`; reviewer/business user consume qua Word/DOC export; AI/SE maintainer consume qua contract docs và pytest contract suite. Evidence nằm trong source, tests và APK artifact, không chỉ là mô tả trong slide.

## Caveat Đúng Sự Thật

Evidence này chứng minh source/test/artifact path. Với CarSky runtime, cần quay thêm same-event video nếu muốn claim full runtime chain: Backend publish -> Signal Watch `Vehicle.Speed` -> Bridge log -> Android logcat -> APK UI đổi cùng một event.
MARKDOWN

{
  cat <<'HTML_HEAD'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Platform + AI Engineering Evidence</title>
<style>
  body { margin: 0; background: #07111f; color: #e5eefb; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  main { max-width: 1180px; margin: 0 auto; padding: 42px; }
  h1 { font-size: 34px; margin: 0 0 10px; }
  h2 { margin-top: 34px; color: #67e8f9; }
  p, li { color: #cbd5e1; line-height: 1.55; }
  .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
  .card { background: #0f1b2d; border: 1px solid #27405f; border-radius: 14px; padding: 18px; }
  .card b { color: #f8fafc; }
  pre { background: #020617; border: 1px solid #1f3b57; border-radius: 12px; padding: 16px; overflow: auto; max-height: 430px; color: #dbeafe; font-size: 12px; line-height: 1.45; }
  code { color: #67e8f9; }
  .ok { color: #86efac; font-weight: 700; }
  .warn { color: #fda4af; font-weight: 700; }
</style>
</head>
<body><main>
<h1>Platform Utilization + AI Engineering Evidence</h1>
<p>This HTML is generated from real repository source, tests and artifacts. It is intended for screenshots/video evidence.</p>
<div class="grid">
  <div class="card"><b>Backend consumer</b><p><code>/api/v1/alerts</code> consumes canonical <code>DecisionEvent</code>.</p></div>
  <div class="card"><b>CarSky consumer</b><p><code>CarSkySignalMapper</code> maps AI/DMS state into <code>Vehicle.Speed</code> speed-mux.</p></div>
  <div class="card"><b>Report consumer</b><p><code>/api/copilot/report</code> and Word/DOC export expose AI explanation artifacts.</p></div>
  <div class="card"><b>Maintainer consumer</b><p>Contract docs and pytest suite verify interface compatibility.</p></div>
</div>
HTML_HEAD

  for file in "$RAW_DIR"/*.txt; do
    base="$(basename "$file")"
    echo "<h2>$base</h2>"
    echo "<pre>"
    sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g' "$file" | head -260
    echo "</pre>"
  done

  cat <<'HTML_TAIL'
</main></body></html>
HTML_TAIL
} > "$HTML"

echo
echo "Evidence package created:"
echo "  $REPORT"
echo "  $HTML"
echo "  $RAW_DIR"
