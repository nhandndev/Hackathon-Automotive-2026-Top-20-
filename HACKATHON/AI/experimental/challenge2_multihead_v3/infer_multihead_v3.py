from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any


if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent))

from _trip_adapter import (
    discover_trip_dirs,
    iter_trip_frames,
    load_trip_json,
    make_dms_core,
    primitive_to_raw_features,
    process_driver_frame,
)
from multihead_driver_state_v3 import MultiHeadDriverStateV3


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    ai_root = here.parents[1]
    parser = argparse.ArgumentParser(description="Inference for experimental Challenge 2 Multi-Head V3.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--trip-dir", help="Single BTC-style trip folder.")
    group.add_argument("--data-dir", help="Folder containing BTC-style trip folders.")
    parser.add_argument("--samples-only", action="store_true")
    parser.add_argument("--legacy-config", default=str(ai_root / "configs" / "challenge2.yaml"))
    parser.add_argument("--multihead-config", default=str(here / "multihead_config.yaml"))
    parser.add_argument("--drowsy-model", default=None, help="Optional binary RF drowsy .joblib.")
    parser.add_argument("--out", default=str(here / "artifacts" / "predictions_multihead_v3"))
    parser.add_argument("--debug-dir", default=None, help="Optional JSONL debug output folder.")
    parser.add_argument("--max-frames-per-trip", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def format_float(value: Any, ndigits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "inf"
    if not math.isfinite(number):
        return "inf"
    return f"{number:.{ndigits}f}"


def frame_ttc(frame: dict[str, Any]) -> Any:
    if "min_ttc" in frame:
        return frame["min_ttc"]
    if "predicted_ttc" in frame:
        return frame["predicted_ttc"]
    return math.inf


def frame_risk(frame: dict[str, Any]) -> float:
    risk = frame.get("risk", {})
    if isinstance(risk, dict):
        for key in ("final_risk_score", "risk_score", "base_risk"):
            if key in risk:
                try:
                    return float(risk[key])
                except (TypeError, ValueError):
                    pass
    for key in ("predicted_risk_score", "risk_score"):
        if key in frame:
            try:
                return float(frame[key])
            except (TypeError, ValueError):
                pass
    return 0.0


def infer_trip(trip_dir: Path, args: argparse.Namespace, out_dir: Path, debug_dir: Path | None) -> None:
    trip_json = load_trip_json(trip_dir)
    fps = float(trip_json.get("metadata", {}).get("fps", 20.0) or 20.0)
    frames = list(iter_trip_frames(trip_json, max_frames=args.max_frames_per_trip))

    dms = make_dms_core(args.legacy_config)
    engine = MultiHeadDriverStateV3(args.multihead_config, args.drowsy_model)

    out_path = out_dir / f"{trip_dir.name}.csv"
    debug_handle = None
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_handle = (debug_dir / f"{trip_dir.name}.heads.jsonl").open("w", encoding="utf-8")

    try:
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "frame_id",
                    "timestamp",
                    "predicted_ttc",
                    "predicted_driver_state",
                    "predicted_risk_score",
                ],
            )
            writer.writeheader()
            for index, frame in enumerate(frames):
                primitive = process_driver_frame(dms, trip_dir, frame, fps=fps)
                raw = primitive_to_raw_features(primitive, frame)
                result = engine.predict(raw)
                writer.writerow(
                    {
                        "frame_id": int(frame.get("frame_id", index)),
                        "timestamp": format_float(frame.get("timestamp", index / fps), 3),
                        "predicted_ttc": format_float(frame_ttc(frame), 3),
                        "predicted_driver_state": result.state,
                        "predicted_risk_score": format_float(frame_risk(frame), 3),
                    }
                )
                if debug_handle is not None:
                    debug_handle.write(
                        json.dumps(
                            {
                                "frame_id": int(frame.get("frame_id", index)),
                                "timestamp": float(frame.get("timestamp", index / fps)),
                                **result.to_dict(),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                if args.verbose and (index + 1) % 100 == 0:
                    print(f"{trip_dir.name}: {index + 1}/{len(frames)}")
    finally:
        dms.close()
        if debug_handle is not None:
            debug_handle.close()

    print(f"{trip_dir.name}: wrote {out_path}")


def main() -> int:
    args = parse_args()
    trip_dirs = [Path(args.trip_dir)] if args.trip_dir else discover_trip_dirs(args.data_dir, args.samples_only)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = Path(args.debug_dir) if args.debug_dir else None

    for trip_dir in trip_dirs:
        infer_trip(trip_dir, args, out_dir, debug_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
