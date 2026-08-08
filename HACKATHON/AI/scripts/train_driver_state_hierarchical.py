import os
import sys
import hashlib
from pathlib import Path
import argparse
import joblib
import numpy as np
import yaml
import json
import logging
import time
import pandas as pd
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import sklearn
import onnxruntime as ort

AI_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AI_ROOT))

KIT = AI_ROOT / "Package_starterkit" / "Package_starterkit" / "package_starterkit"
sys.path.insert(0, str(KIT))
from team_kit.dataset_loader import TripDataset

from core.challenge2_driver.dms_core import DMSCore
from core.challenge2_driver.ml_features import (
    CausalFeatureBuffer,
    ArchitectV2FeatureBuffer,
    feature_names,
    architect_v2_feature_names
)
from core.challenge2_driver.face_landmarker import LANDMARK_BACKEND
from core.challenge2_driver.safety_fusion import should_force_microsleep

from team_kit.evaluation import compute_challenge2_metrics
from core.challenge2_driver.label_contract import (
    FINAL_LABELS,
    normalize_driver_state
)
from core.challenge2_driver.model_contract import validate_driver_artifact


def normalize_driver_state_array(labels) -> np.ndarray:
    return np.asarray([normalize_driver_state(l) for l in labels], dtype=str)

def validate_canonical_labels(name: str, labels: np.ndarray) -> None:
    labels = np.asarray(labels, dtype=str)
    unexpected = set(labels.tolist()) - set(FINAL_LABELS)
    if unexpected:
        raise ValueError(f"{name} contains unsupported labels after normalization: {sorted(unexpected)}")

def print_label_distribution(name, labels):
    values, counts = np.unique(labels, return_counts=True)
    logging.info(f"\n{name} label distribution:")
    for value, count in zip(values, counts):
        logging.info(f"  {value:<12} {int(count)}")


ARCHITECT_V2_SEARCH_SPACE = {
    "n_estimators": [200, 300, 400, 500, 700],
    "max_depth": [12, 16, 20, 24, None],
    "min_samples_split": [2, 5, 10, 20],
    "min_samples_leaf": [1, 2, 5, 10],
    "max_features": ["sqrt", "log2", 0.50, 0.75],
    "class_weight": ["balanced", "balanced_subsample"],
    "bootstrap": [True],
}

def baseline_candidate():
    return {
        "n_estimators": 200, "max_depth": 16, "min_samples_split": 20,
        "min_samples_leaf": 10, "max_features": "log2",
        "class_weight": "balanced_subsample", "bootstrap": True,
    }

def canonical_json(config: dict) -> str:
    return json.dumps(config, sort_keys=True)

def generate_candidates(n_iterations: int, search_seed: int):
    rng = np.random.default_rng(search_seed)
    candidates = [baseline_candidate()]
    seen = {canonical_json(candidates[0])}
    
    while len(candidates) < n_iterations:
        cand = {k: values[int(rng.integers(0, len(values)))] for k, values in ARCHITECT_V2_SEARCH_SPACE.items()}
        key = canonical_json(cand)
        if key not in seen:
            seen.add(key)
            candidates.append(cand)
    return candidates


def _is_trip_dir(path: Path) -> bool:
    if not path.is_dir(): return False
    trip_id = path.name
    has_gt = (path / f"{trip_id}.json").is_file() or (path / f"{trip_id}.json.gz").is_file()
    return has_gt and (path / "driver").is_dir()

def discover_trips(split_dir: Path) -> list[Path]:
    if not split_dir.is_dir():
        raise FileNotFoundError(f"Missing split directory: {split_dir}")
    trips = sorted(path for path in split_dir.iterdir() if _is_trip_dir(path))
    if not trips:
        raise RuntimeError(f"No valid trips found in {split_dir}")
    return trips


@dataclass
class TripFeatureData:
    trip_id: str
    frame_ids: np.ndarray
    timestamps: np.ndarray
    labels: np.ndarray
    unified_X: np.ndarray
    safety_microsleep_override: np.ndarray


