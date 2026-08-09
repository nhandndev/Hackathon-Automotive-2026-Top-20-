# Source Report - E-27 C2 Generalization

| Evidence | Source | Ghi chú |
|---|---|---|
| `split_policy.md` | Owner instruction + `experiment/dataset-v2/` | Policy 70/30 and YOLO-form train/valid |
| `split_manifest.csv` | Local folders `experiment/dataset-v2/train`, `experiment/dataset-v2/valid` | Split counts and examples |
| `c2_eval_sources.md` | `evaluation.json`, `overall_class_metrics.csv`, `overall_confusion_matrix.png` | Evaluation artifacts already present |

## Chưa làm

- Chưa capture Kaggle license/screenshot.
- Chưa audit subject-disjoint split vì cần subject IDs/provenance.
