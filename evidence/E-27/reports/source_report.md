# Source Report - E-27 C2 Generalization

| Evidence | Source | Note |
|---|---|---|
| `reports/split_policy.md` | Owner instruction + `derived/split_manifest.csv` | 70/30 policy and original YOLO train/valid split for crawled data |
| `derived/split_manifest.csv` | Evidence-local summary | Split counts copied/summarized from a local ignored dataset scan |
| `derived/generalization_summary.json` | Evidence-local summary | Counts, feature schema and artifact availability summary |
| `derived/c2_overall_class_metrics.csv` | Evidence-local copy | Metrics copied into evidence from a local ignored analysis artifact |
| `derived/c2_overall_confusion_matrix.png` | Evidence-local copy | Confusion matrix copied into evidence from a local ignored analysis artifact |
| `reports/c2_eval_sources.md` | Evidence-local source map | Points to repo-pushable metrics/CM evidence |

## Not enough to claim

- Subject-disjoint generalization is not claimed.
- Kaggle license capture/review is not claimed.
- Model retraining is not claimed in this evidence.
- Raw datasets/artifacts may be under `.gitignore`; repo evidence is the files under `derived/` in this folder.
