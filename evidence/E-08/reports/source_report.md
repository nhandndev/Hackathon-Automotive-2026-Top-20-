# Source Report - E-08 C2 Dependencies

File này trả lời câu hỏi: evidence nào lấy nguồn từ đâu.

| Evidence file | Nguồn trong repo | Ý nghĩa |
|---|---|---|
| `c2_artifact_manifest.json` | `HACKATHON/AI/models/`, `HACKATHON/AI/configs/challenge2.yaml`, `HACKATHON/AI/models/face_landmark_models.manifest.yaml` | Manifest tổng hợp artifact runtime C2 |
| `preflight.log` | Chạy Python import/load model thực tế trong `.venv` | Chứng minh dependency và model load được |
| `model_hashes.txt` | `Get-FileHash SHA256` trên model/config/ONNX | Chốt đúng artifact, tránh nhầm model |
| `source_licenses/yunet_source.txt` | `HACKATHON/AI/models/face_landmark_models.manifest.yaml` | Nguồn + license YuNet |
| `source_licenses/face_landmark_468_source.txt` | `HACKATHON/AI/models/face_landmark_models.manifest.yaml` | Nguồn + note license/redistribution FaceMesh-compatible ONNX |
| `source_licenses/random_forest_model_note.txt` | `HACKATHON/AI/models/candidate_013.joblib`, project training lineage | Note model RF team-trained |
| `README.md` | Các file evidence ở folder này | Tóm tắt đã làm/chưa làm |

## Source chain

```text
challenge2.yaml
  -> face_detection_yunet_2023mar.onnx
  -> face_landmark_468.onnx
  -> legacy_59 temporal features
  -> candidate_013.joblib
  -> predicted_driver_state
```

## Manual evidence còn thiếu

- Screenshot/PDF upstream source/license page nếu BTC yêu cầu ảnh.
- Owner/legal review redistribution cho `face_landmark_468.onnx` trước public release.
