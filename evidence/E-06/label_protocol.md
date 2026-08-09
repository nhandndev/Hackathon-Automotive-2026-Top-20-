# E-06 - Label Protocol Source for C2 Ablation

User note: for Challenge 2, use `experiment/dataset-v2`.

## Available dataset structure

```text
experiment/dataset-v2/
  train/
  valid/
  .ch2_feature_cache/schema_v4/
```

The dataset contains BTC-style trip folders and converted crawled/Kaggle trip folders:

- `T01d`, `T02d`, ...
- `T_claw_train_*`
- `T_claw_test_*`

## Label set used by C2

```text
alert
drowsy
yawning
distracted
microsleep
```

## Ablation meaning

E-06 is not normal C2 accuracy. It asks:

```text
raw alert stream vs orchestrated/decision-engine alert stream
```

Meaning:

- Raw alert = every frame/episode where model/rule says risky.
- Orchestrated alert = events after Decision Engine persistence, cooldown, recovery and severity policy.

## Current status

Dataset-v2 can provide the C2 labels/features, but ablation still needs an episode protocol:

- what counts as one alert episode,
- minimum duration,
- how to score duplicate alerts,
- what false alarm means at episode level.

Without this protocol, generating `ablation.csv` would be arbitrary.