def evaluate_like_official_c2(*, y_true, y_pred, trip_ids, frame_ids):
    per_trip = []
    unique_trips = list(dict.fromkeys(trip_ids.tolist()))
    for trip_id in unique_trips:
        mask = (trip_ids == trip_id)
        pairs = {}
        for fid, pred, gt in zip(frame_ids[mask], y_pred[mask], y_true[mask]):
            pairs[int(fid)] = (str(pred), str(gt))
        metrics = compute_challenge2_metrics(str(trip_id), pairs)
        if metrics is not None:
            per_trip.append(metrics)
    if not per_trip:
        raise RuntimeError("No validation trips scored.")
    overall = float(np.mean([m.composite_score for m in per_trip]))
    return {"overall_c2_composite": overall, "per_trip": per_trip}

def get_config_hash(config: dict) -> str:
    rel = {k: config.get(k) for k in ["face", "eye", "mouth", "hand", "ml"]}
    return hashlib.sha256(json.dumps(rel, sort_keys=True).encode("utf-8")).hexdigest()

def get_trip_fingerprint(trip_dir: Path) -> dict:
    trip_id = trip_dir.name
    gt_path = trip_dir / f"{trip_id}.json"
    if not gt_path.is_file(): gt_path = trip_dir / f"{trip_id}.json.gz"
    
    return {
        "trip_id": trip_id,
        "gt_size": gt_path.stat().st_size if gt_path.is_file() else 0,
        "gt_mtime_ns": gt_path.stat().st_mtime_ns if gt_path.is_file() else 0,
        "driver_frame_count": len(list((trip_dir / "driver").glob("*.jpg"))) if (trip_dir / "driver").is_dir() else 0,
    }

