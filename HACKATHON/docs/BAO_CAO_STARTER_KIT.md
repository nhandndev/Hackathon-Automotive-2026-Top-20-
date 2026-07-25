# Báo cáo nghiên cứu Hackathon Starter Kit

> Phạm vi: toàn bộ thư mục `package_starterkit/` trong bộ tài liệu nhận được.
> Báo cáo được lập bằng cách đối chiếu README, hướng dẫn người mới, notebook và mã nguồn Python. Vì dataset thật không có trong thư mục hiện tại nên các nhận định về dữ liệu là từ schema/tài liệu và mã loader, không phải kết quả chạy mô hình trên dữ liệu thật.

## 1. Kết luận nhanh

Đây là **starter kit cho hackathon AI của FPT Automotive**, không phải một ứng dụng hoàn chỉnh. Nó giúp đội thi:

1. đọc bộ dữ liệu chuyến xe (*trip*) gồm camera đường, camera cabin, telemetry và nhãn;
2. chạy một baseline TTC đơn giản để làm mốc;
3. tự chấm dự đoán trên các trip luyện tập có nhãn;
4. xuất CSV để nộp dự đoán cho các trip chấm điểm;
5. trực quan hoá dữ liệu bằng Jupyter hoặc, nếu cần, truy vấn qua HTTP cục bộ.

Ba bài toán là: dự đoán **TTC** theo frame, phân loại **trạng thái tài xế** theo frame, và điểm **an toàn chuyến đi** theo trip. Đội có thể làm một hoặc nhiều bài toán.

Điểm cần nhớ nhất: chỉ 6 trip `T01-Sample`–`T06-Sample` có ground truth để phát triển và tự chấm. Mười trip `T01d`–`T10d` bị ẩn nhãn có chủ đích; chúng là dữ liệu để sinh CSV nộp ban tổ chức.

## 2. Hiện trạng bộ file đã nhận

Thư mục dự án thực tế là `package_starterkit/` (thư mục con của nơi mở workspace). Thành phần hiện có:

| Đường dẫn | Vai trò |
|---|---|
| `README.md` | Tài liệu kỹ thuật chính: dataset, challenge, API, format CSV và baseline. |
| `requirements.txt` | Dependency Python cần cài. |
| `data/PUT_DATASET_HERE.txt` | Nhắc cách đặt dataset; không chứa dữ liệu. |
| `team_kit/dataset_loader.py` | Thư viện đọc trip, ảnh, calibration và DataFrame. |
| `team_kit/baseline_ttc_predictor.py` | Baseline TTC bằng stereo OpenCV; có CLI. |
| `team_kit/evaluation.py` | Bộ chấm local cho cả 3 challenge; có CLI. |
| `team_kit/explore_trip.ipynb` | Notebook xem dữ liệu/biểu đồ/ảnh mẫu. |
| `team_kit/local_stream_server.py` | HTTP server cục bộ tuỳ chọn; không bắt buộc. |
| `team_kit/HUONG_DAN_NGUOI_MOI.md/.html` | Hướng dẫn dễ tiếp cận bằng tiếng Việt. |
| `team_kit/__init__.py` | Đánh dấu `team_kit` là Python package. |

### Trạng thái kiểm tra tại thời điểm báo cáo

- Chỉ có thư mục placeholder `data/`, chưa có bất kỳ trip nào.
- Windows Python Launcher (`py.exe`) có mặt nhưng báo **“No installed Pythons found”**. Vì vậy chưa thể chạy smoke test, baseline hoặc evaluator trên máy hiện tại cho đến khi cài Python.
- Do chưa có dataset, không thể tạo prediction thật hay xác nhận số liệu baseline. Đây không phải lỗi của starter kit.

## 3. Kiến trúc và luồng làm việc

