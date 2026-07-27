# FPTU DMS Vision — AI Fleet Management & Driver Intelligence Platform

README này là điểm bắt đầu bắt buộc cho thành viên **AI**, **Backend**, **Frontend** và mọi AI coding agent làm việc trong repository. Đọc file này trước khi Vibe Coding, sau đó đọc code và tài liệu đúng phạm vi task.

> Repository đang phát triển nhanh. `docs/` chứa toàn bộ context nghiên cứu và kế hoạch của nhóm nhưng có thể có nội dung cũ, giả thuyết hoặc contract chưa cập nhật. Không được dùng một đoạn tài liệu đơn lẻ để ghi đè code/test đang chạy.

## 1. Dự án làm gì?

FPTU DMS Vision tham gia Connected Car Hackathon 2026, xử lý dữ liệu road camera, cabin camera và telemetry để tạo năm output nộp bài:

1. **Prediction CSV:** 10 file `T01d.csv`–`T10d.csv`, mỗi file 1.800 frame.
2. **GitHub repository:** code, cấu hình và tài liệu có thể tái lập.
3. **Demo:** Fleet Dashboard, replay chuyến đi và CarSky HMI khi integration sẵn sàng.
4. **Implementation Notes:** giải thích thuật toán, thí nghiệm, metric và hạn chế.
5. **Usage Notes:** hướng dẫn cài đặt và chạy lại bằng lệnh thật.

Ba challenge chính:

| Challenge | Đầu ra | Mục tiêu |
|---|---|---|
| Challenge 1 — Collision Risk | `predicted_ttc` | Ước lượng Time-to-Collision; `inf` khi không có nguy cơ |
| Challenge 2 — Driver Intelligence | `predicted_driver_state` | Phân loại `alert`, `drowsy`, `yawning`, `distracted`, `microsleep` |
| Challenge 3 — Risk Fusion | `predicted_risk_score` | Điểm rủi ro frame 0–100 và aggregate an toàn cấp trip |

Sản phẩm demo mở rộng năm output thành Driver HUD, Fleet Manager Dashboard, event timeline, báo cáo doanh nghiệp, AI Copilot và CarSky HMI.

## 2. Kiến trúc tổng thể

```text
Road camera ──→ AI Road/TTC ─────────┐
Cabin camera → AI Driver State ──────┼→ AI Fusion/Risk → AITrip JSON
Telemetry ───→ Motion/behavior ──────┘                      │
                                                            ▼
                                              FastAPI validate + cache
                                                │        │        │
                                                ▼        ▼        ▼
                                              REST   WebSocket  CarSky
                                                │      20 FPS    Signals
                                                └────────┬────────┘
                                                         ▼
                                             Dashboard / HUD / HMI
```

Nguyên tắc output-driven:

- Có một Core AI duy nhất cho inference và evaluation.
- Script sinh CSV và demo phải gọi lại cùng Core, không copy thuật toán.
- Backend phân phối và tổng hợp output AI; không tạo một risk truth khác.
- Extension như Fleet Dashboard, Copilot và CarSky không được làm chậm hoặc phá pipeline CSV bắt buộc.

## 3. Cấu trúc repository

```text
HACKATHON/
├── AI/                         # Không gian làm việc của AI team
│   ├── core/                   # TTC, driver state, fusion/risk
│   ├── configs/                # Threshold/model/runtime config
│   ├── scripts/                # Inference, evaluation, export
│   └── extensions/             # Phần mở rộng không thuộc core submission
├── SE/
│   ├── BE/                     # FastAPI Backend — Nhân
│   │   ├── app/core/           # Settings, errors, lifecycle
│   │   ├── app/domain/         # Canonical schemas/interfaces
│   │   ├── app/adapters/       # File/external integrations
│   │   ├── app/modules/        # Fleet, streaming, coaching, reports
│   │   ├── tests/              # Automated tests
│   │   ├── scripts/            # Submission/export utilities
│   │   └── docs/phases/        # Backend implementation phases
│   └── FE/
│       └── index.html          # Dashboard prototype hiện tại
├── docs/                       # Context, nghiên cứu, kế hoạch, starter-kit
│   └── MockDataSet/            # Mô tả/mock contract để phối hợp
├── carsky/                     # Guide local, đã git-ignore
├── index.html                  # CarSky technical guide bản root/local
└── README.md                   # Project constitution này
```

Không tự di chuyển ownership giữa `AI/`, `SE/BE/` và `SE/FE/`. Shared contract được thay đổi tại boundary, không sửa logic của team khác để “chạy tạm”.

