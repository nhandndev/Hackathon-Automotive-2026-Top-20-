# Source Report - E-06 Ablation

| Evidence | Source | Note |
|---|---|---|
| `derived/label_inventory.json` | Evidence-local derived summary | Counts trip/frame/label from a local ignored dataset scan |
| `derived/label_counts.csv` | `frames[*].driver.state` summarized into evidence | Label count table by split |
| `reports/label_protocol.md` | Dataset schema + owner note | Documents that episode protocol is required before ablation |
| `commands/commands.log` | Repo evidence checks | How to re-check evidence files |

## Current conclusion

Frame-level C2 label evidence has been summarized into `evidence/E-06/derived/label_inventory.json`, but it is not enough to create raw-alert-vs-orchestrated ablation because episode-level labels are missing.

## Not claimed

- No Decision Engine false-alarm reduction percentage is claimed.
- No `ablation.csv` is claimed.
- No episode labels are inferred from frame labels without owner-approved protocol.

## Repo note

Original raw dataset is local-only/gitignored. Repo evidence is the derived files in this folder.
