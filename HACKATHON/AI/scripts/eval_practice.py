"""
Run Challenge-1 inference on all 6 full-GT Practice trips, score each with
the organizer's evaluation.py, and print a per-trip + average composite
table. This is the local self-check loop for tuning (file 03/04 workflow).
"""

from __future__ import annotations

import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

KIT = AI_ROOT / "Dataset" / "Dataset" / "Package_starterkit" / "package_starterkit"
DATA = AI_ROOT / "Dataset" / "Dataset" / "Practice_Dataset 2"
OUT = AI_ROOT / "predictions" / "FPTU_DMS_Vision"
sys.path.insert(0, str(KIT))

from run_inference import run_trip, _load_config  # noqa: E402
from team_kit.evaluation import evaluate  # noqa: E402


def main() -> int:
    import logging
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    config = _load_config(AI_ROOT / "configs" / "challenge1.yaml")
    trips = sorted(p for p in DATA.iterdir() if p.is_dir() and p.name.endswith("-Sample"))

    rows = []
    for trip in trips:
        run_trip(trip, OUT, config)
        report = evaluate(OUT / f"{trip.name}.csv", DATA, None)
        m = report.per_trip[0]
        rows.append((trip.name, m.mae_critical, m.f1, m.inv_ttc_mae, m.composite_score))
        print(f"  {trip.name}: MAE-crit={m.mae_critical:.2f} F1={m.f1:.2f} "
              f"inv={m.inv_ttc_mae:.3f} composite={m.composite_score:.1f}", flush=True)

    print("\n==== SUMMARY ====")
    print(f"{'Trip':<14}{'MAE-crit':<10}{'F1':<7}{'inv':<8}{'Composite':<10}")
    for name, mae, f1, inv, comp in rows:
        print(f"{name:<14}{mae:<10.2f}{f1:<7.2f}{inv:<8.3f}{comp:<10.1f}")
    avg = sum(r[4] for r in rows) / len(rows)
    print(f"\nAVERAGE COMPOSITE: {avg:.1f} / 100")
    return 0


if __name__ == "__main__":
    sys.exit(main())
