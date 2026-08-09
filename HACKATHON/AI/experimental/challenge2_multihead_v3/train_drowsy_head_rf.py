from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


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


DROWSY_FEATURES = [
    "PERCLOS_5s",
    "blink_duration_mean_5s",
    "eye_openness_mean_5s",
    "eye_openness_std_5s",
    "blink_rate_10s",
    "long_closure_count_10s",
]
NEGATIVE_STATES = {"alert", "yawning", "distracted", "microsleep"}
POSITIVE_STATES = {"drowsy"}


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    ai_root = here.parents[1]
    parser = argparse.ArgumentParser(description="Train experimental binary RF for Drowsy Head.")
    parser.add_argument(
        "--dataset-dir",
        required=True,
        help="Folder containing BTC-style trip folders, or a dataset root with train/valid subfolders.",
    )
    parser.add_argument("--samples-only", action="store_true", help="Only use folders containing '-Sample'.")
    parser.add_argument("--legacy-config", default=str(ai_root / "configs" / "challenge2.yaml"))
    parser.add_argument("--multihead-config", default=str(here / "multihead_config.yaml"))
    parser.add_argument("--output", default=str(here / "models" / "drowsy_head_rf.joblib"))
    parser.add_argument("--report", default=str(here / "models" / "drowsy_head_rf_report.json"))
    parser.add_argument("--max-trips", type=int, default=None)
    parser.add_argument("--max-frames-per-trip", type=int, default=None)
    parser.add_argument("--n-iter", type=int, default=12, help="RandomizedSearch iterations. 0 = no search.")
    parser.add_argument("--cv", type=int, default=3)
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def label_to_binary(label: str | None) -> int | None:
    if label in POSITIVE_STATES:
        return 1
    if label in NEGATIVE_STATES:
        return 0
    return None


def resolve_dataset_layout(args: argparse.Namespace) -> tuple[Path, Path | None]:
    dataset_dir = Path(args.dataset_dir)
    train_dir = dataset_dir / "train"
    valid_dir = dataset_dir / "valid"
    if train_dir.exists() and valid_dir.exists():
        return train_dir, valid_dir
    if train_dir.exists():
        return train_dir, None
    return dataset_dir, None


