# E-27 - C2 Split Policy

## Recorded policy

- Train/valid split follows random 70/30.
- For crawled/Kaggle data, original YOLO-style `train` and `valid` split is preserved.
- Kaggle source provided by owner: https://www.kaggle.com/datasets/habbas11/dms-driver-monitoring-system

## Current repo evidence

| Split | Evidence file | Count |
|---|---|---:|
| train | `evidence/E-27/derived/split_manifest.csv#train` | 96 |
| valid | `evidence/E-27/derived/split_manifest.csv#valid` | 34 |

## Limits

- Raw dataset folder is local-only/gitignored, so it is not cited directly as a repo evidence path.
- Subject-disjoint proof is missing because no reliable subject ID/provenance manifest was found.
- Kaggle screenshot/license capture is not present in this evidence folder.
