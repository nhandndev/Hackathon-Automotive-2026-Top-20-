#!/usr/bin/env python3
"""Small CarSky helper for Phase 05 manual validation.

Commands:
  status
  nodes
  signals
  values
  send-safe
  send-warning
  send-critical
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib import request, error, parse


DEFAULT_ROOM_ID = "97fg4ghsgeo9w4bvze3qq"
DEFAULT_DEVICE_NAMES = ("FPTU DMS Vision", "test")
DMS_VALUE_PATHS = [
    "Vehicle.Driver.State",
    "Vehicle.Driver.AlertnessScore",
    "Vehicle.ADAS.MinTTC",
    "Vehicle.ADAS.FinalRiskScore",
    "Vehicle.ADAS.CriticalAlert",
    "Vehicle.Speed",
    "Vehicle.SpeedLimit",
    "Vehicle.ADAS.Headway",
    "Vehicle.ADAS.DisplaySeverity",
    "Vehicle.ADAS.AlertReasonCode",
    "Vehicle.ADAS.RecommendedActionCode",
    "Vehicle.ADAS.EventTransition",
    "Vehicle.ADAS.AIStatus",
    "Vehicle.ADAS.DataAgeMs",
]


def load_env() -> None:
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def base_url() -> str:
    return os.environ.get("CARSKY_BASE_URL", "https://hackathon-1.carsky.io").rstrip("/")


def auth_headers() -> dict[str, str]:
    token = os.environ.get("CARSKY_API_KEY", "")
    mode = os.environ.get("CARSKY_AUTH_MODE", "bearer").lower()
    headers = {"Content-Type": "application/json"}
    if token:
        if mode == "x-api-key":
            headers["X-API-Key"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def api(method: str, path: str, body: Any | None = None) -> Any:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = request.Request(
        base_url() + path,
        data=data,
        method=method,
        headers=auth_headers(),
    )
    try:
        with request.urlopen(req, timeout=float(os.environ.get("CARSKY_TIMEOUT_SEC", "10"))) as res:
            payload = res.read().decode("utf-8")
    except error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        print(payload, file=sys.stderr)
        raise SystemExit(exc.code)
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return payload


def find_active_room_id() -> str | None:
    candidates = []
    configured_device = os.environ.get("CARSKY_DEVICE_NAME")
    if configured_device:
        candidates.append(configured_device)
    candidates.extend(DEFAULT_DEVICE_NAMES)

    for device in candidates:
        q = parse.urlencode({"device": device})
        try:
            deployments = api("GET", f"/api/v1/deployments/find?{q}")
        except SystemExit:
            continue
        for item in deployments or []:
            if item.get("status") in {"RUNNING", "DEPLOYING", "PENDING"}:
                return item.get("roomId")
    return None


def room_id() -> str:
    configured = os.environ.get("CARSKY_ROOM_ID")
    if configured:
        try:
            status = api("GET", f"/api/v1/deployments/{configured}/status")
            if status.get("status") != "NOT_FOUND":
                return configured
        except SystemExit:
            pass

    discovered = find_active_room_id()
    return discovered or configured or DEFAULT_ROOM_ID


def discover_signal_node() -> str:
    configured = os.environ.get("CARSKY_NODE_KEY")
    if configured and configured != "<signal-node-key>":
        return configured
    signal_sources = api("GET", f"/api/v1/signals/{room_id()}")
    for node in signal_sources.get("nodes", []):
        if node.get("kind") == "kuksa" or node.get("key") == "dms-signal-broker":
            return node["key"]
    nodes = api("GET", f"/api/v1/deployments/{room_id()}/nodes")
    for node in nodes:
        if node.get("displayName") == "DMS Signal Broker" or node.get("nodeType") == "kuksa-databroker":
            return node["name"]
    raise SystemExit("Không tìm thấy DMS Signal Broker node. Chạy command `nodes` để kiểm tra.")


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


SAFE = [
    {"path": "Vehicle.Driver.State", "value": "alert"},
    {"path": "Vehicle.Driver.AlertnessScore", "value": 0.95},
    {"path": "Vehicle.ADAS.MinTTC", "value": 10.0},
    {"path": "Vehicle.ADAS.FinalRiskScore", "value": 5.0},
    {"path": "Vehicle.ADAS.CriticalAlert", "value": False},
    {"path": "Vehicle.Speed", "value": 60.0},
    {"path": "Vehicle.SpeedLimit", "value": 80.0},
    {"path": "Vehicle.ADAS.Headway", "value": 3.0},
    {"path": "Vehicle.ADAS.DisplaySeverity", "value": "SAFE"},
    {"path": "Vehicle.ADAS.AlertReasonCode", "value": "NONE"},
    {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "NONE"},
    {"path": "Vehicle.ADAS.EventTransition", "value": "END"},
    {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
    {"path": "Vehicle.ADAS.DataAgeMs", "value": 40},
]

WARNING = [
    {"path": "Vehicle.Driver.State", "value": "distracted"},
    {"path": "Vehicle.Driver.AlertnessScore", "value": 0.45},
    {"path": "Vehicle.ADAS.MinTTC", "value": 3.0},
    {"path": "Vehicle.ADAS.FinalRiskScore", "value": 55.0},
    {"path": "Vehicle.ADAS.CriticalAlert", "value": False},
    {"path": "Vehicle.Speed", "value": 75.0},
    {"path": "Vehicle.SpeedLimit", "value": 80.0},
    {"path": "Vehicle.ADAS.Headway", "value": 2.2},
    {"path": "Vehicle.ADAS.DisplaySeverity", "value": "WARNING"},
    {"path": "Vehicle.ADAS.AlertReasonCode", "value": "DISTRACTED"},
    {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "FOCUS_FORWARD"},
    {"path": "Vehicle.ADAS.EventTransition", "value": "START"},
    {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
    {"path": "Vehicle.ADAS.DataAgeMs", "value": 40},
]

CRITICAL = [
    {"path": "Vehicle.Driver.State", "value": "microsleep"},
    {"path": "Vehicle.Driver.AlertnessScore", "value": 0.15},
    {"path": "Vehicle.ADAS.MinTTC", "value": 1.2},
    {"path": "Vehicle.ADAS.FinalRiskScore", "value": 88.0},
    {"path": "Vehicle.ADAS.CriticalAlert", "value": True},
    {"path": "Vehicle.Speed", "value": 80.0},
    {"path": "Vehicle.SpeedLimit", "value": 80.0},
    {"path": "Vehicle.ADAS.Headway", "value": 0.9},
    {"path": "Vehicle.ADAS.DisplaySeverity", "value": "CRITICAL"},
    {"path": "Vehicle.ADAS.AlertReasonCode", "value": "TTC_CRITICAL"},
    {"path": "Vehicle.ADAS.RecommendedActionCode", "value": "BRAKE_SAFE"},
    {"path": "Vehicle.ADAS.EventTransition", "value": "START"},
    {"path": "Vehicle.ADAS.AIStatus", "value": "ONLINE"},
    {"path": "Vehicle.ADAS.DataAgeMs", "value": 40},
]


def actuate(signals: list[dict[str, Any]]) -> None:
    node = discover_signal_node()
    print_json(api("POST", f"/api/v1/signals/{room_id()}/{node}/actuate", {"signals": signals}))


def main() -> None:
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "status",
            "nodes",
            "signals",
            "values",
            "send-safe",
            "send-warning",
            "send-critical",
        ],
    )
    args = parser.parse_args()

    if args.command == "status":
        print_json(api("GET", f"/api/v1/deployments/{room_id()}/status"))
    elif args.command == "nodes":
        print_json(api("GET", f"/api/v1/deployments/{room_id()}/nodes"))
    elif args.command == "signals":
        print_json(api("GET", f"/api/v1/signals/{room_id()}/{discover_signal_node()}"))
    elif args.command == "values":
        print_json(
            api(
                "POST",
                f"/api/v1/signals/{room_id()}/{discover_signal_node()}/values",
                {"paths": DMS_VALUE_PATHS},
            )
        )
    elif args.command == "send-safe":
        actuate(SAFE)
    elif args.command == "send-warning":
        actuate(WARNING)
    elif args.command == "send-critical":
        actuate(CRITICAL)


if __name__ == "__main__":
    main()