def create_manifest(cache_dir: Path, config: dict):
    manifest_path = cache_dir / "manifest.json"
    manifest = {
        "cache_schema_version": 5,
        "feature_extraction_version": 5,
        "challenge2_config_hash": get_config_hash(config),
        "architecture": "architect_v2",
        "unified": {
            "schema": "unified_84_legacy59_hand25",
            "count": 84,
            "feature_names": architect_v2_feature_names()
        },
        "landmark_backend": LANDMARK_BACKEND,
        "hand_backend": "mock-hand-detector"
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

def is_manifest_compatible(cache_dir: Path, config: dict) -> bool:
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.is_file(): return False
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        if manifest.get("cache_schema_version") != 5: return False
        if manifest.get("feature_extraction_version") != 5: return False
        if manifest.get("challenge2_config_hash") != get_config_hash(config): return False
        if manifest.get("landmark_backend") != LANDMARK_BACKEND: return False
        if manifest.get("architecture") != "architect_v2": return False
        
        unified_info = manifest.get("unified", {})
        if unified_info.get("schema") != "unified_84_legacy59_hand25": return False
        if unified_info.get("count") != 84: return False
        if list(unified_info.get("feature_names", [])) != architect_v2_feature_names(): return False
        
        return True
    except Exception:
        return False

def validate_trip_cache(cache_path: Path) -> TripFeatureData:
    data = np.load(cache_path, allow_pickle=True)
    unified_X = data["unified_X"]
    if unified_X.ndim != 2 or unified_X.shape[1] != 84:
        raise ValueError(f"Unified shape mismatch: {unified_X.shape[1]} vs 84")
        
    cached_names = list(data.get("feature_names", []))
    if not cached_names:
        raise ValueError("Missing feature_names in cache file")
    if [str(n) for n in cached_names] != architect_v2_feature_names():
        raise ValueError("Feature names mismatch")
        
    return TripFeatureData(
        trip_id=str(data["trip_id"]),
        frame_ids=data["frame_ids"], timestamps=data["timestamps"],
        labels=normalize_driver_state_array(data["labels"]),
        unified_X=unified_X,
        safety_microsleep_override=data["safety_microsleep_override"]
    )

def save_trip_cache(cache_path: Path, item: TripFeatureData, fingerprint: dict):
    tmp_path = cache_path.with_suffix(".tmp.npz")
    np.savez_compressed(
        tmp_path, trip_id=item.trip_id, frame_ids=item.frame_ids,
        timestamps=item.timestamps, labels=item.labels, unified_X=item.unified_X,
        safety_microsleep_override=item.safety_microsleep_override,
        fingerprint=fingerprint,
        feature_names=np.asarray(architect_v2_feature_names(), dtype=str)
    )
    os.replace(tmp_path, cache_path)

def extract_features_from_trip(trip_dir: Path, config: dict) -> TripFeatureData:
    t_start = time.perf_counter()
    ds = TripDataset(trip_dir)
    dms = DMSCore(config)
    
    buffer = ArchitectV2FeatureBuffer()
    unified_rows, labels, frame_ids, timestamps, safety = [], [], [], [], []
    
    dms_time = 0.0

    try:
        def iter_driver_frames_prefetched(ds_obj):
            frames = list(ds_obj.iter_frames())
            with ThreadPoolExecutor(max_workers=1) as loader:
                iterator = iter(frames)
                try:
                    current = next(iterator)
                except StopIteration: return
                
                current_future = loader.submit(ds_obj.load_driver, current.frame_id)
                for next_frame in iterator:
                    next_future = loader.submit(ds_obj.load_driver, next_frame.frame_id)
                    yield current, current_future.result()
                    current, current_future = next_frame, next_future
                yield current, current_future.result()

        for frame, cabin in iter_driver_frames_prefetched(ds):
            if cabin is None: continue
            
            t0 = time.perf_counter()
            timestamp_ms = round(frame.timestamp * 1000)
            result = dms.process(cabin, frame.frame_id, timestamp_ms)
            dms_time += time.perf_counter() - t0
            
            unified_rows.append(buffer.update(result))
            
            sf = should_force_microsleep(result, int(config.get("eye", {}).get("microsleep_min_ms", 500)))
            
            labels.append(normalize_driver_state(frame.driver_state))
            frame_ids.append(frame.frame_id)
            timestamps.append(frame.timestamp)
            safety.append(sf)
            
    finally:
        dms.close()
        
    logging.debug(f"{trip_dir.name} - Total: {time.perf_counter()-t_start:.2f}s, DMS: {dms_time:.2f}s")
    
    return TripFeatureData(
        trip_id=trip_dir.name,
        frame_ids=np.asarray(frame_ids, dtype=np.int32),
        timestamps=np.asarray(timestamps, dtype=np.float32),
        labels=np.asarray(labels, dtype=str),
        unified_X=np.asarray(unified_rows, dtype=np.float32),
        safety_microsleep_override=np.asarray(safety, dtype=bool)
    )

def prepare_split_features(
    dataset_root: Path, split_name: str, trip_dirs: list[Path],
    config: dict, feature_workers: int, use_cache: bool, force_extract: bool
):
    manifest_dir = dataset_root / ".ch2_feature_cache" / "schema_v5"
    cache_root = manifest_dir / split_name
    cache_root.mkdir(parents=True, exist_ok=True)
    
    manifest_ok = is_manifest_compatible(manifest_dir, config)
    cache_allowed = use_cache and not force_extract and manifest_ok
            
    jobs = []
    cached_results = {}
    cache_hits, cache_misses = 0, 0
    
    for trip_dir in trip_dirs:
        cache_path = cache_root / f"{trip_dir.name}.npz"
        cached = None
        if cache_allowed and cache_path.is_file():
            fp = get_trip_fingerprint(trip_dir)
            try:
                data = np.load(cache_path, allow_pickle=True)
                if data.get("fingerprint").item() == fp:
                    cached = validate_trip_cache(cache_path)
            except Exception as e:
                logging.warning(f"Failed to load cached file {cache_path}: {e}. Will re-extract.")
                cached = None
                
        if cached is not None:
            cached_results[trip_dir.name] = cached
            cache_hits += 1
            logging.info(f"[{split_name}] {trip_dir.name} CACHE HIT")
        else:
            jobs.append(trip_dir)
            cache_misses += 1

    extracted_results = {}
    if jobs:
        if feature_workers <= 1:
            for trip_dir in jobs:
                logging.info(f"[{split_name}] {trip_dir.name} CACHE MISS - Extracting...")
                res = extract_features_from_trip(trip_dir, config)
                extracted_results[res.trip_id] = res
                if use_cache:
                    save_trip_cache(cache_root / f"{res.trip_id}.npz", res, get_trip_fingerprint(trip_dir))
        else:
            with ThreadPoolExecutor(max_workers=feature_workers) as executor:
                futures = {executor.submit(extract_features_from_trip, td, config): td for td in jobs}
                for i, future in enumerate(as_completed(futures), 1):
                    td = futures[future]
                    logging.info(f"[{split_name}] {td.name} CACHE MISS - Extracted [{i}/{len(jobs)}]")
                    res = future.result()
                    extracted_results[res.trip_id] = res
                    if use_cache:
                        save_trip_cache(cache_root / f"{res.trip_id}.npz", res, get_trip_fingerprint(td))

    if use_cache and cache_misses > 0:
        logging.info(f"[{split_name}] Creating/Updating cache manifest...")
        create_manifest(manifest_dir, config)

    final_list = []
    for td in trip_dirs:
        tid = td.name
        if tid in cached_results:
            final_list.append(cached_results[tid])
        else:
            final_list.append(extracted_results[tid])
            
    return final_list, cache_hits, cache_misses


@dataclass
class ArchitectV2TrainingData:
    X_train: np.ndarray
    y_train: np.ndarray
    X_valid: np.ndarray
    y_valid: np.ndarray
    validation_trip_ids: np.ndarray
    validation_frame_ids: np.ndarray
    validation_safety: np.ndarray
    feature_names: list[str]


def prepare_training_data(args, config: dict) -> tuple:
    t_start = time.perf_counter()
    dataset_dir = Path(args.dataset_dir)
    
    train_trips = discover_trips(dataset_dir / "train")
    valid_trips = discover_trips(dataset_dir / "valid")
    
    logging.info(f"Train trips: {len(train_trips)}")
    logging.info(f"Valid trips: {len(valid_trips)}")
    
    train_data_list, t_hits, t_misses = prepare_split_features(
        dataset_dir, "train", train_trips, config, args.feature_workers,
        not args.no_feature_cache, args.force_feature_extract
    )
    
    valid_data_list, v_hits, v_misses = prepare_split_features(
        dataset_dir, "valid", valid_trips, config, args.feature_workers,
        not args.no_feature_cache, args.force_feature_extract
    )

    t_wall = time.perf_counter() - t_start
    total_frames = sum(len(d.labels) for d in train_data_list) + sum(len(d.labels) for d in valid_data_list)
    fps = total_frames / t_wall if t_wall > 0 else 0
    
    perf_metrics = {
        "feature_workers": args.feature_workers,
        "cuda_available": "CUDAExecutionProvider" in ort.get_available_providers(),
        "train": {"trips": len(train_trips), "cache_hits": t_hits, "cache_misses": t_misses},
        "valid": {"trips": len(valid_trips), "cache_hits": v_hits, "cache_misses": v_misses},
        "wall_seconds": round(t_wall, 2),
        "total_frames_extracted": total_frames,
        "effective_extraction_fps": round(fps, 2)
    }
    
    metrics_path = args.output_dir / "feature_preparation_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(perf_metrics, f, indent=2)

    def concat(dlist, field):
        arrs = [getattr(d, field) for d in dlist if len(getattr(d, field)) > 0]
        return np.concatenate(arrs, axis=0) if arrs else np.array([])
        
    t_X = concat(train_data_list, "unified_X")
    t_y = concat(train_data_list, "labels")
    
    v_X = concat(valid_data_list, "unified_X")
    v_y = concat(valid_data_list, "labels")
    v_safety = concat(valid_data_list, "safety_microsleep_override")
    
    v_trip_ids = np.concatenate([
        np.full(len(item.labels), item.trip_id, dtype=object)
        for item in valid_data_list if len(item.labels) > 0
    ]) if valid_data_list else np.array([])
    v_frame_ids = concat(valid_data_list, "frame_ids")
    
    validate_canonical_labels("TRAIN", t_y)
    validate_canonical_labels("VALID", v_y)
    print_label_distribution("TRAIN", t_y)
    print_label_distribution("VALID", v_y)
    
    return ArchitectV2TrainingData(
        X_train=t_X, y_train=t_y,
        X_valid=v_X, y_valid=v_y,
        validation_trip_ids=v_trip_ids,
        validation_frame_ids=v_frame_ids,
        validation_safety=v_safety,
        feature_names=architect_v2_feature_names()
    ), perf_metrics


def eval_metrics(y_true, y_pred) -> dict:
    y_true = normalize_driver_state_array(y_true)
    y_pred = np.asarray(y_pred, dtype=str)
    
    unexpected_true = set(y_true) - set(FINAL_LABELS)
    unexpected_pred = set(y_pred) - set(FINAL_LABELS)
    if unexpected_true: raise ValueError(f"Unknown GT labels: {sorted(unexpected_true)}")
    if unexpected_pred: raise ValueError(f"Unknown predicted labels: {sorted(unexpected_pred)}")

    acc = float(accuracy_score(y_true, y_pred))
    report = classification_report(y_true, y_pred, labels=FINAL_LABELS, output_dict=True, zero_division=0)
    
    macro_f1 = float(report["macro avg"]["f1-score"])
    
    y_true_binary = (y_true == "distracted").astype(int)
    y_pred_binary = (y_pred == "distracted").astype(int)
    fp = np.sum((y_pred_binary == 1) & (y_true_binary == 0))
    tn = np.sum((y_pred_binary == 0) & (y_true_binary == 0))
    far = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "c2_composite": 0.5 * acc + 0.5 * macro_f1,
        "alert_recall": report["alert"]["recall"],
        "distracted_precision": report["distracted"]["precision"],
        "distracted_recall": report["distracted"]["recall"],
        "distracted_f1": report["distracted"]["f1-score"],
        "distracted_far": far,
        "drowsy_recall": report["drowsy"]["recall"],
        "yawning_recall": report["yawning"]["recall"],
        "microsleep_recall": report["microsleep"]["recall"],
        "report": report
    }