```text
Dataset trip (ảnh đường + ảnh cabin + JSON + calib)
                    |
                    v
          TripDataset / HackathonDataset
           |             |             |
           |             |             +--> notebook / HTTP local (tuỳ chọn)
           |             +--> model trạng thái tài xế (Challenge 2)
           +--> model TTC (Challenge 1) --> TTC dự đoán
                                              |
Telemetry gốc ------------------------------->|--> điểm Safe Driving (Challenge 3)
                                              v
                            predictions/<team>/<trip_id>.csv
                                              |
                       evaluation.py trên trip Sample / ban tổ chức trên T0Xd
```

Luồng khuyến nghị là: hiểu dữ liệu bằng notebook → phát triển trên 6 trip Sample → tự chấm local → chạy inference trên 10 trip `d` → kiểm tra CSV → nộp theo quy định của ban tổ chức.

## 4. Dataset và chính sách ẩn nhãn

### 4.1. Hai tập trip

| Tập | ID | Quy mô | Mục đích | Ground truth |
|---|---|---:|---|---|
| Luyện tập | `T01-Sample`–`T06-Sample` | Khoảng 30 giây, 600 frame/trip | Build, debug, tự chấm | Có đầy đủ |
| Chấm điểm | `T01d`–`T10d` | Khoảng 90 giây, 1.800 frame/trip | Sinh dự đoán để nộp | Bị ẩn |

Tần số khung hình là 20 FPS, tương đương khoảng 0,05 giây/frame. Sáu trip Sample, khi gộp lại, có đủ 5 trạng thái tài xế và bốn loại event kịch bản: `pedestrian_jaywalk`, `motorcycle_cut_in`, `lead_brake`, `stopped_vehicle_ahead`.

### 4.2. Cấu trúc một trip

Ví dụ `data/T01-Sample/`:

```text
T01-Sample/
├── T01-Sample.json.gz          # hoặc .json: metadata, frame records, aggregate
├── driver/                     # ảnh camera cabin theo frame
└── kitti/
    ├── image_2/                # ảnh RGB trái, bản phát hành 640×360
    ├── image_3/                # ảnh RGB phải; stereo baseline 30 cm
    ├── depth/                  # depth .npy, chỉ có ở keyframe
    ├── calib/                  # KITTI calibration theo frame
    ├── label_2/                # nhãn KITTI 2D/3D
    └── calibration_info.txt    # intrinsics/baseline tổng quát cho stereo
```

Ảnh được loader đọc bằng OpenCV nên mảng ảnh có thứ tự kênh **BGR**, không phải RGB. Ảnh đường có thể là `.png`, `.jpg` hoặc `.jpeg`; loader tự thử các đuôi này. Ảnh driver có tên dạng `frame_000000.jpg` (hoặc PNG/JPEG tương đương); ảnh đường dùng dạng `000000.jpg`.

### 4.3. Những gì bị ẩn ở 10 trip chấm điểm

Không được xem các giá trị sau là bug nếu chúng `unknown`, `0`, `inf`, `{}` hoặc không có file:

- `frames[].driver`: state, alertness, mắt, đầu, miệng và ID subject;
- TTC/động học mục tiêu: `targets[].rel_pos`, vận tốc tương đối, khoảng cách, closing speed, TTC, collision cone;
- `min_ttc`, `headway_sec`, `behavior_flags`, `risk` theo frame;
- `trip_aggregate`, `driver_summary`;
- vị trí/rotation/geolocation của ego (nhưng vẫn giữ speed và acceleration);
- chi tiết `events_log[].params` (vẫn giữ loại event và thời điểm);
- file mapping driver lịch sử `T0Xd_nthu_mapping.json`;
- trường vị trí 3D `location` của `kitti/label_2/*.txt` bị ghi thành `0.00 0.00 0.00`.

Các input vẫn hợp lệ ở toàn bộ 16 trip gồm: ảnh đường/cabin, bbox và các trường KITTI không bị nêu trên, tốc độ, gia tốc dọc/ngang, `target_id`/`target_class`, loại event và thời điểm event. Trường/đường dẫn có chữ `nthu` là tên lịch sử; ảnh cabin thực tế có nguồn DMD, không phải NTHU-DDD gốc.

## 5. Ba challenge và cách chấm

