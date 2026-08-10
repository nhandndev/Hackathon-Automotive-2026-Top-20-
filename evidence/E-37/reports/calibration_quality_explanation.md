# E-37 - Calibration Quality Audit

E37 checks stereo calibration quality for Challenge 1/TTC.

Current artifacts in this folder:

- `derived/baseline_distribution.csv`
- `derived/epipolar_montage.png`
- `derived/calibration_summary.json`

## Meaning of current artifacts

`baseline_distribution.csv` records the baseline/matrix/trip summary contained in the artifact. `epipolar_montage.png` is a visual montage for checking epipolar alignment.

## Important limitation

In this update, no source manifest or generation script was found in the repo through read-only scan. Therefore E37 currently proves that calibration audit artifacts exist, but does not prove the full generation process or absolute calibration correctness.