def train_one_candidate(iteration_id, candidate_params, data: ArchitectV2TrainingData, args, config):
    t0 = time.perf_counter()
    seed = args.search_seed + iteration_id
    
    model = RandomForestClassifier(**candidate_params, random_state=seed, n_jobs=-1)
    model.fit(data.X_train, data.y_train)
    
    assert model.n_features_in_ == 84, f"Unified model features count mismatch: {model.n_features_in_} vs 84"
    
    pred_labels = model.predict(data.X_valid)
    # Apply safety override (microsleep)
    pred_labels[data.validation_safety] = "microsleep"
    
    metrics = eval_metrics(data.y_valid, pred_labels)
    official = evaluate_like_official_c2(
        y_true=data.y_valid, y_pred=pred_labels,
        trip_ids=data.validation_trip_ids, frame_ids=data.validation_frame_ids
    )
    
    bundle = {
        "architecture": "architect_v2",
        "feature_schema": "unified_84_legacy59_hand25",
        "model": model,
        "feature_names": data.feature_names,
        "feature_count": 84,
        "model_classes": list(model.classes_),
        "window_seconds": {
            "legacy": [3, 10, 30],
            "hand": [1, 3]
        },
        "landmark_backend": LANDMARK_BACKEND,
        "hand_backend": "mock-hand-detector",
        "feature_schema_version": 5,
        "model_version": 7,
        "scikit_learn_version": sklearn.__version__,
        "search_metadata": {
            "search_version": "rf_random_search_v2", "candidate_id": iteration_id,
            "search_seed": args.search_seed, "n_iterations": args.n_iterations,
        },
        "label_policy": {"unknown": "alert"}
    }
    
    validate_driver_artifact(bundle)
    
    mp = args.output_dir / "models" / f"candidate_{iteration_id:03d}.joblib"
    joblib.dump(bundle, mp, compress=3)
    
    # Expose P(distracted) in dashboard/debug
    classes = list(model.classes_)
    probs_valid = model.predict_proba(data.X_valid)
    p_distracted_all = probs_valid[:, classes.index("distracted")] if "distracted" in classes else np.zeros(len(pred_labels))
    
    mjson = {
        "candidate_id": iteration_id, "status": "completed",
        "model_params": {**candidate_params, "random_state": seed},
        "final_validation": metrics,
        "official_validation": {
            "overall_c2_composite": official["overall_c2_composite"],
            "per_trip": {m.trip_id: {"composite": m.composite_score, "accuracy": m.accuracy, "macro_f1": m.macro_f1} for m in official["per_trip"]}
        },
        "model_file": str(mp.relative_to(args.output_dir)),
        "total_seconds": time.perf_counter() - t0,
        "label_policy": {"unknown": "alert"}
    }
    with open(args.output_dir / "metrics" / f"candidate_{iteration_id:03d}.json", "w") as f:
        json.dump(mjson, f, indent=2)
    return mjson