### 5.1. Challenge 1 — Collision Risk Monitor

Đầu ra là `predicted_ttc`, đơn vị giây, cho từng frame. `inf` có nghĩa không phát hiện nguy cơ va chạm/không có vận tốc đóng.

| Đại lượng | Quy tắc trong `evaluation.py` |
|---|---|
| Vùng critical | TTC thật `< 3.0 s`; dùng cho MAE-critical. |
| Vùng danger | TTC thật `< 2.0 s`; dùng cho phân loại nhị phân và F1. |
| MAE-critical | Trung bình `|TTC dự đoán - TTC thật|` chỉ trên vùng critical. Khi tính chênh lệch, `inf` được clip thành 99. |
| inverse TTC MAE | MAE của `1/TTC`; giá trị TTC không hữu hạn cho đóng góp 0. |
| F1 | Dương tính khi TTC dự đoán `< 2.0 s`; so với nhãn danger thật. |
| Điểm composite | `0.40 × mae_score + 0.30 × (100×F1) + 0.30 × inv_score`. |

Trong đó `mae_score = max(0, 100 - 20 × MAE-critical)` và `inv_score = max(0, 100 - 200 × inverse_TTC_MAE)`. Điểm càng cao càng tốt. Nếu trip không có frame critical, `mae_score` được đặt 50 trong code local.

### 5.2. Challenge 2 — Driver Intelligence Platform

Đầu ra bắt buộc (nếu làm challenge này) là một trong năm nhãn:

```text
alert | drowsy | yawning | distracted | microsleep
```

Đề bài cũng nêu alertness liên tục 0–1 như hướng mở rộng, nhưng format submission hiện tại **không có cột predicted alertness**; evaluator hiện chỉ chấm trạng thái 5 lớp. Điểm challenge 2 là:

```text
100 × (0.5 × Accuracy + 0.5 × Macro-F1)
```

Macro-F1 chỉ trung bình những lớp thực sự xuất hiện trong ground truth của trip đó. Các dòng trống ở cột driver state bị loại khỏi `n_scored` trong evaluator, tuy nhiên file nộp chính thức vẫn phải có dự đoán cho mọi frame.

### 5.3. Challenge 3 — Fleet Safe Driving Score

Challenge này cho một điểm 0–100 cấp trip. Code evaluator tái tạo điểm dự đoán như sau:

```text
near_miss = số frame có predicted_ttc hữu hạn và < 1.5 s
speeding% = 100 × số frame(speed > speed_limit + 5 km/h) / số frame

predicted_safe = clip[0,100](100
  - harsh_brake × 3.0
  - harsh_accel × 2.0
  - harsh_corner × 2.0
  - near_miss × 5.0
  - speeding% × 0.15)

composite = max(0, 100 - 2 × |predicted_safe - true_safe|)
```

Ngưỡng được mã hoá trong `evaluation.py` là phanh gấp `< -0.40g`, tăng tốc gấp `> +0.35g`, cua gấp `|lateral_accel| > 0.30g`, với `g = 9.81 m/s²`. Các số đếm harsh và speeding% được tính trực tiếp từ telemetry còn công khai, nên giống nhau cho mọi đội ở cùng một trip. Phần duy nhất phụ thuộc mô hình là `near_miss`, lấy từ chính `predicted_ttc`.

**Chi tiết rất quan trọng:** code hiện chỉ dùng `predicted_risk_score` như một cờ cho biết đội có làm Challenge 3 (ít nhất một ô không rỗng). Giá trị số của cột này không được đưa vào công thức. Dù vậy, vẫn phải nộp số thực 0–100 đúng format, vì đó là yêu cầu dữ liệu công bố và quy định nộp có thể được kiểm tra bên ngoài evaluator.

Công thức gốc còn thành phần tailgating, nhưng kit chưa thể tái tạo vì `headway_sec` bị ẩn và CSV không có cột dự đoán headway. Vì vậy điểm Challenge 3 local có thể lệch nhẹ so với công thức nội bộ hoàn chỉnh ở trip có bám đuôi.

