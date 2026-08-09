# E-27 - C2 Generalization / Split Policy

## Policy đã chốt

- Split train/valid theo tỉ lệ random 70/30.
- Với crawled/Kaggle data, giữ đúng split `train` và `valid` theo form dataset gốc kiểu YOLO.
- Không trộn lại validation của crawled data nếu dataset gốc đã tách sẵn.

## Dataset source

Owner-provided source:

```text
https://www.kaggle.com/datasets/habbas11/dms-driver-monitoring-system
```

Repo dataset path:

```text
experiment/dataset-v2/
  train/
  valid/
```

Observed local split folders:

```text
train trips/folders: 96
valid trips/folders: 34
feature cache: experiment/dataset-v2/.ch2_feature_cache/schema_v4/
```

## Feature cache evidence

`experiment/dataset-v2/.ch2_feature_cache/schema_v4/manifest.json` records:

- fatigue schema: `legacy_59_3_10_30`
- fatigue feature count: `59`
- distraction schema: `distraction_v1_1_3`
- landmark backend: `onnx-yunet-facemesh468`

## Limitations

- Kaggle license/source screenshot is not captured here.
- This policy describes the current experiment dataset-v2 split; it does not prove unseen-subject generalization unless subject IDs are available and audited.
