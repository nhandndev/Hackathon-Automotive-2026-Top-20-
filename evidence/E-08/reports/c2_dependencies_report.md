# E-08 - Challenge 2 Dependencies Evidence

Mục tiêu: chứng minh Challenge 2 có đủ artifact runtime, model path rõ ràng, nguồn/license của ONNX được ghi lại, và môi trường demo có thể load được dependency.

## Đã làm được trong repo

| Evidence | File |
|---|---|
| Artifact manifest tổng hợp | `c2_artifact_manifest.json` |
| Log preflight môi trường + model/config tồn tại | `preflight.log` |
| SHA256 + size cho model/config/ONNX | `model_hashes.txt` |
| Note nguồn/license YuNet | `source_licenses/yunet_source.txt` |
| Note nguồn/license FaceMesh-compatible 468 ONNX | `source_licenses/face_landmark_468_source.txt` |
| Note model Random Forest team-trained | `source_licenses/random_forest_model_note.txt` |

## Chưa làm được / cần owner xác nhận

| Việc còn lại | Lý do |
|---|---|
| Screenshot/PDF trang source/license upstream | Cần capture thủ công nếu BTC yêu cầu bằng chứng dạng ảnh |
| Xác nhận redistribution cho `face_landmark_468.onnx` | Repo manifest có ghi nguồn converted artifact và note cần review redistribution |
| Dataset provenance/license cho model RF | Thuộc nhóm evidence dữ liệu/training, không phải dependency runtime |

## Kết luận

E-08 đã đủ phần runtime evidence cơ bản: artifact hiện diện, hash rõ ràng, config/model schema khớp, môi trường load được dependency và preflight PASS.
