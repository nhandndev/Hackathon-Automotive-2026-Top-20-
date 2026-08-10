# E-08 - Challenge 2 Dependencies Evidence

Goal: prove the repo contains enough evidence to trace C2 runtime dependencies. It does not claim every runtime binary is pushed directly if it is currently ignored by `.gitignore`.

| Group | Repo evidence status | Evidence |
|---|---:|---|
| Random Forest C2 | Tracked/pushable | `HACKATHON/AI/models/candidate_013.joblib`, `derived/c2_artifact_manifest.json` |
| YuNet runtime dependency | Binary local/gitignored; repo has note/hash | `raw/source_licenses/yunet_source.txt`, `derived/model_hashes.txt` |
| Face Landmark runtime dependency | Binary local/gitignored; repo has note/hash | `raw/source_licenses/face_landmark_468_source.txt`, `derived/model_hashes.txt` |
| Runtime config | Tracked/pushable | `HACKATHON/AI/configs/challenge2.yaml` |
| Upstream license screenshot/PDF | Missing | Capture manually if BTC requires it |
| Redistribution/legal review | Missing | Owner/legal confirmation required |

Conclusion: E-08 contains basic dependency evidence in the repo. If a fresh clone demo needs ONNX binaries, they must be supplied through a model/release artifact channel or intentionally added to the repo.
