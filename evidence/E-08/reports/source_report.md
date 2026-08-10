# Source Report - E-08 C2 Dependencies

| Evidence | Source | Note |
|---|---|---|
| `derived/c2_artifact_manifest.json` | `HACKATHON/AI/models/candidate_013.joblib`, `HACKATHON/AI/configs/challenge2.yaml`, `evidence/E-08/raw/source_licenses/` | Repo-pushable C2 dependency manifest |
| `derived/preflight.log` | Local runtime check log copied into evidence | May mention local runtime binaries; not used as repo source path |
| `derived/model_hashes.txt` | Hash snapshot copied into evidence | Hash evidence for runtime artifacts; ONNX binaries are not cited as repo-pushable paths |
| `raw/source_licenses/yunet_source.txt` | Source/license note | Repo-pushable note for YuNet runtime dependency |
| `raw/source_licenses/face_landmark_468_source.txt` | Source/license note | Repo-pushable note for Face Landmark runtime dependency |
| `commands/commands.log` | Repo evidence checks | How to check evidence files |

## Current conclusion

- C2 model `candidate_013.joblib` is tracked/pushable in the repo.
- C2 config `challenge2.yaml` is tracked/pushable in the repo.
- YuNet and Face Landmark runtime binaries are local runtime material/gitignored, so they are not cited as repo evidence paths.
- Repo-pushable evidence for those runtime dependencies is the source/license notes and hash snapshot in `evidence/E-08/`.
- No upstream license screenshot/PDF is present in this folder.
- No legal redistribution review for the Face Landmark runtime binary is present; only source notes exist.

## Not inferred

- This file does not prove training dataset license completeness.
- This file does not prove domain gap/drift; that belongs to E-42.
- This file does not guarantee runtime binaries exist after a fresh clone if they remain in `.gitignore`; a model/release artifact channel is needed.
