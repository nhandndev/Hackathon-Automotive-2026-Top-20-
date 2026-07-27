"""Test rescue-only fusion: use geo detector ONLY on frames where the main
pipeline (YOLO+stereo+hold) returns inf. Measures whether this captures
T02's missed-detection gain without importing geo's standalone false-alarm
flood (which fires somewhat independent of what the main pipeline sees)."""
import sys, math, yaml
from pathlib import Path
AI = Path.cwd()
sys.path.insert(0, str(AI / "Dataset/Dataset/Package_starterkit/package_starterkit"))
sys.path.insert(0, str(AI)); sys.path.insert(0, str(AI / "scripts"))
from team_kit.dataset_loader import TripDataset
from core.challenge1_road.predict_ttc import RoadTTCPredictor
import proto_geo_detector as G

cfg = yaml.safe_load(open("configs/challenge1.yaml"))

def run(trip_name):
    trip_dir = AI / "Dataset/Dataset/Practice_Dataset 2" / trip_name
    ds = TripDataset(trip_dir)
    calib = ds.load_calibration()
    main = RoadTTCPredictor(calib, cfg); main.set_trip_dir(trip_dir); main.reset()
    stereo = G.StereoDepth(float(calib["K_left"][0][0]), float(calib["baseline_m"]))
    depth_dir = trip_dir / "kitti" / "depth"

    tracks = []
    last_finite_ttc, last_finite_t, gap_count = float("inf"), 0.0, 0
    errs, tp, fp, fn = [], 0, 0, 0
    rescued = 0

    for fr in ds.iter_frames():
        left, right = ds.load_left(fr.frame_id), ds.load_right(fr.frame_id)
        main_ttc = main.predict_frame(fr.frame_id, fr.timestamp, left, right, fr.speed_kmh)

        # geo signal (only need to bother computing when main is inf, but
        # for fair state/tracking continuity we still update geo tracks every frame)
        p = depth_dir / f"{fr.frame_id:06d}.npy"
        if p.exists():
            depth = __import__("numpy").load(p).astype("float32")
            depth[depth >= 60.0] = float("inf")
        else:
            depth = stereo.depth_map(stereo.disparity(left, right))
        blobs = G.find_depth_blobs(depth)
        used = set()
        for tr in tracks:
            lz, lx = tr.last[1], tr.last[2]
            best_i, best_d = None, 1e9
            for i, b in enumerate(blobs):
                if i in used: continue
                d = abs(b["z"]-lz)/G.TRACK_MATCH_Z + abs(b["x"]-lx)/G.TRACK_MATCH_X
                if d < best_d and abs(b["z"]-lz) < G.TRACK_MATCH_Z and abs(b["x"]-lx) < G.TRACK_MATCH_X:
                    best_d, best_i = d, i
            if best_i is not None:
                tr.update(blobs[best_i]["z"], blobs[best_i]["x"], fr.timestamp); used.add(best_i)
        for i, b in enumerate(blobs):
            if i not in used: tracks.append(G.GeoTrack(b["z"], b["x"], fr.timestamp))
        tracks[:] = [tr for tr in tracks if fr.timestamp - tr.last[0] < 0.3]

        geo_ttc = float("inf")
        for tr in tracks:
            if tr.last[0] != fr.timestamp: continue
            sp = tr.closing_speed()
            if sp is None or sp < G.MIN_APPROACH_SPEED: continue
            geo_ttc = min(geo_ttc, tr.last[1]/sp)

        # RESCUE-ONLY fusion: geo only speaks when main is silent (inf)
        if math.isfinite(main_ttc):
            pred = main_ttc
        elif math.isfinite(geo_ttc):
            pred = geo_ttc
            rescued += 1
        else:
            pred = float("inf")

        gt = fr.min_ttc
        if math.isfinite(gt) and gt < 3.0:
            errs.append(abs((pred if math.isfinite(pred) else 99.0) - gt))
        pd_, gd = (math.isfinite(pred) and pred < 2.0), (math.isfinite(gt) and gt < 2.0)
        if pd_ and gd: tp += 1
        elif pd_ and not gd: fp += 1
        elif gd and not pd_: fn += 1

    f1 = 2*tp/(2*tp+fp+fn) if (2*tp+fp+fn) > 0 else 0.0
    mae = sum(errs)/len(errs) if errs else float("nan")
    print(f"{trip_name}: MAE-crit={mae:.2f} n={len(errs)} F1={f1:.2f} (tp{tp} fp{fp} fn{fn}) rescued={rescued}/600")

run("T02-Sample")
run("T04-Sample")