## 4. Team ownership

| Nhóm/vai trò | Sở hữu |
|---|---|
| AI Road | Object tracking, collision cone, TTC, confidence và evaluation Challenge 1 |
| AI Driver | Face/eye/mouth/head features, temporal state và evaluation Challenge 2 |
| AI Fusion | Behavior/risk model, calibration và output Challenge 3 |
| Nhân — Backend | FastAPI, canonical ingestion, cache, REST, WebSocket, Copilot gateway, CarSky adapter, exporter |
| Thiện — Frontend | Driver HUD, Fleet Dashboard, replay controls, map/charts, Copilot UI, HMI presentation |

Tên hoặc feature mới của thành viên có thể chưa xuất hiện trong README. Ownership thực tế trong branch/code mới phải được kiểm tra trước khi sửa; không xóa feature chỉ vì README chưa kể đến.

## 5. Source of truth và cách xử lý tài liệu outdated

Khi hai nguồn mâu thuẫn, dùng thứ tự sau:

1. Yêu cầu mới nhất đã được team/owner xác nhận.
2. Test đang pass và executable schema/interface.
3. Code đang được sử dụng trong pipeline hiện tại.
4. Phase/contract đúng subsystem.
5. Tài liệu nghiên cứu và kế hoạch trong `docs/`.

Quy tắc đọc trạng thái:

- **Implemented:** có code nhưng chưa chắc đúng hoặc đủ test.
- **Verified:** có test/acceptance pass; đây mới là trạng thái tin cậy.
- **Proposed:** chỉ có trong tài liệu; không được mô tả như đã triển khai.
- **Legacy/Outdated:** mâu thuẫn schema/test mới; chỉ dùng để hiểu lịch sử.

Không “sửa code cho giống tài liệu cũ”. Nếu code mới có feature hợp lệ nhưng docs thiếu, giữ feature, kiểm thử và cập nhật tài liệu. Nếu thay đổi contract, phải cập nhật producer, consumer, fixture và test trong cùng thay đổi hoặc cung cấp compatibility layer.

### Bản đồ tài liệu

| Tài liệu | Dùng để làm gì | Mức tin cậy |
|---|---|---|
| [`BAO_CAO_STARTER_KIT.md`](docs/BAO_CAO_STARTER_KIT.md) | Quy định starter kit, dataset, evaluation và submission | Nguồn nghiên cứu quan trọng; đối chiếu file BTC thật |
| [`01_Phan_tich...md`](docs/01_Phan_tich_bai_toan_truoc_khi_build_core%20(3).md) | Driver/TTC/risk reasoning và edge cases | Research/giả thuyết; threshold phải được validate |
| [`02_Kien_truc...md`](docs/02_Kien_truc_He_thong_Output_Driven%20(3).md) | Kiến trúc Core tạo 5 output | Kiến trúc định hướng |
| [`03_Ke_hoach...md`](docs/03_Ke_hoach_San_xuat_Output_Nop_Bai%20(2).md) | Lịch sản xuất và checklist output | Kế hoạch; ngày/trạng thái có thể outdated |
| [`04_Chien_luoc...md`](docs/04_Chien_luoc_Toi_da_hoa_Diem_5_Output%20(1).md) | Chiến lược tối ưu điểm | Tham khảo chiến thuật |
| [`KeHoach_Dashboard...md`](docs/KeHoach_Dashboard_Agile_Thien_Nhan%20(3).md) | SRS/UI/BE feature map | Context sản phẩm; API/schema có thể legacy |
| [`DatasetMock.md`](docs/MockDataSet/DatasetMock.md) | Hình dạng output AI nhóm đang thống nhất | Intent/mock; ví dụ chưa chắc là JSON hợp lệ |
| [`SE/BE/docs/phases`](SE/BE/docs/phases/) | Contract và Definition of Done Backend | Nguồn triển khai Backend hiện hành |
| [`ai_contract.py`](SE/BE/app/domain/schemas/ai_contract.py) | Pydantic contract Backend đang chạy | Executable source of truth hiện tại |

## 6. Data contract giữa AI và SE

Backend canonical nhận một trip:

```text
AITrip
├── trip_id
├── metadata
│   ├── trip_id, description, duration_sec, fps, map
│   ├── driver_profile, carla_version, random_seed
│   └── speed_limit_kmh
└── frames[]
    ├── frame_id, timestamp
    ├── ego
    │   ├── speed_kmh, longitudinal_accel, lateral_accel
    │   └── geolocation {lat, lon, alt}
    ├── driver
    │   ├── state, alertness_score
    │   └── eye_state, head_pose, mouth_state, nthu_subject_id
    ├── min_ttc, headway_sec
    ├── behavior_flags
    └── risk {base_risk, driver_factor, final_risk_score}
```