def extract_dataset(
    root_dir: str | Path,
    args: argparse.Namespace,
    split_name: str,
    max_trips: int | None = None,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    trip_dirs = discover_trip_dirs(root_dir, samples_only=args.samples_only)
    if max_trips is not None:
        trip_dirs = trip_dirs[: max(0, max_trips)]

    X: list[list[float]] = []
    y: list[int] = []
    rows: list[dict[str, Any]] = []

    for trip_dir in trip_dirs:
        trip_json = load_trip_json(trip_dir)
        fps = float(trip_json.get("metadata", {}).get("fps", 20.0) or 20.0)
        frames = list(iter_trip_frames(trip_json, max_frames=args.max_frames_per_trip))
        dms = make_dms_core(args.legacy_config)
        multihead = MultiHeadDriverStateV3(args.multihead_config)

        used = skipped = 0
        try:
            for frame in frames:
                label = str(frame.get("driver", {}).get("state", "")).strip().lower()
                binary = label_to_binary(label)
                if binary is None:
                    skipped += 1
                    continue
                primitive = process_driver_frame(dms, trip_dir, frame, fps=fps)
                raw = primitive_to_raw_features(primitive, frame)
                result = multihead.predict(raw)
                temporal = result.temporal.as_dict()
                vector = [float(temporal[name]) for name in DROWSY_FEATURES]
                X.append(vector)
                y.append(binary)
                rows.append(
                    {
                        "split": split_name,
                        "trip_id": trip_dir.name,
                        "frame_id": int(frame.get("frame_id", 0)),
                        "timestamp": float(frame.get("timestamp", 0.0)),
                        "label": label,
                        "binary": binary,
                    }
                )
                used += 1
        finally:
            dms.close()

        if args.verbose:
            counts = {"drowsy": sum(r["binary"] == 1 for r in rows if r["trip_id"] == trip_dir.name)}
            counts["non_drowsy"] = used - counts["drowsy"]
            print(f"{split_name}/{trip_dir.name}: used={used}, skipped={skipped}, {counts}")

    if not X:
        raise RuntimeError("No trainable drowsy samples extracted.")
    return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.int32), rows


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    args: argparse.Namespace,
    X_valid: np.ndarray | None = None,
    y_valid: np.ndarray | None = None,
) -> tuple[Any, dict[str, Any]]:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split

    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2:
        raise RuntimeError(
            f"Drowsy binary RF needs both classes. Found classes={dict(zip(classes.tolist(), counts.tolist()))}"
        )

    if X_valid is not None and y_valid is not None and len(y_valid) > 0:
        X_train, y_train = X, y
        X_test, y_test = X_valid, y_valid
        eval_source = "dataset_valid_split"
    else:
        stratify = y if min(counts) >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=args.test_size,
            random_state=args.random_state,
            stratify=stratify,
        )
        eval_source = "random_train_test_split"

    base = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=args.random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )

    search_summary: dict[str, Any] | None = None
    if args.n_iter > 0:
        min_class = int(min(np.unique(y_train, return_counts=True)[1]))
        cv_splits = max(2, min(args.cv, min_class))
        param_dist = {
            "n_estimators": [200, 300, 500, 700],
            "max_depth": [None, 4, 6, 8, 12],
            "min_samples_leaf": [1, 2, 4, 8],
            "min_samples_split": [2, 4, 8, 12],
            "max_features": ["sqrt", "log2", None],
        }
        cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=args.random_state)
        search = RandomizedSearchCV(
            base,
            param_distributions=param_dist,
            n_iter=args.n_iter,
            scoring="f1",
            cv=cv,
            random_state=args.random_state,
            n_jobs=-1,
            verbose=1 if args.verbose else 0,
        )
        search.fit(X_train, y_train)
        model = search.best_estimator_
        search_summary = {
            "best_score_cv_f1": float(search.best_score_),
            "best_params": search.best_params_,
        }
    else:
        model = base.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    report = {
        "feature_names": DROWSY_FEATURES,
        "n_samples": int(len(y)),
        "class_counts": {"non_drowsy": int((y == 0).sum()), "drowsy": int((y == 1).sum())},
        "eval_source": eval_source,
        "test_size": int(len(y_test)),
        "valid_class_counts": {
            "non_drowsy": int((y_test == 0).sum()),
            "drowsy": int((y_test == 1).sum()),
        },
        "classification_report": classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["non_drowsy", "drowsy"],
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist(),
        "search": search_summary,
    }
    return model, report


def main() -> int:
    import joblib

    args = parse_args()
    train_dir, valid_dir = resolve_dataset_layout(args)
    X, y, rows = extract_dataset(train_dir, args, "train", max_trips=args.max_trips)
    X_valid = y_valid = None
    valid_rows: list[dict[str, Any]] = []
    if valid_dir is not None:
        X_valid, y_valid, valid_rows = extract_dataset(valid_dir, args, "valid", max_trips=args.max_trips)
    model, report = train_model(X, y, args, X_valid=X_valid, y_valid=y_valid)

    artifact = {
        "architecture": "multihead_v3_drowsy_binary_rf",
        "model": model,
        "feature_names": DROWSY_FEATURES,
        "label_mapping": {"non_drowsy": 0, "drowsy": 1},
        "report": report,
        "source_rows_preview": (rows + valid_rows)[:20],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved drowsy RF: {output}")
    print(f"Saved report:    {report_path}")
    print(f"Train samples: drowsy={(y == 1).sum()} non_drowsy={(y == 0).sum()}")
    if y_valid is not None:
        print(f"Valid samples: drowsy={(y_valid == 1).sum()} non_drowsy={(y_valid == 0).sum()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