## 6. Phân tích từng thành phần mã nguồn

### 6.1. `team_kit/dataset_loader.py`

Đây là API chính để đọc dữ liệu; không có CLI. `TripDataset(trip_dir)` chấp nhận đường dẫn bất kỳ tới **thư mục trip**, rồi đọc `<trip_id>.json.gz` ưu tiên trước `.json`. Ảnh và frame record được nạp lười: tạo `TripDataset` không đọc toàn bộ ảnh ngay.

`FrameRecord` có các nhóm trường sau:

| Nhóm | Trường tiêu biểu |
|---|---|
| Định danh/telemetry | `frame_id`, `timestamp`, `speed_kmh`, `longitudinal_accel`, `lateral_accel` |
| Driver GT | `driver_state`, `alertness_score`, `eye_state`, `head_pose`, `mouth_state`, `nthu_subject_id` |
| Risk/TTC GT | `min_ttc`, `headway_sec`, `base_risk`, `driver_factor`, `final_risk_score` |
| Hành vi | `is_harsh_brake`, `is_harsh_accel`, `is_harsh_corner`, `is_speeding`, `is_tailgating` |
| Ngữ cảnh | `targets`, `events_active` |

API quan trọng:

| Lệnh/thuộc tính | Kết quả |
|---|---|
| `len(ds)`, `ds[i]`, `ds.iter_frames()` | Số frame, một `FrameRecord`, hoặc iterator frame. |
| `ds.frames_df` | DataFrame một hàng/frame; TTC/headway `inf` được thể hiện là 99 và có cờ `min_ttc_inf`. |
| `ds.load_left(id)`, `ds.load_right(id)` | Mảng BGR `H×W×3` camera stereo. |
| `ds.load_driver(id)` | Mảng BGR cabin. |
| `ds.load_depth(id)` | Depth `float32` tính bằng mét hoặc `None` nếu không phải keyframe. |
| `ds.load_calibration()` | JSON calibration tổng quát (`K_left`, `baseline_m`, `P2_left`, `P3_right`) cho baseline. |
| `ds.load_frame_calibration(id)` | Calibration KITTI chuẩn theo frame: `P0`–`P3`, `R0_rect`, `Tr_velo_to_cam`, `Tr_imu_to_velo`. |
| `ds.summary()` | Dict tóm tắt trip. |
| `ds.metadata`, `ds.trip_aggregate`, `ds.driver_summary`, `ds.events_log` | Metadata/aggregate/tổng kết driver/event. |

`HackathonDataset(data_root)` dùng khi thư mục cha chứa nhiều trip: `trip_ids`, `get_trip(id)`, iterator và `summary_table()`. Pattern ID được nhận là `T<digits>`, tùy chọn hậu tố `d` hoặc `-Sample`.

### 6.2. `baseline_ttc_predictor.py`

Baseline này **không dùng deep learning**. Quy trình:

1. đổi hai ảnh stereo sang grayscale và dùng `cv2.StereoSGBM_create` để tạo disparity;
2. lấy ROI cố định giữa-dưới ảnh: `x=35%–65%`, `y=50%–85%`;
3. đổi disparity sang depth theo `depth = fx × baseline / disparity`;
4. chỉ giữ depth từ 1,5 m đến 80 m, cần ít nhất 100 pixel hợp lệ;
5. lấy median depth trong ROI, giữ lịch sử 5 frame;
6. fit hồi quy tuyến tính depth theo thời gian, closing speed là âm của slope;
7. nếu closing speed `<= 0,3 m/s`, trả `inf`; nếu không, `TTC = depth / closing_speed`.

SGBM mặc định có `numDisparities=96`, `blockSize=11`, `uniquenessRatio=10`, chế độ `SGBM_3WAY`. Tham số OpenCV phải giữ tên camelCase như `numDisparities`; đổi sang snake_case sẽ lỗi. Baseline không biết vị trí từng xe vì dùng ROI cố định, nên object detection + tracking là hướng cải thiện trực tiếp.

