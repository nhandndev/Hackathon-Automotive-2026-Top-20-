# E-37: Calibration quality — Challenge 1 (Road/TTC)

**Owner:** Tâm. **Supporting:** Dân.

## Correction to a prior scan

An earlier pass over this repo (read-only scan) reported: *"no source
manifest or generation script was found in the repo through read-only
scan. Therefore E37 currently proves that calibration audit artifacts
exist, but does not prove the full generation process or absolute
calibration correctness."* That scan did not look inside
`Practice_Dataset/*/kitti/`, where the manifests actually live. This is
the same calibration data `team_kit/dataset_loader.py`'s
`TripDataset.load_calibration()` already loads for every trip
`scripts/eval_practice.py` scores — i.e. it is not a separate/mocked
source, it is the live input driving the production 73.6/100 composite
score.

Two files per trip:
- `kitti/calibration_info.txt` — one JSON manifest per trip (fov, baseline,
  image size, K/P2/P3 matrices).
- `kitti/calib/{frame_id}.txt` — one KITTI-format calib file **per frame**
  (P0-P3, R0_rect, Tr_velo_to_cam, Tr_imu_to_velo).

## Hành động thực hiện

`evidence/scripts/compute_calibration_quality.py`:
1. Parses all 7 available trip manifests (6 Practice + `extra_trips`
   lead-brake) for the manifest-level baseline.
2. **Independently recomputes** baseline_m from every one of the 4200
   per-frame KITTI calib files (`baseline_m = -Tx(P3) / fx(P2)`, standard
   convention) — not just trusting the manifest's stated value.
3. Renders an epipolar-line montage: one representative frame (id=50) per
   trip, left/right stacked side by side, green reference lines every 40px.

## Kết quả

**Baseline distribution** (`baseline_distribution.csv`, `baseline_per_frame.csv`, `baseline_summary.txt`):

| Trip | baseline_m (manifest) | fov_deg | image size |
|---|---|---|---|
| T01-Sample | 0.3 | 90 | 640x360 |
| T02-Sample | 0.3 | 90 | 640x360 |
| T03-Sample | 0.3 | 90 | 640x360 |
| T04-Sample | 0.3 | 90 | 640x360 |
| T05-Sample | 0.3 | 90 | 640x360 |
| T06-Sample | 0.3 | 90 | 640x360 |
| T01-Sample-leadbrake (extra_trips) | 0.3 | 90 | 640x360 |

Per-frame recomputation across **all 4200 calib files**: mean=0.300000 m,
**std=0.000000**, min=max=0.300000 m. The manifest's stated baseline is
exactly correct and identical, frame-by-frame, trip-by-trip — no drift, no
per-frame calibration noise. This matches the synthetic-rig nature of the
dataset (CARLA fixed stereo camera pair), not a physically-calibrated real
rig where some baseline jitter would be expected.

**Epipolar montage** (`epipolar_montage.png`): landmarks common to both the
left and right image of each pair (bridge structure in T01, buildings in
T04, tree line in T05, oncoming cars in T06, etc.) land on the exact same
horizontal scanline in both images at every reference line — the visual
signature of correct rectification (pure horizontal baseline shift, zero
vertical disparity). No trip shows a vertical offset between L/R.

## Kết luận

Calibration quality for Challenge 1 is **good and verified quantitatively
+ visually**, not just asserted: baseline is constant to the full
precision of the stored floats across every frame of every available
trip, and rectification is visually confirmed correct across all 7 trips
via the epipolar montage. This directly supports the accuracy of
`core/challenge1_road/ttc_engine.py`'s SGBM-based depth estimation, which
assumes exactly this (constant baseline, zero vertical disparity) to
convert disparity to depth.

**Giới hạn:** không có bằng chứng về **quá trình sinh ra** các file
calibration này (không tìm thấy script generation trong repo — có thể do
`Data_train`/nguồn gốc dataset nằm ngoài repo, xem ghi chú "Note on data
availability" trong `evidence/05_model_ablation/domain_gap_report.md`).
Báo cáo này xác nhận **artifact tồn tại và tự nhất quán** (baseline không
đổi, rectification đúng), không xác nhận **quy trình tạo ra** artifact đó
đúng theo thiết kế phần cứng/simulator gốc.
