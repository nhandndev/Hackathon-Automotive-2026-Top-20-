# E-27 - C2 Evaluation Sources

Current usable C2 evaluation artifacts:

| Artifact | Meaning |
|---|---|
| `HACKATHON/AI/artifacts/predictions_6_samples/evaluation.json` | Final C2 per-trip BTC practice evaluation under `challenge2` |
| `HACKATHON/AI/artifacts/predictions/candidate013_pred/analysis/overall_class_metrics.csv` | Overall per-class one-vs-rest metrics for candidate_013 |
| `HACKATHON/AI/artifacts/predictions/candidate013_pred/analysis/overall_confusion_matrix.png` | Overall C2 confusion matrix image, 3600 frames |

Key metrics from the attached confusion-matrix analysis:

```text
Accuracy: 83.806%
Frames: 3600
Macro Precision: 83.9%
Macro Recall/TPR: 82.4%
Macro F1: 82.1%
Macro Specificity: 95.8%
Macro FAR/FPR: 4.2%
Macro FNR/Miss: 17.6%
```

Important observation:

- `microsleep` recall is 100.0% in the provided analysis.
- `alert` recall is low because many alert frames are predicted as distracted.