CLI baseline:

```powershell
python team_kit/baseline_ttc_predictor.py `
  --trip-dir .\data\T01-Sample `
  --output .\predictions\T01-Sample.csv `
  --verbose
```

CSV baseline có thêm `ground_truth_ttc` để tham khảo local. Cột này bị evaluator bỏ qua hoàn toàn và không nên giữ trong file nộp.

### 6.3. `evaluation.py`

Chạy được với một CSV hoặc cả thư mục CSV. Ground truth luôn được loader đọc lại từ `--trip-dir`/`--data-dir` đáng tin cậy; evaluator không bao giờ tin cột GT trong CSV. Đây là cơ chế chống việc giả mạo nhãn.

```powershell
# Chấm một trip Sample
python team_kit/evaluation.py `
  --predictions .\predictions\T01-Sample.csv `
  --trip-dir .\data\T01-Sample `
  --output .\evaluation\T01-Sample-report.json

# Chấm nhiều trip Sample trong một thư mục
python team_kit/evaluation.py `
  --predictions .\predictions `
  --data-dir .\data `
  --output .\evaluation\report-all-sample.json
```

Tên file phải khớp ID trip (`T01-Sample.csv`, `T01d.csv`…). Khi nhận thư mục, evaluator bỏ qua file không khớp pattern ID. Báo cáo tổng hợp là trung bình macro theo trip, tức mỗi trip có cùng trọng số.

Lưu ý khi đọc code: evaluator luôn tạo phần Challenge 1; nếu thiếu `predicted_ttc`, nó diễn giải là `inf`. Challenge 2 và 3 chỉ xuất hiện khi cột tương ứng có dữ liệu. Vì thế cần theo đúng challenge/team đăng ký và quy định chính thức của ban tổ chức, thay vì cố tình bỏ cột để tác động điểm local.

### 6.4. `explore_trip.ipynb`

Notebook có 8 phần: tổng quan trip/event log; timeline driver state và alertness; dynamics speed/acceleration; TTC/risk; phân bố driver state; bốn cặp ảnh mẫu; timeline behavior flags; aggregate trip. Cell setup tự tìm project root và mặc định `TRIP_DIR = PROJECT_ROOT / 'data' / 'T01-Sample'`.

Chạy notebook trước khi train để kiểm tra: ảnh BGR/RGB, frame/timestamp, nhãn hiện diện ở Sample, và telemetry/event còn hiện diện ở trip `d`. Nếu dùng matplotlib, cần đổi BGR sang RGB trước khi hiển thị.

### 6.5. `local_stream_server.py`

Đây là lựa chọn phụ, dành cho pipeline không phải Python hoặc dashboard. Nó cache `TripDataset` theo ID và dùng `ThreadingHTTPServer`. Mặc định bind `127.0.0.1:8765`, không có xác thực; không được public Internet hoặc mở `0.0.0.0` nếu không thật sự cần.

```powershell
python team_kit/local_stream_server.py --data-dir .\data --port 8765
```

Các route gồm `/trips`, `/trips/{id}/summary`, `/calibration`, `/events`, `/aggregate`, `/frames`, `/frames/{id}`, và các endpoint `/left`, `/right`, `/driver`, `/depth`. Ảnh/depth trả raw bytes; depth có thể 404 ở non-keyframe. Đây là pass-through, không khôi phục nhãn bị ẩn.

## 7. Thiết lập môi trường trên Windows (khuyến nghị)

Các lệnh dưới đây chạy tại thư mục chứa `requirements.txt` và `team_kit/`, cụ thể:

```powershell
cd "C:\FA Hackathon\team-kit\Package_starterkit\package_starterkit"
```

### Bước 1 — cài Python

Cài Python 3.10 trở lên từ trang Python chính thức. Khi cài trên Windows, chọn thêm Python vào PATH. Sau khi cài, mở terminal mới và kiểm tra:

```powershell
py --version
```

Máy hiện tại mới có `py.exe` nhưng chưa có interpreter; cần hoàn thành bước này trước khi làm các bước sau.

### Bước 2 — tạo môi trường ảo và cài dependency

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu PowerShell không cho activate script, không cần thay đổi cấu hình hệ thống; dùng trực tiếp interpreter của môi trường ảo:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dependency thực tế trong `requirements.txt` là `opencv-python>=4.8`, `numpy>=1.24`, `pandas>=2.0`, `matplotlib>=3.7`, `jupyter>=1.0`. Dòng chú thích README có nhắc `pyyaml`, nhưng file requirements và mã nguồn không import/cần `pyyaml`; không cần cài thêm cho starter kit này.

### Bước 3 — lấy và đặt dataset

Dataset phải do ban tổ chức cung cấp. Có thể để ở bất kỳ ổ/thư mục nào, miễn truyền đúng đường dẫn cho loader. Hai cách hợp lệ:

1. để nguyên nơi đã giải nén, ví dụ `D:\hackathon-data\T01-Sample`;
2. đặt các thư mục trip vào `package_starterkit\data\`, ví dụ `data\T01-Sample\...` và `data\T01d\...`.

Không được đổi tên ID thư mục trip. Khi có đủ dữ liệu, `data/` phải chứa trực tiếp 16 thư mục `T01d`–`T10d`, `T01-Sample`–`T06-Sample`.

### Bước 4 — smoke test trước khi chạy model

```powershell
python -c "from team_kit.dataset_loader import TripDataset; ds = TripDataset(r'.\data\T01-Sample'); print(ds.summary()); print('frames =', len(ds))"
```

Nếu dataset đặt nơi khác, thay chuỗi path bằng path thật. Kết quả hợp lệ phải in được summary và số frame. Lỗi `Trip directory not found` nghĩa là path đang trỏ sai cấp thư mục; phải trỏ tới thư mục trip, không phải file `.json.gz`.

### Bước 5 — dùng notebook

```powershell
jupyter notebook team_kit\explore_trip.ipynb
```

Chạy cell từ đầu xuống. Sửa `TRIP_DIR` nếu dataset không ở `data/T01-Sample`. Không dùng các trip `T0Xd` để kỳ vọng biểu đồ ground truth đầy đủ.

## 8. Thiết lập trên Google Colab (phương án thay thế)

1. Nén nguyên thư mục `team_kit/` thành `team_kit.zip`; nén từng trip cần dùng, ví dụ `T01-Sample.zip`.
2. Upload các zip lên Google Drive.
3. Tạo notebook Colab, mở `explore_trip.ipynb` hoặc notebook riêng.
4. Trong Cell 0 của notebook có sẵn, chỉnh `TEAM_KIT_ZIP` và `TRIP_ZIPS` theo path Drive, rồi chạy cell để mount Drive, giải nén đúng cấu trúc và cài `opencv-python-headless`.
5. Cell setup cần thấy `/content/project/team_kit/dataset_loader.py` và thường dùng trip tại `/content/project/data/T01-Sample`.

Không “flatten” nội dung của `team_kit.zip`: phải giữ nguyên thư mục con `team_kit/`, nếu không `from team_kit.dataset_loader import TripDataset` sẽ lỗi. Trên Colab, `opencv-python-headless` phù hợp hơn bản OpenCV có giao diện.

## 9. Quy trình phát triển và kiểm thử đề xuất

1. Đặt một trip `T01-Sample`, chạy smoke test và notebook.
2. Lặp với cả 6 trip Sample để tránh overfit vào một kịch bản/người lái.
3. Viết pipeline inference tạo đúng một dòng/ID frame; giữ thứ tự thời gian để tận dụng 20 FPS.
4. Tự chấm trên Sample bằng `evaluation.py`; lưu JSON report để so sánh các phiên bản model.
5. Chỉ sau khi pipeline ổn định, chạy inference trên `T01d`–`T10d`. Không cố đọc GT từ các trip này.
6. Kiểm tra schema/row count/file name trước khi đóng gói nộp.

Hướng cải thiện được kit gợi ý: object detection để ROI bám vật thể gần nhất, multi-object tracking để làm mượt theo thời gian, depth đơn mắt làm tín hiệu dự phòng, CNN/ViT cho ảnh cabin, và mô hình temporal LSTM/Transformer. Cần giữ inference deterministic; không bật augmentation ngẫu nhiên lúc dự đoán.

## 10. Chuẩn nộp bài

### 10.1. Vị trí và tên file

Mỗi trip chấm điểm có một CSV:

```text
predictions/<ten_team>/T01d.csv
predictions/<ten_team>/T02d.csv
...
predictions/<ten_team>/T10d.csv
```

Mỗi `T0Xd.csv` phải có **1.800 dòng dữ liệu**, ứng với frame `0` đến `1799`. Không nộp CSV Sample trừ khi ban tổ chức yêu cầu riêng; Sample dùng để tự kiểm tra.

### 10.2. Schema CSV

Nếu làm đủ ba challenge, dùng đúng header sau:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
0,0.000,inf,alert,5.0
1,0.050,inf,alert,5.0
2,0.100,3.275,drowsy,42.0
```

