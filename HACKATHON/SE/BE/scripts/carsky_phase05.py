#!/usr/bin/env python3
"""Operate an existing CarSky deployment without creating/deleting resources.

This helper is for preflight and fallback scenarios. The real end-to-end path
is AI DecisionEvent -> Backend /api/v1/alerts -> CarSkyPublisher.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings

SCENARIOS: dict[str, dict[str, list[dict[str, Any]]]] = {
    "normal": {"signals": [
        {"path": "Vehicle.Driver.State", "value": "alert"},
        {"path": "Vehicle.Driver.AlertnessScore", "value": 0.95},
        {"path": "Vehicle.ADAS.MinTTC", "value": 10.0},
        {"path": "Vehicle.ADAS.FinalRiskScore", "value": 5.0},
        {"path": "Vehicle.ADAS.CriticalAlert", "value": False},
        {"path": "Vehicle.ADAS.DisplaySeverity", "value": "SAFE"},
        {"path": "Vehicle.ADAS.AlertReasonCode", "value": "NONE"},
        {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "NONE"},
        {"path": "Vehicle.ADAS.EventTransition", "value": "END"},
        {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
        {"path": "Vehicle.ADAS.DataAgeMs", "value": 40},
    ]},
    "warning": {"signals": [
        {"path": "Vehicle.Driver.State", "value": "distracted"},
        {"path": "Vehicle.Driver.AlertnessScore", "value": 0.45},
        {"path": "Vehicle.ADAS.MinTTC", "value": 3.0},
        {"path": "Vehicle.ADAS.FinalRiskScore", "value": 55.0},
        {"path": "Vehicle.ADAS.CriticalAlert", "value": False},
        {"path": "Vehicle.ADAS.DisplaySeverity", "value": "WARNING"},
        {"path": "Vehicle.ADAS.AlertReasonCode", "value": "DISTRACTED"},
        {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "FOCUS_FORWARD"},
        {"path": "Vehicle.ADAS.EventTransition", "value": "START"},
        {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
        {"path": "Vehicle.ADAS.DataAgeMs", "value": 40},
    ]},
    "critical": {"signals": [
        {"path": "Vehicle.Driver.State", "value": "microsleep"},
        {"path": "Vehicle.Driver.AlertnessScore", "value": 0.15},
        {"path": "Vehicle.ADAS.MinTTC", "value": 1.2},
        {"path": "Vehicle.ADAS.FinalRiskScore", "value": 88.0},
        {"path": "Vehicle.ADAS.CriticalAlert", "value": True},
        {"path": "Vehicle.ADAS.DisplaySeverity", "value": "CRITICAL"},
        {"path": "Vehicle.ADAS.AlertReasonCode", "value": "TTC_CRITICAL"},
        {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "BRAKE_SAFE"},
        {"path": "Vehicle.ADAS.EventTransition", "value": "START"},
        {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
        {"path": "Vehicle.ADAS.DataAgeMs", "value": 40},
    ]},
}


class Phase05Operator:
    def __init__(self) -> None:
        required = {
            "CARSKY_BASE_URL": settings.CARSKY_BASE_URL,
            "CARSKY_API_KEY": settings.CARSKY_API_KEY,
            "CARSKY_ROOM_ID": settings.CARSKY_ROOM_ID,
            "CARSKY_NODE_KEY": settings.CARSKY_NODE_KEY,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SystemExit(f"Missing required .env values: {', '.join(missing)}")
        self.base_url = settings.CARSKY_BASE_URL.rstrip("/")
        self.room_id = settings.CARSKY_ROOM_ID
        self.signal_node = settings.CARSKY_NODE_KEY
        self.android_node = settings.CARSKY_ANDROID_NODE_KEY
        header = "X-API-Key" if settings.CARSKY_AUTH_MODE == "x-api-key" else "Authorization"
        token = settings.CARSKY_API_KEY if header == "X-API-Key" else f"Bearer {settings.CARSKY_API_KEY}"
        self.client = httpx.Client(timeout=30, headers={header: token})

    def close(self) -> None:
        self.client.close()

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        attempts = max(1, settings.CARSKY_MAX_RETRIES + 1)
        for attempt in range(attempts):
            try:
                response = self.client.request(method, f"{self.base_url}{path}", **kwargs)
                response.raise_for_status()
                return response
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                retryable = isinstance(exc, httpx.TransportError) or (
                    isinstance(exc, httpx.HTTPStatusError)
                    and (exc.response.status_code == 429 or exc.response.status_code >= 500)
                )
                if retryable and attempt < attempts - 1:
                    time.sleep(0.25 * (2**attempt))
                    continue
                if isinstance(exc, httpx.HTTPStatusError):
                    try:
                        details = exc.response.json()
                    except ValueError:
                        details = exc.response.text[:500]
                    raise RuntimeError(
                        f"CarSky {exc.response.status_code} for {path} "
                        f"after {attempt + 1} attempt(s): {details}"
                    ) from exc
                raise RuntimeError(
                    f"CarSky transport failure for {path} "
                    f"after {attempt + 1} attempt(s): {exc}"
                ) from exc
        raise RuntimeError("Unreachable CarSky retry state")

    def status(self) -> Any:
        return self.request("GET", f"/api/v1/deployments/{self.room_id}/status").json()

    def nodes(self) -> Any:
        return self.request("GET", f"/api/v1/deployments/{self.room_id}/nodes").json()

    def adb_tunnel(self) -> Any:
        return self.request(
            "GET", f"/api/v1/deployments/{self.room_id}/adb-tunnel"
        ).json()

    def scenario(self, name: str) -> Any:
        return self.request(
            "POST", f"/api/v1/signals/{self.room_id}/{self.signal_node}/actuate",
            json=SCENARIOS[name],
        ).json()

    def adb(self, command: str, *, binary: bool = False) -> httpx.Response:
        if not self.android_node:
            raise SystemExit("CARSKY_ANDROID_NODE_KEY is required for ADB commands")
        return self.request(
            "POST", f"/api/v1/deployments/{self.room_id}/adb-exec/{self.android_node}",
            json={"command": command, "binary": binary},
        )

    def install_apk(self, apk: Path) -> list[Any]:
        encoded = base64.b64encode(apk.read_bytes()).decode("ascii")
        output: list[Any] = []
        output.append(self.adb(
            "rm -f /data/local/tmp/dms-hmi.part.* "
            "/data/local/tmp/dms-hmi.b64 /data/local/tmp/dms-hmi.apk"
        ).json())
        for index, offset in enumerate(range(0, len(encoded), 1800)):
            chunk = encoded[offset:offset + 1800]
            output.append(self.adb(
                f"printf '%s' '{chunk}' > /data/local/tmp/dms-hmi.part.{index:04d}"
            ).json())
        output.append(self.adb(
            "cat /data/local/tmp/dms-hmi.part.* > /data/local/tmp/dms-hmi.b64"
        ).json())
        output.append(self.adb("base64 -d /data/local/tmp/dms-hmi.b64 > /data/local/tmp/dms-hmi.apk").json())
        output.append(self.adb("pm install -r -d -t /data/local/tmp/dms-hmi.apk").json())
        output.append(self.adb("am start -n vn.fpt.dms.hmi/.MainActivity").json())
        return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("nodes")
    sub.add_parser("adb-tunnel")
    scenario = sub.add_parser("scenario")
    scenario.add_argument("name", choices=sorted(SCENARIOS))
    install = sub.add_parser("install-apk")
    install.add_argument("apk", type=Path)
    args = parser.parse_args()
    operator = Phase05Operator()
    try:
        if args.command == "status": result = operator.status()
        elif args.command == "nodes": result = operator.nodes()
        elif args.command == "adb-tunnel": result = operator.adb_tunnel()
        elif args.command == "scenario": result = operator.scenario(args.name)
        else: result = operator.install_apk(args.apk.resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        operator.close()


if __name__ == "__main__":
    main()
