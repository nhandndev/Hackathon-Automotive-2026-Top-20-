from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent))

from multihead_driver_state_v3 import MultiHeadDriverStateV3, RawDriverFeatures


def build_synthetic_stream(max_frames: int) -> list[RawDriverFeatures]:
    """Small deterministic smoke stream.

    This is intentionally not training data. It only checks that the new
    pipeline state machine can move through rule heads without touching legacy
    code or spending time on a full training run.
    """
    fps = 20.0
    frames: list[RawDriverFeatures] = []
    for frame_id in range(max_frames):
        t = frame_id / fps
        ear = 0.322
        mar = 0.205
        yaw = 0.0
        pitch = 0.0
        hand_visible = False
        phone_detected = False

        if 8 <= frame_id < 38:
            ear = 0.210
        elif 42 <= frame_id < 88:
            mar = 0.690
        elif 94 <= frame_id < 140:
            yaw = 34.0
            hand_visible = frame_id >= 104
        elif 146 <= frame_id < 190:
            yaw = 28.0
            hand_visible = True
            phone_detected = True

        frames.append(
            RawDriverFeatures(
                frame_id=frame_id,
                timestamp_sec=t,
                ear=ear,
                mar=mar,
                yaw_deg=yaw,
                pitch_deg=pitch,
                roll_deg=0.0,
                eye_quality=0.95,
                mouth_quality=0.95,
                head_quality=0.95,
                hand_visible=hand_visible,
                hand_quality=0.90,
                phone_detected=phone_detected,
                speed_kmh=32.0,
                longitudinal_accel=0.02,
                lateral_accel=0.05,
            )
        )
    return frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke demo for experimental C2 multi-head v3.")
    parser.add_argument("--config", default=str(Path(__file__).with_name("multihead_config.yaml")))
    parser.add_argument("--drowsy-model", default=None, help="Optional binary RF drowsy .joblib.")
    parser.add_argument("--max-frames", type=int, default=80)
    parser.add_argument(
        "--output",
        default=str(Path(__file__).with_name("artifacts") / "smoke_multihead_v3.csv"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    engine = MultiHeadDriverStateV3(args.config, args.drowsy_model)
    frames = build_synthetic_stream(args.max_frames)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frame_id",
                "timestamp",
                "state",
                "confidence",
                "micro_score",
                "yawn_score",
                "dist_score",
                "drowsy_score",
                "source_head",
            ],
        )
        writer.writeheader()
        for raw in frames:
            result = engine.predict(raw)
            row = {
                "frame_id": raw.frame_id,
                "timestamp": f"{raw.timestamp_sec:.3f}",
                "state": result.state,
                "confidence": f"{result.confidence:.3f}",
                "micro_score": f"{result.head_scores['microsleep']:.3f}",
                "yawn_score": f"{result.head_scores['yawning']:.3f}",
                "dist_score": f"{result.head_scores['distracted']:.3f}",
                "drowsy_score": f"{result.head_scores['drowsy']:.3f}",
                "source_head": result.source_head,
            }
            writer.writerow(row)
            if raw.frame_id % 10 == 0 or result.state != "alert":
                print(
                    f"{raw.frame_id:04d} {raw.timestamp_sec:05.2f}s "
                    f"state={result.state:<10} conf={result.confidence:.2f} "
                    f"micro={result.head_scores['microsleep']:.2f} "
                    f"yawn={result.head_scores['yawning']:.2f} "
                    f"dist={result.head_scores['distracted']:.2f}"
                )

    print(f"\nSmoke output: {out_path}")
    print("No training was run. Legacy production pipeline was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