| Cột | Bắt buộc khi | Quy tắc |
|---|---|---|
| `frame_id` | Mọi file | Integer, đủ mọi ID và không trùng. |
| `timestamp` | Theo format công bố | Giây; đồng bộ frame tương ứng. Evaluator local hiện không dùng cột này, nhưng không được bỏ nếu format nộp yêu cầu. |
| `predicted_ttc` | Challenge 1 | Giây; ghi `inf` khi không có nguy cơ/vật cản. Không để ô trống. |
| `predicted_driver_state` | Challenge 2 | Một trong 5 nhãn hợp lệ, ưu tiên viết thường chính xác. |
| `predicted_risk_score` | Challenge 3 | Số thực 0–100. |

Nếu chỉ làm một challenge, README hướng dẫn bỏ hẳn cột challenge không làm thay vì điền rỗng/điền bừa. Tuy nhiên, do evaluator local luôn tính Challenge 1 và coi TTC thiếu là `inf`, cần xác nhận với ban tổ chức cách họ tách hạng mục nếu đội chỉ nộp Challenge 2 hoặc 3. An toàn nhất là tuân thủ format/challenge đã đăng ký với ban tổ chức.

### 10.3. Checklist kỹ thuật trước khi nộp

- [ ] Đã chạy `evaluation.py` trên ít nhất một trip Sample và nhận report hợp lý.
- [ ] Có đúng 10 file `T01d.csv`–`T10d.csv` nếu nộp toàn bộ tập chấm điểm.
- [ ] Mỗi file có 1.800 data row, `frame_id` duy nhất 0–1799; không thiếu/đảo frame.
- [ ] `timestamp` khớp trip, TTC tính bằng giây, `inf` viết đúng chữ khi cần.
- [ ] Nhãn driver chỉ thuộc 5 lớp được phép.
- [ ] Risk score nằm trong 0–100.
- [ ] Đã bỏ `ground_truth_ttc` và mọi cột nhãn thật khỏi file nộp.
- [ ] Tên CSV khớp ID trip, không phải tên model hay tên tự do.
- [ ] Lưu một bản report/commit/model version để tái lập kết quả khi cần.

