#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "fleetdashboard_android_hmi"

SOURCE_FILES = [
    "SE/FE/package.json",
    "SE/FE/server.ts",
    "SE/FE/src/App.tsx",
    "SE/FE/src/data/btcTripData.ts",
    "SE/FE/src/components/CopilotFleetReportPage.tsx",
    "SE/BE/app/integrations/carsky/mapper.py",
    "SE/BE/app/integrations/carsky/client.py",
    "SE/BE/app/integrations/carsky/service.py",
    "SE/BE/app/modules/ai_alerts/router.py",
    "SE/BE/carsky/dms_hmi_bridge_speed_passthrough.lua",
    "SE/BE/carsky/dms_hmi_bridge.lua",
    "SE/BE/carsky/dms_hmi_bridge_dual_push.lua",
    "SE/HMI/README.md",
    "SE/HMI/app/src/main/AndroidManifest.xml",
    "SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java",
    "SE/HMI/vhal-vsock-relay/README.md",
]

PATTERNS = {
    "saved_trip_loading": [
        r"saved_trips",
        r"parseSavedTrip",
        r"runtime_status",
        r"Infinity",
    ],
    "bedrock_env_and_validation": [
        r"AWS_BEARER_TOKEN_BEDROCK",
        r"BEDROCK_API_KEY",
        r"ai_status",
        r"validated",
        r"unavailable",
        r"SE/BE|BE/.env|\.\./BE/\.env",
    ],
    "word_doc_export": [
        r"handleExportWord",
        r"application/msword",
        r"\.doc",
        r"Word",
    ],
    "speed_mux_backend": [
        r"vehicle-speed-mux",
        r"Vehicle.Speed",
        r"_mux",
        r"41",
        r"50",
    ],
    "android_hmi_vhal": [
        r"PERF_VEHICLE_SPEED",
        r"CarPropertyManager",
        r"decodeMultiplex",
        r"mux decimal",
        r"V2.2",
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_command(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout
    except Exception as exc:  # noqa: BLE001 - evidence script should capture failures.
        return 999, f"{type(exc).__name__}: {exc}"


def collect_manifest() -> str:
    lines = [
        "# Source Manifest",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Repo root: {ROOT}",
        "",
        "| Path | Exists | SHA-256 | Bytes |",
        "|---|---:|---|---:|",
    ]
    for item in SOURCE_FILES:
        path = ROOT / item
        if path.exists():
            lines.append(f"| `{item}` | yes | `{sha256(path)}` | {path.stat().st_size} |")
        else:
            lines.append(f"| `{item}` | no |  |  |")
    return "\n".join(lines) + "\n"


def find_snippets() -> str:
    sections: list[str] = ["# Source Snippets", ""]
    for group, patterns in PATTERNS.items():
        sections.extend([f"## {group}", ""])
        matched_any = False
        for item in SOURCE_FILES:
            path = ROOT / item
            if not path.exists() or path.suffix.lower() not in {".ts", ".tsx", ".py", ".java", ".lua", ".md", ".json", ".xml"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            hits: list[str] = []
            for idx, line in enumerate(text, start=1):
                if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns):
                    cleaned = line.strip()
                    if len(cleaned) > 180:
                        cleaned = cleaned[:177] + "..."
                    hits.append(f"- `{item}:{idx}` `{cleaned}`")
            if hits:
                matched_any = True
                sections.extend(hits[:16])
        if not matched_any:
            sections.append("- No source snippet found.")
        sections.append("")
    return "\n".join(sections) + "\n"


def collect_hmi_artifacts() -> str:
    candidates = [
        "SE/HMI/release/dms-hmi-realtime-vhal.apk",
        "SE/HMI/release/adb_install_realtime_hmi.txt",
        "SE/HMI/release/install_hmi_realtime_adb.sh",
        "SE/HMI/app/build/outputs/apk/debug/app-debug.apk",
        "SE/HMI/vhal-vsock-relay/target/aarch64-linux-android/release/vhal-vsock-relay",
        "SE/HMI/vhal-vsock-relay/vhal-vsock-relay",
    ]
    lines = [
        "# HMI / APK / Relay Artifacts",
        "",
        "| Artifact | Exists | SHA-256 | Bytes |",
        "|---|---:|---|---:|",
    ]
    for item in candidates:
        path = ROOT / item
        if path.exists():
            lines.append(f"| `{item}` | yes | `{sha256(path)}` | {path.stat().st_size} |")
        else:
            lines.append(f"| `{item}` | no |  |  |")
    lines.extend([
        "",
        "## APK-derived static evidence",
        "",
        "This section is extracted from the APK artifact itself, not only from source files.",
        "",
    ])
    lines.extend(apk_static_evidence(ROOT / "SE/HMI/release/dms-hmi-realtime-vhal.apk"))
    return "\n".join(lines) + "\n"


def apk_static_evidence(apk_path: Path) -> list[str]:
    if not apk_path.exists():
        return ["APK not found; cannot extract APK-derived evidence.", ""]

    lines: list[str] = [
        f"APK: `{rel(apk_path)}`",
        f"APK SHA-256: `{sha256(apk_path)}`",
        f"APK bytes: `{apk_path.stat().st_size}`",
        "",
        "### ZIP entries",
        "",
        "| Entry | Bytes | Compressed |",
        "|---|---:|---:|",
    ]
    dex_bytes = b""
    sf_text = ""
    mf_text = ""
    with zipfile.ZipFile(apk_path) as zf:
        for info in zf.infolist():
            lines.append(f"| `{info.filename}` | {info.file_size} | {info.compress_size} |")
        if "classes.dex" in zf.namelist():
            dex_bytes = zf.read("classes.dex")
        if "META-INF/ANDROIDD.SF" in zf.namelist():
            sf_text = zf.read("META-INF/ANDROIDD.SF").decode("utf-8", errors="replace")
        if "META-INF/MANIFEST.MF" in zf.namelist():
            mf_text = zf.read("META-INF/MANIFEST.MF").decode("utf-8", errors="replace")

    lines.extend([
        "",
        "### APK signing metadata",
        "",
        "```text",
        "\n".join((sf_text or mf_text or "No META-INF signing text found.").splitlines()[:24]),
        "```",
        "",
        "### DEX strings relevant to HMI runtime",
        "",
    ])

    interesting = [
        "DMS_HMI",
        "vn/fpt/dms/hmi/MainActivity",
        "PERF_VEHICLE_SPEED",
        "CarPropertyManager",
        "Registered DMS VHAL transport",
        "mux decimal raw",
        "mux raw",
        "mux speed",
        "V2.2 SPEED MUX",
        "V2.1 CUSTOM VHAL",
        "SAFE",
        "CRITICAL",
        "TTC",
        "km/h",
    ]
    found = []
    if dex_bytes:
        dex_text = "\n".join(run_strings(dex_bytes))
        for token in interesting:
            if token in dex_text:
                found.append(f"- `{token}`: found in `classes.dex`")
            else:
                found.append(f"- `{token}`: not found in `classes.dex`")
    else:
        found.append("- `classes.dex`: not found in APK.")
    lines.extend(found)

    source_tag = source_build_tag()
    apk_tag = "V2.2 SPEED MUX" if any("`V2.2 SPEED MUX`: found" in x for x in found) else ""
    if not apk_tag and any("`V2.1 CUSTOM VHAL`: found" in x for x in found):
        apk_tag = "V2.1 CUSTOM VHAL"
    lines.extend([
        "",
        "### APK/source version consistency",
        "",
        f"- Source `BUILD_TAG`: `{source_tag or 'not found'}`",
        f"- APK `classes.dex` tag: `{apk_tag or 'not found'}`",
    ])
    if source_tag and apk_tag and source_tag != apk_tag:
        lines.append("- Result: `MISMATCH`; rebuild and reinstall APK before claiming the source version is deployed.")
    elif source_tag and apk_tag:
        lines.append("- Result: `MATCH`.")
    else:
        lines.append("- Result: `INCONCLUSIVE`; version tag not found in one side.")
    lines.append("")
    return lines


def run_strings(blob: bytes) -> list[str]:
    text = blob.decode("latin-1", errors="ignore")
    return re.findall(r"[\x20-\x7e]{4,}", text)


def source_build_tag() -> str:
    source = ROOT / "SE/HMI/app/src/main/java/vn/fpt/dms/hmi/MainActivity.java"
    if not source.exists():
        return ""
    match = re.search(r'BUILD_TAG\s*=\s*"([^"]+)"', source.read_text(encoding="utf-8", errors="replace"))
    return match.group(1) if match else ""


def collect_fe_checks(run_checks: bool) -> str:
    lines = ["# FE Checks", ""]
    fe_dir = ROOT / "SE" / "FE"
    if not run_checks:
        lines.append("Not run. Re-run with `--run-checks` to execute `npm run lint` and `npm run build`.")
        return "\n".join(lines) + "\n"
    if not shutil.which("npm"):
        lines.append("npm not found.")
        return "\n".join(lines) + "\n"
    for cmd in [["npm", "run", "lint"], ["npm", "run", "build"]]:
        code, out = run_command(cmd, fe_dir, timeout=240)
        lines.extend([
            f"## {' '.join(cmd)}",
            "",
            f"Exit code: {code}",
            "",
            "```text",
            out[-12000:],
            "```",
            "",
        ])
    return "\n".join(lines) + "\n"


def manual_todo() -> str:
    return """# Manual Capture TODO

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
"""


def summary() -> str:
    return """# Evidence Summary — Fleet Dashboard + Android HMI

This package was generated from local source files. It does not replace manual screenshots/videos from the running demo.

## Evidence Status

| Evidence ID | Scope | Current status | Generated evidence | Manual evidence still needed |
|---|---|---|---|---|
| E-19 | Copilot grounded output | Pending formal audit | Source snippets for validation/fallback | Golden question set + raw Bedrock outputs |
| E-20 | Copilot latency/cost/failure | Demo sample only | Server/source snippets | Latency logs, timeout/provider-down traces |
| E-21 | Report export | Implemented DOC path | Source snippets for Word/DOC export | Exported DOC files + visual review |
| E-22 | Fleet Dashboard workflow | Implemented | FE source manifest/build checks if run | Screen recording of workflow |
| E-23 | Honest fallback | Partial/source-supported | Fallback snippets | Screenshots for API down/no trips/Bedrock fail |
| E-24 | CarSky/KUKSA/VHAL/APK path | Artifact-backed / deployment-dependent | Mapper snippets + APK hash/DEX/signing evidence | Same-event Signal Watch + bridge log + logcat + APK video |

## Report Wording

Use:

```text
Fleet Dashboard evidence is source/build backed. Android HMI evidence must be APK-artifact backed first: APK SHA-256, ZIP entries, signing metadata, DEX strings, installed APK logcat, and UI video for the same event. Vehicle.Speed / PERF_VEHICLE_SPEED speed-mux is the verified demo transport. Custom DMS CarProperty IDs are not the final demo path.
```

Avoid:

```text
PDF export completed.
Custom DMS CarProperty fully production-ready.
Signal Watch alone proves Android HMI.
Source code alone proves the installed APK version.
Bedrock creates canonical metrics.
```
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect FleetDashboard + Android HMI evidence package.")
    parser.add_argument("--run-checks", action="store_true", help="Run FE npm lint/build and capture output.")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "EVIDENCE_SUMMARY.md", summary())
    write(OUT / "SOURCE_MANIFEST.md", collect_manifest())
    write(OUT / "SOURCE_SNIPPETS.md", find_snippets())
    write(OUT / "HMI_APK_ARTIFACTS.md", collect_hmi_artifacts())
    write(OUT / "FE_CHECKS.md", collect_fe_checks(args.run_checks))
    write(OUT / "MANUAL_CAPTURE_TODO.md", manual_todo())

    print(f"Evidence package written to: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
