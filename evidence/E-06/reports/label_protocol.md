# E-06 - Label Protocol Source for C2 Ablation

Available label evidence is summarized in `evidence/E-06/derived/label_inventory.json`.

Original dataset folders contain BTC-style trips and converted crawled/Kaggle trip folders. Frame labels were read from:

```text
frames[*].driver.state
```

Observed / used C2 label set:

```text
alert
drowsy
yawning
distracted
microsleep
```

## What ablation still needs

E-06 is not normal C2 accuracy. It asks:

```text
raw alert stream vs orchestrated/decision-engine alert stream
```

Currently we only have frame-level labels. To create a real `ablation.csv`, an episode-level protocol is still required:

- what counts as one alert episode,
- minimum duration,
- how duplicate alerts are scored,
- how episode-level false alarm is defined,
- where episode ground truth comes from.

Without this protocol, ablation results would be arbitrary.