### 10.4. Phần chưa có trong starter kit

Starter kit chỉ xác định dữ liệu và format CSV. Nó **không** nêu link/portal upload, hạn nộp, người nhận, có cần zip cả source code hay không, giới hạn dung lượng, tiêu chí xếp hạng giữa các challenge, hoặc mẫu báo cáo trình bày. Không nên tự suy đoán các điều này. Cần hỏi kênh Slack/README chính của hackathon để xác nhận trước khi gửi.

## 11. Các lỗi hay gặp và cách xử lý

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `python` không nhận diện | Chưa cài Python hoặc terminal cũ | Cài Python, mở terminal mới; dùng `py --version`. |
| `No installed Pythons found` | Chỉ có Windows launcher | Cài một bản Python rồi tạo lại `.venv`. |
| `ModuleNotFoundError: team_kit` | Chạy ngoài project root | `cd` về thư mục chứa `team_kit/`, hoặc thêm project root vào `sys.path`. |
| `Trip directory not found` | Path sai cấp/thư mục chưa giải nén | Trỏ đúng vào `.../T01-Sample`, không trỏ file JSON. |
| Không thấy ảnh ở frame | Download/giải nén thiếu hoặc file hỏng | Kiểm tra cấu trúc `kitti/image_2`, `image_3`, `driver`; tải lại trip nếu thiếu. |
| Sample có GT nhưng `T0Xd` toàn `unknown`/`inf`/`0` | Chính sách redaction | Đúng thiết kế; dùng Sample để debug, dùng `T0Xd` để inference/nộp. |
| `StereoSGBM_create` báo invalid keyword | Đổi tham số OpenCV sang snake_case | Giữ tên camelCase gốc của OpenCV. |
| Sửa `ground_truth_ttc` mà điểm không đổi | Cột đó bị bỏ qua | Chỉ cải thiện `predicted_ttc`; GT được đọc từ dataset tin cậy. |