def rank_candidates_and_save(args):
    all_m = []
    for f in (args.output_dir / "metrics").glob("candidate_*.json"):
        with open(f, "r") as fp: all_m.append(json.load(fp))
            
    rows = []
    for m in [m for m in all_m if m["status"] == "completed"]:
        v = m["final_validation"]
        off = m.get("official_validation", {})
        min_trip = min((t["composite"] for t in off.get("per_trip", {}).values()), default=0)
        
        r = {
            "candidate_id": m["candidate_id"], 
            "c2_composite": off.get("overall_c2_composite", v["c2_composite"]),
            "min_trip_composite": min_trip,
            "accuracy": v["accuracy"], "macro_f1": v["macro_f1"],
            "alert_recall": v["alert_recall"], "distracted_far": v["distracted_far"],
            "drowsy_recall": v.get("drowsy_recall", 0),
            "distracted_recall": v["distracted_recall"], "distracted_precision": v["distracted_precision"]
        }
        for k, val in m.get("model_params", {}).items(): r[k] = val
        rows.append(r)
        
    if not rows: return
    
    df = pd.DataFrame(rows).sort_values(
        by=["c2_composite", "min_trip_composite", "drowsy_recall", "distracted_far", "alert_recall", "distracted_recall"],
        ascending=[False, False, False, True, False, False]
    )
    df.insert(0, "rank", range(1, len(df) + 1))
    df.to_csv(args.output_dir / "leaderboard.csv", index=False)
    
    best_id = int(df.iloc[0]["candidate_id"])
    best_dir = args.output_dir / "best"
    best_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(args.output_dir / "models" / f"candidate_{best_id:03d}.joblib", best_dir / "best_model.joblib")
    shutil.copy(args.output_dir / "metrics" / f"candidate_{best_id:03d}.json", best_dir / "best_metrics.json")


