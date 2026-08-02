"""Validate and send DecisionEvent JSONL records to an SE HTTP endpoint."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

from core.decision_engine import DecisionEvent  # noqa: E402
from integrations import SEApiClient  # noqa: E402

LOGGER = logging.getLogger("send_decision_events")


def iter_events(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                yield DecisionEvent.model_validate(json.loads(line))
            except Exception as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid DecisionEvent: {exc}"
                ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="POST canonical DecisionEvents to the SE integration API"
    )
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--timeout-sec", type=float, default=3.0)
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Log failed events and continue; default is fail fast",
    )
    args = parser.parse_args()

    if not args.events.is_file():
        parser.error(f"Event JSONL not found: {args.events}")
    api_key = os.environ.get("FPTU_SE_API_KEY")
    bearer_token = os.environ.get("FPTU_SE_BEARER_TOKEN")
    sent = failed = 0
    with SEApiClient(
        args.endpoint,
        api_key=api_key,
        bearer_token=bearer_token,
        timeout_sec=args.timeout_sec,
    ) as client:
        for event in iter_events(args.events):
            try:
                response = client.send(event)
                sent += 1
                LOGGER.info(
                    "%s %s %s -> %s",
                    event.status,
                    event.alert_type,
                    event.event_id,
                    response,
                )
            except Exception:
                failed += 1
                LOGGER.exception("Failed event %s", event.idempotency_key)
                if not args.continue_on_error:
                    return 1
    LOGGER.info("Completed: sent=%d failed=%d", sent, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    raise SystemExit(main())