Quy tắc bất biến tại integration boundary:

- AI sở hữu `driver`, `min_ttc`, `headway_sec`, `behavior_flags` và `risk` trong output canonical.
- Backend validate, cache, aggregate và phân phối; không ghi đè `risk.final_risk_score` của AI.
- Backend enrichment phải nằm namespace riêng, không trộn vào raw AI frame.
- `trip_id` root phải bằng `metadata.trip_id`.
- Driver enum: `alert|drowsy|yawning|distracted|microsleep`.
- Score trong 0–100; `alertness_score` trong 0–1; speed không âm.
- Positive infinity lưu nội bộ bằng `float("inf")`; REST/WebSocket xuất chuỗi `"Infinity"`.
- Submission CSV dùng `inf`, không dùng chuỗi JSON `"Infinity"`.
- Literal `Infinity` không phải JSON chuẩn. Ví dụ trong `DatasetMock.md` chỉ mô tả field, không copy nguyên văn làm fixture.
- Extra AI fields phải round-trip không mất dữ liệu.

Submission CSV đầy đủ:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Mỗi trip mục tiêu: `T01d`–`T10d`, 1.800 dòng, frame `0..1799`, 20 FPS và timestamp bước 0,05 giây. Nếu file BTC thật khác, file BTC và evaluator chính thức ưu tiên hơn giả định này.

## 7. Contract SE và runtime

### Backend

- Runtime chuẩn: Python 3.11.
- Framework: FastAPI + Pydantic v2.
- REST prefix chính: `/api/v1`; `/api` là compatibility alias tạm thời.
- Public endpoints, không authentication/authorization.
- Không login, JWT, session, role, permission hoặc inbound API-key middleware.
- Credential AI/LLM/CarSky chỉ dùng cho outbound integration.
- Health: `GET /health`.
- Readiness: `GET /ready`.
- Swagger: `GET /docs`.
- Replay target: `WS /ws/replay/{trip_id}`, 20 FPS.

```bash
cd SE/BE
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd SE/BE
source .venv/bin/activate
pytest -q
```

Hiện Phase 01 đã verified với 19 test trên Python 3.11. `/ready` được phép trả 503 trước khi Phase 02 nạp đủ dataset/cache.

### Frontend

- Prototype hiện tại: `SE/FE/index.html`.
- Dùng Tailwind CDN, Leaflet, Chart.js và Lucide.
- Một số URL trong prototype còn là legacy, ví dụ `/api/coaching/generate`; phải đối chiếu OpenAPI trước khi khóa integration.
- Frontend không tự tính lại AI risk; chỉ render raw AI data và Backend enrichment.
- Replay UI phải có state riêng cho play/pause/seek/speed và không giả định mọi frame đến đúng giờ.

### CarSky HMI

- CarSky guide local được git-ignore; thành viên mới có thể cần nhận guide riêng.
- Backend gửi qua Signals API; không dùng `/shell`, `/tap`, `/text` làm alert channel production.
- Signal Watch chỉ debug; Screen Widget chỉ phản chiếu HMI app.
- HMI consumer phải chạy trong Skycraft Android/custom runtime.
- Critical alert gửi theo episode transition, không gửi lặp 20 lần/giây.
- TTS lỗi không được làm hỏng visual critical alert, REST hoặc WebSocket.
- Runbook: [`PHASE_05_1`](SE/BE/docs/phases/PHASE_05_1_CARSKY_HMI_RUNBOOK.md) và [`PHASE_05_2`](SE/BE/docs/phases/PHASE_05_2_CARSKY_HMI_ACTION_CHECKLIST.md).

## 8. Trạng thái hiện tại

| Khu vực | Trạng thái quan sát được |
|---|---|
| Backend Phase 01 | Verified: app chạy, canonical schema/config/error/health/readiness; 19 test pass |
| Backend Phase 02–06 | Có spec chi tiết; code legacy tồn tại một phần, chưa được coi là hoàn thành |
| AI | Đang được thành viên chỉnh sửa; không giả định skeleton/file cũ vẫn là implementation hiện hành |
| Frontend | Có dashboard prototype một file HTML; integration contract còn cần đồng bộ |
| CarSky | Có tài liệu/runbook; integration thật cần credential, Blueprint, VSS, Room/node và HMI app |
| Submission | Có script khởi đầu; phải validate lại bằng evaluator/file BTC chính thức |