def validate_execution_provider(require_cuda: bool):
    providers = ort.get_available_providers()
    logging.info(f"ONNX Runtime providers: {providers}")
    if require_cuda and "CUDAExecutionProvider" not in providers:
        raise RuntimeError("CUDAExecutionProvider is unavailable. Install/configure onnxruntime-gpu before running GPU feature extraction.")


def validate_training_dataset(root: Path) -> None:
    train = root / "train"
    valid = root / "valid"
    if not train.is_dir():
        raise FileNotFoundError(f"Missing train split: {train}")
    if not valid.is_dir():
        raise FileNotFoundError(f"Missing valid split: {valid}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=str, required=True)
    parser.add_argument("--config-path", type=str, default=str(AI_ROOT / "configs" / "challenge2.yaml"))
    parser.add_argument("--output-dir", type=Path, default=AI_ROOT / "artifacts" / "ch2_rf_search")
    parser.add_argument("--n-iterations", type=int, default=10)
    parser.add_argument("--search-seed", type=int, default=20260807)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retune-existing", action="store_true")
    
    parser.add_argument("--feature-workers", type=int, default=2)
    parser.add_argument("--force-feature-extract", action="store_true")
    parser.add_argument("--no-feature-cache", action="store_true")
    parser.add_argument("--require-cuda", action="store_true")
    
    # Deprecated/ignored option for backwards compatibility
    parser.add_argument("--fatigue-feature-schema", type=str, default="legacy59", help="Deprecated/ignored for Architect-v2")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    validate_execution_provider(args.require_cuda)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "models").mkdir(exist_ok=True)
    (args.output_dir / "metrics").mkdir(exist_ok=True)

    with open(args.config_path, "r", encoding="utf-8") as f: config = yaml.safe_load(f)
        
    validate_training_dataset(Path(args.dataset_dir))
    
    if args.retune_existing:
        raise NotImplementedError("--retune-existing is not applicable to architect_v2")
        
    logging.info(f"Feature cache: {Path(args.dataset_dir) / '.ch2_feature_cache'}")
    data, perf = prepare_training_data(args, config)
    
    logging.info("\nFeature preparation summary")
    logging.info(f"Train trips: {perf['train']['trips']}")
    logging.info(f"  cache hits: {perf['train']['cache_hits']}")
    logging.info(f"  extracted:  {perf['train']['cache_misses']}")
    logging.info(f"Valid trips: {perf['valid']['trips']}")
    logging.info(f"  cache hits: {perf['valid']['cache_hits']}")
    logging.info(f"  extracted:  {perf['valid']['cache_misses']}")
    logging.info(f"Feature extraction wall time: {perf['wall_seconds']}s")
    
    candidates = generate_candidates(args.n_iterations, args.search_seed)
    
    expected_dim = 84
    
    logging.info(f"\nArchitecture: architect_v2")
    logging.info(f"Feature schema: unified_84_legacy59_hand25")
    logging.info(f"Expected features: {expected_dim}")
    logging.info(f"TRAIN: {data.X_train.shape}")
    logging.info(f"VALID: {data.X_valid.shape}")
    
    if data.X_train.shape[1] != expected_dim:
        raise ValueError(f"Feature dimension mismatch: {data.X_train.shape[1]} vs {expected_dim}")
    if data.X_valid.shape[1] != expected_dim:
        raise ValueError(f"Validation dimension mismatch: {data.X_valid.shape[1]} vs {expected_dim}")
        
    if data.feature_names != architect_v2_feature_names():
        raise ValueError("Feature names mismatch")
        
    # Critical hand cache guard: calculate hand stats to check for stub/dead hand features
    total_samples = len(data.X_train)
    hand_visible_count = np.sum(data.X_train[:, 59] > 0) # instant_hand_visible is at index 59
    hand_visible_rate = hand_visible_count / max(1, total_samples)
    
    logging.info(f"\nHand visibility rate: {hand_visible_rate * 100:.2f}%")
    if hand_visible_rate == 0.0:
        raise RuntimeError("Hand visibility rate is 0%. Dead hand features detected; training aborted.")
    
    logging.info(f"\nStarting {args.n_iterations} RF candidates...")
    for i, params in enumerate(candidates, start=1):
        mf = args.output_dir / "metrics" / f"candidate_{i:03d}.json"
        if args.resume and mf.exists():
            with open(mf, "r") as f:
                if json.load(f).get("status") == "completed": continue
        
        logging.info(f"\n[{i:03d}/{args.n_iterations}]")
        logging.info("Training Unified RF...")
        
        metrics = train_one_candidate(i, params, data, args, config)
        v = metrics["final_validation"]
        logging.info(f"Accuracy: {v['accuracy']:.4f}")
        logging.info(f"Macro-F1: {v['macro_f1']:.4f}")
        logging.info(f"C2 composite: {v['c2_composite']:.4f}")
        logging.info(f"Saved candidate_{i:03d}.joblib")
        
    logging.info("\nRanking candidates...")
    rank_candidates_and_save(args)

if __name__ == "__main__":
    main()