## 12. Nhận định cuối và việc nên làm ngay

Starter kit đã đủ để bắt đầu nghiên cứu và phát triển, nhưng chưa thể chạy trên máy hiện tại do thiếu Python và dataset. Trình tự hành động ưu tiên là:

1. cài Python, tạo `.venv` và cài `requirements.txt`;
2. nhận/giải nén ít nhất `T01-Sample`;
3. chạy smoke test + notebook;
4. chạy baseline và evaluator để có mốc; rồi mới xây model;
5. xác minh portal, hạn nộp và yêu cầu đóng gói trực tiếp với ban tổ chức.

Điểm chiến lược: tối ưu TTC ở vùng `< 3 s`, đặc biệt ngưỡng danger `< 2 s`; không dùng dữ liệu bị ẩn như đáp án; và kiểm tra nghiêm format CSV trước khi nộp.

## 13. Các điểm cần hỏi lại ban tổ chức / mâu thuẫn tài liệu

Khi thực hiện, ưu tiên mã nguồn và `README.md` ở project root hơn mô tả rải rác trong notebook/hướng dẫn. Các điểm cần làm rõ là:

| Điểm | Quan sát | Cách xử lý an toàn |
|---|---|---|
| Behavior flags trên `T0Xd` | README liệt kê `frames[].behavior_flags` là bị ẩn; một số đoạn trong hướng dẫn/notebook lại mô tả flags vẫn có. Loader sẽ trả `False` khi field vắng. | Không phụ thuộc flags để tính Challenge 3; tái tính từ telemetry bằng đúng ngưỡng của evaluator. Hỏi ban tổ chức nếu model cần dùng flag này. |
| Near miss Challenge 3 | Có mô tả dùng TTC thật, nhưng code thực tế đếm `predicted_ttc < 1.5 s`. | Theo `evaluation.py`: TTC dự đoán là nguồn near-miss cho điểm local. |
| Cài đặt dependency | Một câu chú thích README nhắc `pyyaml`, nhưng `requirements.txt` chỉ có OpenCV, NumPy, pandas, matplotlib, Jupyter và code không import YAML. | Cài đúng `requirements.txt`; chỉ thêm package khi model riêng cần. |
| Làm riêng Challenge 2/3 | Tài liệu nói có thể bỏ cột challenge không làm; evaluator local vẫn tạo điểm Challenge 1 và TTC thiếu thành `inf`. | Xác nhận cơ chế xếp hạng/hạng mục nộp với ban tổ chức trước khi chỉ nộp C2/C3. |
| Cổng nộp và deliverables | Không có trong kit. | Xác nhận deadline, đường upload, có phải zip source/model/report hay không, và dung lượng tối đa. |

Những câu hỏi này không ngăn việc setup, khám phá Sample, huấn luyện hay xuất CSV; chúng chỉ cần được chốt trước thời điểm nộp chính thức.