## 9. Quy trình Vibe Coding bắt buộc

### Trước khi code

1. Đọc README này.
2. Chạy `git status`; mọi thay đổi chưa commit có thể thuộc thành viên khác.
3. Đọc file phase/spec liên quan và code/test hiện tại.
4. Xác định owner và consumer của feature.
5. Ghi rõ feature đang ở `PROPOSED`, `IMPLEMENTED` hay `VERIFIED`.
6. Chốt acceptance criteria trước khi sửa nhiều file.

### Trong khi code

- Không xóa/reset/format hàng loạt thay đổi của người khác.
- Không tự thay contract AI, REST, WebSocket hoặc CSV.
- Không hard-code absolute path, secret, API key, Room ID hoặc Node Key.
- Không thêm authentication/authorization nếu chưa có quyết định mới của nhóm.
- Không biến `Infinity` thành `0`.
- Không để Backend tự tạo risk thay thế AI canonical.
- Không gọi external AI/LLM/CarSky đồng bộ trong vòng lặp WebSocket 50 ms.
- Không copy thuật toán Core sang demo/exporter; import và tái sử dụng.
- Mọi fallback phải deterministic và được gắn nguồn/trạng thái rõ ràng.
- Thêm hoặc cập nhật test cùng behavior mới.

### Sau khi code

1. Chạy test/lint/smoke test phù hợp.
2. Kiểm tra producer và mọi consumer của contract.
3. Cập nhật README/phase nếu kiến trúc, interface hoặc cách chạy thay đổi.
4. Báo file đã đổi, test đã chạy, phần chưa test và input còn thiếu.
5. Chỉ ghi `VERIFIED` khi acceptance test thực sự pass.

## 10. Cách xử lý feature mới và README bị outdated

Feature mới của thành viên là bình thường. AI Agent không được xóa feature đó chỉ vì không thấy trong README.

Phân loại thay đổi:

| Loại | Ví dụ | Cách xử lý |
|---|---|---|
| Local, không đổi contract | Tối ưu UI, refactor nội bộ | Giữ behavior, thêm test, cập nhật usage nếu cần |
| Thêm field optional | Thêm confidence/evidence | Producer thêm, consumer bỏ qua được, schema `extra=allow`, thêm round-trip test |
| Đổi contract | Rename field, endpoint, enum | Cần owner xác nhận, compatibility alias/migration và test hai phía |
| Đổi ownership/risk formula | Backend tính thay AI | Không tự làm; phải có quyết định nhóm và cập nhật architecture |
| Thay output nộp bài | Cột CSV, số dòng, tên file | Chỉ theo BTC/evaluator chính thức, cần dry-run |

Khi phát hiện code mới hơn README:

1. Không revert code.
2. Đọc commit/diff/test và hỏi owner nếu mục đích chưa rõ.
3. Nếu feature đã verified, cập nhật README và phase.
4. Nếu mới implemented nhưng chưa test, giữ trạng thái `IMPLEMENTED`, bổ sung acceptance test.
5. Nếu mâu thuẫn contract ảnh hưởng team khác, dừng integration và lập danh sách producer/consumer cần migrate.

Feature làm thay đổi interface nên có tài liệu ngắn trong `docs/features/` với: mục tiêu, owner, input/output, affected consumers, compatibility, test và trạng thái. Tài liệu này không thay thế test hoặc canonical schema.

## 11. Thứ tự ưu tiên triển khai

```text
1. CSV hợp lệ và Core AI tái lập được
2. Contract AI ↔ Backend ổn định
3. Backend ingestion/cache
4. REST fleet/trip APIs
5. WebSocket replay 20 FPS
6. Frontend integration
7. Copilot và CarSky extension
8. Submission validation, demo và tài liệu cuối
```

Không để extension bonus làm trễ CSV, evaluation hoặc pipeline core.

## 12. Definition of Done chung

Một task chỉ hoàn thành khi:

- Behavior đúng acceptance criteria.
- Contract và ownership không bị phá.
- Test liên quan pass.
- Không làm mất dữ liệu AI hoặc thay đổi output âm thầm.
- Cách chạy được ghi lại nếu có thay đổi.
- Không chứa secret, absolute path hoặc dataset/model lớn trong Git.
- Có fallback rõ ràng cho external service nếu task yêu cầu.
- Nêu rõ phần bắt buộc con người kiểm tra: model quality, UI usability, CarSky device hoặc quy định BTC.

Nếu chưa đủ bằng chứng, dùng `IMPLEMENTED`, không dùng `DONE/VERIFIED`.
