# FPTU DMS Vision — Script thao tác demo end-to-end C2

> Mục tiêu: cả nhóm nhìn vào file này là biết mở gì, chạy gì, nói gì trong demo BTC.  
> Thời lượng mục tiêu: 7–10 phút.  
> Không show API key/secret trên màn hình.

---

## 0. Storyline demo

Thông điệp chính:

> Hệ thống không chỉ phát hiện một sự kiện. Hệ thống hợp nhất trạng thái tài xế, nguy cơ trên đường và telemetry để tạo risk intelligence, rồi đưa cảnh báo đến cả Fleet Manager và Driver HMI.

Luồng sẽ show:

```text
AI Challenge 1 — TTC
AI Challenge 2 — Driver State
AI Challenge 3 — Risk Fusion
    ↓
Backend / Replay / API
    ↓
Fleet Dashboard
    ↓
CarSky KUKSA Signals
    ↓
Android HMI + simulated ECU reaction
```

---

## 1. Người phụ trách khi demo

| Vai trò | Người đề xuất | Nhiệm vụ |
|---|---|---|
| Presenter chính | Nhân hoặc thành viên thuyết trình tốt nhất | Kể storyline, chuyển cảnh demo |
| AI operator | AI member | Chạy AI trip demo, show TTC/driver/risk |
| Backend/CarSky operator | Nhân | Chạy Backend, gửi CarSky signal, kiểm tra HMI |
| Frontend operator | Thiện | Mở Fleet Dashboard, show alert/risk UI |
| Backup operator | 1 thành viên còn lại | Chuẩn bị video/screenshot nếu live lỗi |

---

## 2. Checklist trước khi demo

Làm trước giờ demo ít nhất 30–60 phút.

### 2.1 Repo đúng branch

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
git status --short
```

Không cần clean hoàn toàn, nhưng phải biết file nào đang thay đổi.

### 2.2 Không show secret

Không mở trực tiếp:

```text
SE/BE/.env
```

Nếu cần show config, chỉ show `.env.example` hoặc che API key.

### 2.3 CarSky deployment

Vào CarSky:

```text
https://hackathon-1.carsky.io/
```

Mở device/deployment đang chạy được.

Mục tiêu thấy:

```text
Running 3/3
```

Node nên có:

- DMS Signal Broker.
- DMS HMI Bridge.
- DMS Android HMI.

Widget nên mở sẵn:

- Android Screen.
- Signal Watch.
- ADB nếu cần.

### 2.4 HMI APK

Android Screen phải thấy app DMS HMI.

State ban đầu có thể là:

```text
LÁI XE AN TOÀN
```

hoặc state gần nhất từ CarSky signal.

### 2.5 Backend venv

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate
```

Test nhanh:

```bash
python -m pytest tests/test_health.py -q
```

Nếu sát giờ không muốn chạy test, chỉ chạy Backend.

### 2.6 Frontend deps

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
npm install
```

Nếu đã có `node_modules` rồi thì bỏ qua.

---

## 3. Mở các cửa sổ cần thiết

Nên mở 5 cửa sổ/tab:

### Window A — Terminal AI

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
```

### Window B — Terminal Backend

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate
```

### Window C — Terminal Frontend

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
```

### Window D — Browser Fleet Dashboard

Chuẩn bị URL frontend local, thường là:

```text
http://localhost:5173
```

### Window E — Browser CarSky

Mở:

```text
https://hackathon-1.carsky.io/
```

Chuẩn bị:

- Android Screen widget.
- Signal Watch widget.
- Deployment dashboard nếu cần chứng minh Running 3/3.

---

## 3A. Hướng dẫn triển khai từng stage trước khi demo

Phần này dành cho team chuẩn bị trước khi lên demo. Làm theo thứ tự này để tránh cảnh “mỗi người chạy một kiểu rồi sân khấu biến thành lễ hội bug” — vui thì vui nhưng không nên.

Mục tiêu cuối:

```text
AI Challenge 1/2/3 chạy được
→ có output CSV/JSON
→ Backend chạy được
→ Fleet Dashboard mở được
→ CarSky Running 3/3
→ Signal Watch nhận signal
→ Android HMI đổi trạng thái theo SAFE/WARNING/CRITICAL
```

### 3A.1 Triển khai AI Challenge 1 — TTC / Road Risk

Mục tiêu:

- Đọc dữ liệu road camera / stereo / depth nếu có.
- Tạo `predicted_ttc`.
- Có bằng chứng visual hoặc CSV để show BTC.

Folder cần kiểm tra:

```text
AI/core/challenge1_road/
AI/configs/challenge1.yaml
AI/scripts/trip_visual_demo.py
AI/scripts/eval_practice.py
AI/demo_trips/T_test_01/
```

File logic chính:

```text
AI/core/challenge1_road/predict_ttc.py
AI/core/challenge1_road/ttc_engine.py
AI/core/challenge1_road/depth.py
AI/core/challenge1_road/detection.py
```

Chạy kiểm tra nhanh:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py --trip-dir demo_trips/T_test_01
```

Nếu cần sinh CSV để nộp/demo:

```bash
python scripts/trip_visual_demo.py \
  --trip-dir demo_trips/T_test_01 \
  --output-csv artifacts/T_test_01.csv
```

Nếu cần lấy KPI Challenge 1:

```bash
python scripts/eval_practice.py
```

Nếu lệnh trên cần tham số dataset/submission mà chưa biết, mở help trước:

```bash
python scripts/eval_practice.py --help
```

Output mong đợi:

```text
predicted_ttc
```

Trong CSV tổng hợp phải có:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Khi trình bày:

> Challenge 1 không chỉ detect object. Nó ước lượng khoảng cách/thời gian va chạm TTC, có xử lý trường hợp mất detection ngắn, looming TTC và confirmation để giảm false alarm.

Checklist pass:

- Demo visual mở được.
- Có TTC thay đổi theo frame.
- Không biến `Infinity` thành `0`.
- Có CSV hoặc log chứng minh output.
- Có số KPI hoặc ít nhất có lệnh/ảnh log chuẩn bị để bổ sung.

### 3A.2 Triển khai AI Challenge 2 — Driver State

Mục tiêu:

- Đọc face/driver input.
- Tạo `predicted_driver_state`.
- State hợp lệ: `alert`, `drowsy`, `yawning`, `distracted`, `microsleep`.

Folder cần kiểm tra:

```text
AI/core/challenge2_driver/
AI/configs/challenge2.yaml
AI/models/driver_state_rf_v2.joblib
AI/scripts/webcam_driver_demo.py
AI/scripts/trip_visual_demo.py
```

File logic chính:

```text
AI/core/challenge2_driver/predict_state.py
AI/core/challenge2_driver/dms_core.py
AI/core/challenge2_driver/ml_features.py
AI/core/challenge2_driver/driver_profile.py
```

Chạy chung trong trip demo:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py --trip-dir demo_trips/T_test_01
```

Nếu cần demo webcam/driver riêng, thử:

```bash
python scripts/webcam_driver_demo.py --help
```

Sau đó chạy đúng tham số mà script yêu cầu.

Output mong đợi:

```text
predicted_driver_state
alertness_score
eye_state
head_pose
mouth_state
```

Khi trình bày:

> Challenge 2 tập trung vào trạng thái tài xế. Model hiện dùng feature từ mắt, đầu, miệng và safety fusion để ưu tiên các trạng thái nguy hiểm như distracted, drowsy, microsleep.

Checklist pass:

- Có state hiển thị trong visual demo.
- State nằm trong enum hợp lệ.
- Có model artifact `driver_state_rf_v2.joblib`.
- Có thể giải thích vì sao state nguy hiểm làm risk tăng.
- Cần bổ sung KPI accuracy/F1 khi team AI có log validation.

### 3A.3 Triển khai AI Challenge 3 — Risk Fusion

Mục tiêu:

- Nhận TTC từ Challenge 1.
- Nhận driver state từ Challenge 2.
- Kết hợp telemetry/context để tạo `predicted_risk_score`.

Folder cần kiểm tra:

```text
AI/core/challenge3_fusion/
AI/scripts/trip_visual_demo.py
```

File logic chính:

```text
AI/core/challenge3_fusion/risk_engine.py
```

Chạy chung:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py \
  --trip-dir demo_trips/T_test_01 \
  --output-csv artifacts/T_test_01.csv
```

Kiểm tra CSV:

```bash
python - <<'PY'
from pathlib import Path
p = Path("artifacts/T_test_01.csv")
print(p.read_text(encoding="utf-8").splitlines()[:8])
PY
```

Output mong đợi:

```text
predicted_risk_score: 0..100
```

Mapping demo gợi ý:

| Risk | Severity | HMI |
|---:|---|---|
| 0–30 | SAFE | LÁI XE AN TOÀN |
| 31–70 | WARNING | CẢNH BÁO / TẬP TRUNG |
| 71–100 | CRITICAL | NGUY HIỂM / BRAKE_SAFE |

Khi trình bày:

> Challenge 3 là lớp biến prediction thành decision. TTC thấp và driver state nguy hiểm sẽ làm risk tăng, từ đó sinh severity/action cho dashboard và HMI.

Checklist pass:

- Risk không âm, không vượt 100.
- Risk tăng khi TTC thấp hoặc driver state nguy hiểm.
- CSV đủ 3 cột submission chính.
- Có thể map risk sang CarSky signal.

### 3A.4 Chuẩn hóa output AI để đưa sang Backend/Fleet/CarSky

Output chuẩn để demo:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Output nội bộ mở rộng có thể có:

```json
{
  "trip_id": "T01d",
  "frame_id": 0,
  "timestamp": 0.0,
  "ego": {
    "speed_kmh": 80
  },
  "driver": {
    "state": "distracted",
    "alertness_score": 0.45
  },
  "min_ttc": "Infinity",
  "risk": {
    "final_risk_score": 55
  }
}
```

Quy tắc quan trọng:

- `Infinity` ở JSON boundary nên ghi là chuỗi `"Infinity"`.
- Không đổi `Infinity` thành `0`.
- Không tự đổi tên field sau khi Backend/HMI đã dùng.
- Nếu AI thêm field mới thì Backend nên giữ extra fields nếu không ảnh hưởng contract.
- Nếu AI thiếu field bắt buộc thì demo phải fallback bằng mock signal đã chuẩn bị.

### 3A.5 Triển khai Backend

Mục tiêu:

- Backend chạy được local.
- Có health/docs.
- Có vai trò replay/distribute/publish signal.

Folder cần kiểm tra:

```text
SE/BE/
SE/BE/app/
SE/BE/requirements.txt
SE/BE/scripts/carsky_phase05.py
```

Cài dependency nếu máy mới:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Chạy Backend:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Kiểm tra:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

Expected `/health`:

```json
{
  "status": "ok",
  "service": "dms-backend",
  "stream_fps": 20
}
```

Lưu ý:

- `/ready` có thể `503` nếu dataset/cache chưa đủ; đây không phải lỗi chết app.
- Không thêm auth/security vào demo này.
- Không show `.env` trên màn hình.
- Nếu script CarSky bị lỗi do merge conflict, fix script trước khi demo.

Checklist pass:

- `uvicorn` chạy không crash.
- `/health` trả `200`.
- `/docs` mở được.
- Không có nút Authorize/security scheme bắt buộc.

### 3A.6 Triển khai Fleet Dashboard

Mục tiêu:

- Mở được UI Fleet Dashboard.
- Show được góc nhìn quản lý đội xe: risk, alert, trip/driver.
- Chuẩn bị vị trí/flow cho **Fleet AI Copilot**: chatbot để fleet manager hỏi nhanh về tình trạng đội xe.

Folder cần kiểm tra:

```text
SE/FE/
SE/FE/package.json
```

Cài dependency nếu máy mới:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
npm install
```

Chạy:

```bash
npm run dev
```

Mở:

```text
http://localhost:5173
```

Những phần cần show nếu có:

- Fleet overview.
- Xe/chuyến đi đang risk cao.
- Risk score.
- Alert log.
- Driver behavior/coaching.
- Replay/live panel nếu đã nối Backend.
- Fleet AI Copilot nếu đã có UI hoặc prototype.

Fleet AI Copilot — feature cam kết làm:

| Mục | Nội dung |
|---|---|
| Mục tiêu | Cho fleet manager hỏi bằng ngôn ngữ tự nhiên thay vì tự đọc toàn bộ alert |
| Input | Trip/risk/driver state/alert log/telemetry summary |
| Output | Tóm tắt tình hình, lý do risk tăng, xe cần ưu tiên, hành động đề xuất |
| Phiên bản C2/Code Freeze | Có thể bắt đầu bằng rule-based hoặc RAG nhẹ; nếu ổn sẽ nối LLM API |
| Không nên nói quá | Không nói Copilot đã thay thế điều phối viên hoặc đã production-ready nếu chưa có demo live |

Câu hỏi mẫu cho Copilot:

```text
Xe nào đang nguy hiểm nhất?
Tại sao xe T01d bị cảnh báo?
Tài xế nào đang mất tập trung?
Có xe nào cần BRAKE_SAFE không?
Tóm tắt chuyến T01d trong 3 dòng.
Đề xuất hành động cho fleet manager lúc này.
```

Response mẫu mong muốn:

```text
Xe T01d đang có mức rủi ro cao nhất.
Nguyên nhân chính: tài xế mất tập trung, TTC giảm còn 1.2s và risk score đạt 88.
Khuyến nghị: phát cảnh báo BRAKE_SAFE trên HMI và đánh dấu chuyến này cần review sau demo.
```

Nếu FE chưa nối full realtime, nói đúng:

> Fleet Dashboard hiện là MVP UI/prototype đang polish integration. Core output từ AI và signal layer đã chạy; dashboard là lớp quản trị để hiển thị cùng risk intelligence cho fleet manager.

Nếu Fleet AI Copilot chưa hoàn tất ở thời điểm demo C2, nói đúng:

> Fleet AI Copilot là feature nhóm cam kết hoàn thiện trước Code Freeze. Tại C2, nhóm đã xác định input/output, câu hỏi mẫu và vị trí trong Fleet Dashboard. Copilot sẽ đọc risk/alert/trip summary để giúp fleet manager hỏi nhanh nguyên nhân và hành động đề xuất.

Checklist pass:

- Trang mở được.
- Không crash trắng màn hình.
- Có ít nhất một màn hình thể hiện fleet/risk/alert.
- Có đường lui bằng screenshot nếu live lỗi.

### 3A.7 Triển khai CarSky/KUKSA

Mục tiêu:

- Deployment CarSky chạy `Running 3/3`.
- Signal Watch thấy VSS/KUKSA signal.
- Có thể gửi `send-safe`, `send-warning`, `send-critical`.

Thành phần đúng:

```text
DMS Signal Broker
DMS HMI Bridge
DMS Android HMI
```

VSS artifact quan trọng:

```text
SE/BE/carsky/dms-vss-signals.json
```

Quy tắc sống còn:

- File VSS phải là object/map `{ ... }`, không phải array `[ ... ]`.
- Nếu VSS là array, KUKSA Broker có thể crash với lỗi kiểu `invalid type: sequence, expected a map`.
- Khi deployment đang `Running 3/3`, không redeploy lung tung sát giờ demo.

Kiểm tra JSON local:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
SE/BE/.venv/bin/python -m json.tool SE/BE/carsky/dms-vss-signals.json >/tmp/dms-vss-signals.validated.json
sed -n '1,20p' SE/BE/carsky/dms-vss-signals.json
```

Đầu file phải giống dạng:

```json
{
  "Vehicle": {
    "type": "branch",
    "children": {}
  }
}
```

Trong CarSky UI:

1. Vào `https://hackathon-1.carsky.io/`.
2. Bên trái chọn `Nydus`.
3. Chọn blueprint/deployment đang chạy.
4. Kiểm tra deployment có `Running 3/3`.
5. Bên trái chọn `Devices`.
6. Chọn device đang dùng, ví dụ `test`.
7. Bấm dấu `+` trong phần Widgets.
8. Thêm:
   - `Screen` → chọn Android screen.
   - `Signal Watch` → chọn signal broker.
   - `Log` nếu cần xem broker/HMI logs.
   - `ADB` nếu cần cài APK.

Gửi signal:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
python scripts/carsky_phase05.py send-critical
```

Expected:

```json
{
  "ok": true,
  "sent": 14
}
```

Signal Watch cần thấy các signal như:

```text
Vehicle.Speed
Vehicle.SpeedLimit
Vehicle.Driver.State
Vehicle.Driver.AlertnessScore
Vehicle.ADAS.MinTTC
Vehicle.ADAS.FinalRiskScore
Vehicle.ADAS.DisplaySeverity
Vehicle.ADAS.CriticalAlert
Vehicle.ADAS.RecommendedActionCode
Vehicle.ADAS.AIStatus
```

Checklist pass:

- Deployment `Running 3/3`.
- Signal Watch có khoảng 19 signal.
- `send-critical` trả `"ok": true`.
- Signal Watch đổi giá trị.
- HMI đổi màu/trạng thái.

### 3A.8 Triển khai Android HMI APK

Mục tiêu:

- Cài được APK lên Android VM trong CarSky.
- HMI đọc được signal và đổi UI.

Folder cần kiểm tra:

```text
SE/HMI/demo-live/
SE/HMI/demo-live/build_demo_apk.sh
SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

Build APK local:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/HMI/demo-live
./build_demo_apk.sh
```

APK expected:

```text
SE/HMI/demo-live/build/dist/dms-hmi-live-debug.apk
```

Cài qua CarSky ADB widget:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON
pbcopy < SE/HMI/install_hmi_live_via_carsky_adb_widget.sh
```

Sau đó:

1. Mở CarSky device.
2. Mở widget `DMS Android ADB`.
3. Click vào vùng ADB shell.
4. Dán bằng `Cmd + V`.
5. Enter nếu script chưa tự chạy.

Kiểm tra package:

```bash
dumpsys package vn.fpt.dms.hmi | grep -iE "Activity|MainActivity|permission"
ps -A | grep vn.fpt.dms.hmi
```

Start lại app nếu cần:

```bash
am force-stop vn.fpt.dms.hmi
am start -n vn.fpt.dms.hmi/.MainActivity
```

Nếu cài APK báo lỗi `INSTALL_FAILED_VERSION_DOWNGRADE`:

```bash
pm install -r -d -t /data/local/tmp/dms_hmi_live.apk
```

Nếu báo `INSTALL_FAILED_DEPRECATED_SDK_VERSION`:

- APK build sai/manifest lỗi hoặc version artifact không đúng.
- Build lại từ `SE/HMI/demo-live/build_demo_apk.sh`.
- Không dùng tool convert web-to-APK lạ nếu chưa verify trên CarSky.

Checklist pass:

- Android Screen thấy app DMS.
- SAFE/WARNING/CRITICAL đổi theo signal.
- Signal Watch và HMI khớp nhau.
- Nếu voice không nghe, vẫn xem là pass visual vì Android VM có thể thiếu TTS engine.

### 3A.9 Thứ tự triển khai chuẩn trước ngày demo

Làm theo thứ tự này:

| Thứ tự | Việc | Ai phụ trách | Pass khi |
|---:|---|---|---|
| 1 | AI Challenge 1 chạy TTC | AI member | Có TTC/CSV/KPI log |
| 2 | AI Challenge 2 chạy driver state | AI member | Có state hợp lệ/accuracy log |
| 3 | AI Challenge 3 chạy risk fusion | AI member | Có risk 0..100 |
| 4 | Sinh CSV tổng hợp | AI member | CSV đủ 3 cột BTC |
| 5 | Backend chạy `/health` | Nhân/BE | `/health` 200 |
| 6 | Fleet Dashboard chạy | FE member | UI mở được |
| 7 | CarSky Running 3/3 | Nhân/CarSky | Broker/Bridge/HMI ready |
| 8 | Signal Watch nhận data | Nhân/CarSky | thấy signal đổi |
| 9 | HMI đổi visual | Nhân/HMI | SAFE/WARNING/CRITICAL |
| 10 | Rehearsal 10 phút | cả nhóm | không quá thời gian |

Nếu thiếu một stage, ưu tiên demo vẫn phải giữ mạch:

```text
AI output → risk decision → CarSky signal → HMI
```

Fleet Dashboard có thể nói là MVP nếu chưa nối realtime hoàn chỉnh, nhưng không được nói quá là production-ready.

---

## 4. Demo Step 1 — Mở bài toán và kiến trúc

Người nói:

> Bài toán nhóm em chọn là DMS-10 Driver Intelligence Platform. Insight của nhóm là tai nạn không bắt đầu từ một tín hiệu đơn lẻ, mà từ nhiều tín hiệu nguy hiểm bị nhìn riêng lẻ. Vì vậy hệ thống của nhóm hợp nhất road risk, driver state và telemetry thành một unified risk score.

Show nhanh diagram bằng lời:

```text
Road Camera → TTC
Driver Camera → Driver State
Telemetry → Vehicle Context
All → Risk Fusion → Dashboard/HMI
```

Không quá 45 giây.

---

## 5. Demo Step 2 — AI Challenge 1/2/3 trên demo trip

Mục tiêu: show AI core đang chạy từ input camera/telemetry ra output TTC, driver state, risk.

### 5.1 Chạy demo visual trip

Trong Window A:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py --trip-dir demo_trips/T_test_01
```

Nếu muốn xuất video/CSV:

```bash
python scripts/trip_visual_demo.py \
  --trip-dir demo_trips/T_test_01 \
  --output-video artifacts/T_test_01-demo.mp4 \
  --output-csv artifacts/T_test_01.csv
```

### 5.2 Nói khi màn hình AI hiện lên

Người nói:

> Đây là demo trip ba camera. Góc road-left và road-right phục vụ Challenge 1 để ước lượng TTC. Góc face camera phục vụ Challenge 2 để dự đoán trạng thái tài xế. Panel fusion bên dưới hợp nhất TTC, driver state và telemetry để tạo risk score cho Challenge 3.

Show các phần:

- Road-left: TTC/object/depth.
- Road-right: stereo reference.
- Face camera: driver state.
- Fusion dashboard: risk.

### 5.3 Điểm cần nhấn

Nói:

> Các output này cũng là format submission chính: `predicted_ttc`, `predicted_driver_state`, `predicted_risk_score`. Demo UI không tạo prediction riêng, chỉ visualize output từ core AI.

Nếu có người hỏi Challenge 1:

> Challenge 1 TTC đã được cải thiện thêm bằng depth keyframe nếu có, looming TTC, hold gap khi mất detection và danger confirmation để giảm false alarm.

Nếu có người hỏi Challenge 2:

> Challenge 2 dùng feature từ face/eye/mouth/head pose, Random Forest v2 và safety fusion để xử lý microsleep khi có bằng chứng mắt nhắm liên tục.

Nếu có người hỏi Challenge 3:

> Challenge 3 hiện dùng risk fusion deterministic để dễ giải thích: TTC gần làm risk tăng, driver state nguy hiểm như distracted/microsleep cũng làm risk tăng.

---

## 6. Demo Step 3 — Sinh CSV output chuẩn BTC

Mục tiêu: chứng minh không chỉ có demo visual mà còn có output nộp bài.

Trong Window A:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py \
  --trip-dir demo_trips/T_test_01 \
  --output-csv artifacts/T_test_01.csv
```

Show file CSV:

```bash
python - <<'PY'
from pathlib import Path
p = Path("artifacts/T_test_01.csv")
print(p)
print(p.read_text(encoding="utf-8").splitlines()[:6])
PY
```

Expected columns:

```csv
frame_id,timestamp,predicted_ttc,predicted_driver_state,predicted_risk_score
```

Người nói:

> Đây là contract output cuối cùng. Ba challenge không tách rời trên demo, mà được ghép thành cùng một frame-level CSV.

---

## 7. Demo Step 4 — Chạy Backend

Mục tiêu: show Backend là lớp phân phối dữ liệu cho dashboard/replay/CarSky.

Trong Window B:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mở browser:

```text
http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok",
  "service": "dms-backend",
  "version": "...",
  "stream_fps": 20
}
```

Mở Swagger nếu cần:

```text
http://localhost:8000/docs
```

Người nói:

> Backend giữ vai trò validate, cache, replay 20 FPS, và publish signal sang CarSky. API demo không dùng authentication vì đây là môi trường hackathon/trusted demo, còn credential CarSky chỉ dùng outbound.

Lưu ý:

- `/ready` có thể 503 nếu dataset/cache chưa đủ 10 trip. Không dùng `/ready` làm proof chính nếu chưa nạp đủ dataset.

---

## 8. Demo Step 5 — Chạy Fleet Dashboard

Mục tiêu: show góc nhìn Fleet Manager/HQ.

Trong Window C:

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
npm run dev
```

Mở:

```text
http://localhost:5173
```

Nếu frontend không chạy do dependency:

```bash
npm install
npm run dev
```

Người nói:

> Đây là góc nhìn Fleet Manager. Proposal của nhóm không chỉ cảnh báo trên xe, mà còn giúp quản lý biết xe nào đang cần ưu tiên, vì sao risk tăng và hành động nào nên được đưa ra.

Những thứ cần show:

- Fleet overview.
- Risk score/card.
- Alert/event log.
- Trip/replay nếu có.
- Driver behavior/coaching nếu đã nối.
- Fleet AI Copilot nếu đã có bản prototype.

Nếu có Copilot prototype, hỏi thử 1–2 câu:

```text
Xe nào đang nguy hiểm nhất?
Vì sao risk của T01d tăng?
Đề xuất hành động cho tài xế hiện tại.
```

Người nói:

> Fleet AI Copilot là lớp trợ lý cho fleet manager. Thay vì đọc từng event thủ công, người quản lý có thể hỏi trực tiếp vì sao risk tăng và xe nào cần ưu tiên. Feature này nhóm cam kết hoàn thiện từ C2 đến Code Freeze.

Nếu Dashboard chưa nối full realtime:

> Phần dashboard hiện là MVP/prototype đang hoàn thiện integration. Cốt lõi dữ liệu frame-level và risk signal đã có; phần UI đang được polish để trình bày tốt hơn.

---

## 9. Demo Step 6 — CarSky/KUKSA/HMI

Mục tiêu: show connected-car proof, không chỉ web dashboard.

### 9.1 Mở CarSky

Trong browser Window E:

1. Vào `https://hackathon-1.carsky.io/`.
2. Chọn device đang chạy được, ví dụ `test` hoặc device team đang dùng.
3. Mở Android Screen widget.
4. Mở Signal Watch widget.
5. Mở deployment nếu cần show `Running 3/3`.

Show:

```text
DMS Signal Broker
DMS HMI Bridge
DMS Android HMI
Running 3/3
```

Người nói:

> Đây là môi trường CarSky/KUKSA. Backend không cần nói trực tiếp với APK. Backend ghi signal lên CarSky, HMI đọc signal từ CarSky và đổi giao diện.

### 9.2 Gửi signal SAFE

Trong Window B, mở terminal mới nếu Backend đang chiếm terminal.

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
python scripts/carsky_phase05.py send-safe
```

Expected:

```json
{
  "ok": true,
  "sent": 14
}
```

Show HMI:

```text
LÁI XE AN TOÀN
TIẾP TỤC QUAN SÁT
```

### 9.3 Gửi signal WARNING

```bash
CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
python scripts/carsky_phase05.py send-warning
```

Show HMI:

```text
CẢNH BÁO
TẬP TRUNG PHÍA TRƯỚC
```

Show Signal Watch:

```text
Vehicle.Driver.State = distracted
Vehicle.ADAS.FinalRiskScore = 55
Vehicle.ADAS.DisplaySeverity = WARNING
Vehicle.ADAS.RecommendedActionCode = FOCUS_FORWARD
```

### 9.4 Gửi signal CRITICAL

```bash
CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
python scripts/carsky_phase05.py send-critical
```

Show HMI:

```text
NGUY HIỂM hoặc CẢNH BÁO
PHANH AN TOÀN / BRAKE_SAFE
ECU: BRAKE ASSIST REQUESTED • BUZZER ON • HAZARD ON
```

Show Signal Watch:

```text
Vehicle.Driver.State = microsleep
Vehicle.ADAS.MinTTC = 1.2
Vehicle.ADAS.FinalRiskScore = 88
Vehicle.ADAS.CriticalAlert = true
Vehicle.ADAS.DisplaySeverity = CRITICAL
Vehicle.ADAS.RecommendedActionCode = BRAKE_SAFE
Vehicle.ADAS.AIStatus = ONLINE
```

Người nói:

> Đây là bằng chứng end-to-end đến connected car layer. Cùng một risk intelligence được publish thành VSS/KUKSA signals, sau đó HMI trong xe đổi trạng thái cảnh báo. Dòng ECU hiện tại là simulated ECU reaction để thể hiện hành động an toàn theo context.

---

## 10. Demo Step 7 — Kết nối câu chuyện AI → Dashboard → HMI

Người nói:

> Với Fleet Manager, thông tin này xuất hiện dưới dạng risk score, alert log và trip analytics. Với Driver, thông tin này xuất hiện thành cảnh báo ngắn gọn trên HMI: cần làm gì ngay. Nhóm không gửi video thô liên tục, mà ưu tiên gửi signal/kết luận cấp dữ liệu.

Nhấn mạnh:

- AI core tạo prediction.
- Backend phân phối và publish.
- Dashboard dành cho HQ.
- HMI dành cho driver.
- CarSky/KUKSA chứng minh hướng connected car.

---

## 11. Câu nói kết thúc demo

> Tại C2, nhóm đã có pipeline AI ba challenge, Backend foundation, Fleet Dashboard MVP và CarSky HMI integration. Từ giờ đến Code Freeze, nhóm sẽ tập trung chốt KPI định lượng, chuẩn hóa full CSV submission, polish dashboard/HMI và giảm rủi ro demo live.

---

## 12. Backup plan nếu live demo lỗi

### 12.1 Nếu AI visual demo lỗi

Show:

- `AI/README.md`.
- `AI/demo_trips/T_test_01`.
- Screenshot/video đã record.
- CSV output sample nếu có.

Nói:

> Live window gặp lỗi môi trường local, nhưng core/runtime và output CSV đã được chuẩn bị. Đây là video/output backup từ cùng script.

### 12.2 Nếu Backend lỗi

Show:

- `http://localhost:8000/health` nếu còn chạy.
- Code architecture trong `app/main.py`.
- Dashboard static/prototype.

Nói:

> Backend foundation đã có health, routing và replay module. Phần demo có thể chuyển qua AI visual + CarSky signal direct để không mất mạch end-to-end.

### 12.3 Nếu Frontend lỗi

Show:

- Screenshot hoặc local file.
- Chuyển trọng tâm sang AI + CarSky/HMI.

Nói:

> Dashboard đang được polish, còn core risk output và HMI integration vẫn chạy được.

### 12.4 Nếu CarSky lỗi

Show:

- Screenshot Running 3/3 cũ.
- Signal Watch screenshot.
- HMI screenshot Safe/Warning/Critical.
- `CARSKY_BTC_SUPPORT_REPORT.md` nếu cần giải thích technical issue.

Nói:

> CarSky là môi trường cloud/runtime bên ngoài nên có thể phụ thuộc trạng thái deployment. Nhóm đã chứng minh được KUKSA signal và HMI update; nếu live cloud lỗi, nhóm dùng recorded evidence.

### 12.5 Nếu HMI không nghe voice

Nói:

> Android VM hiện chưa có TTS engine mặc định, nên visual alert là kênh chính. Voice button/logic đã có nhưng audio route phụ thuộc runtime HMI.

---

## 13. Câu hỏi BTC/mentor có thể hỏi

### Hỏi: Đây là mock hay thật?

Trả lời:

> AI demo trip dùng input camera/telemetry thật trong trip demo. CarSky signal hiện có thể dùng mock sender để kích hoạt state nhanh trong demo. Khi AI realtime/final pipeline đủ ổn, Backend sẽ thay mock sender bằng AI output realtime nhưng giữ nguyên signal contract.

### Hỏi: Vì sao không gửi ảnh thô lên dashboard?

Trả lời:

> Proposal của nhóm theo hướng data-level decision: xử lý local/core, chỉ gửi kết luận/signal như TTC, driver state, risk score. Điều này giảm bandwidth, tăng privacy và phù hợp fleet operation.

### Hỏi: Challenge 3 risk có giải thích được không?

Trả lời:

> Có. Risk hiện tại là deterministic fusion giữa TTC risk và driver-state risk. Ví dụ TTC thấp hoặc microsleep đều làm risk tăng, và dashboard/HMI có thể hiển thị reason/action.

### Hỏi: CarSky giao tiếp với Backend bằng gì?

Trả lời:

> Backend gọi CarSky Signals API để actuate/update VSS/KUKSA signal. HMI đọc lại values từ CarSky/KUKSA và render UI. Backend không cần CarSky gọi ngược vào máy local.

### Hỏi: Có ECU thật chưa?

Trả lời:

> Tại C2, nhóm đang có simulated ECU reaction trên HMI dựa trên VSS signals như `RecommendedActionCode`, `CriticalAlert`, `DisplaySeverity`. Đây là proof-of-concept cho cockpit reaction. Nếu cần proof mạnh hơn, bước tiếp theo là tách thêm VSS signals cho brake assist, buzzer, hazard và ECU script node riêng.

### Hỏi: KPI hiện tại là gì?

Trả lời:

> Challenge 1 đã có tuning mới và team AI đang chốt score log. Challenge 2 có model RF v2 và cần báo accuracy/F1 theo validation. C2 tập trung chứng minh end-to-end; trước Code Freeze nhóm sẽ chốt bảng KPI đầy đủ.

---

## 14. Lệnh nhanh dùng trong demo

### AI visual demo

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py --trip-dir demo_trips/T_test_01
```

### AI output CSV

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/AI
python scripts/trip_visual_demo.py \
  --trip-dir demo_trips/T_test_01 \
  --output-csv artifacts/T_test_01.csv
```

### Backend

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/FE
npm run dev
```

### CarSky critical signal

```bash
cd /Users/lilnhan/Documents/GitHub/Hackathon-Automotive-2026/HACKATHON/SE/BE
source .venv/bin/activate

CARSKY_ROOM_ID=wfhuue4wpc9jbvv4o7jbi \
CARSKY_NODE_KEY=dms-signal-broker \
CARSKY_TIMEOUT_SEC=30 \
python scripts/carsky_phase05.py send-critical
```

---

## 15. Những thứ tuyệt đối không làm khi đang demo

- Không mở `.env` chứa API key.
- Không deploy lại CarSky/VSS nếu bản đang Running.
- Không sửa APK/HMI sát giờ.
- Không chạy train model nặng.
- Không npm install nếu internet/máy đang không ổn, trừ khi bắt buộc.
- Không nói các phần roadmap như Pi/Hailo/MQTT/offline queue là đã hoàn thành nếu chưa có demo thật.

---

## 16. Thứ tự demo tối ưu trong 10 phút

| Thời gian | Nội dung |
|---:|---|
| 0:00–0:45 | Bài toán + insight |
| 0:45–2:45 | AI Challenge 1/2/3 visual demo |
| 2:45–3:30 | Show CSV output contract |
| 3:30–4:30 | Backend health/API/replay role |
| 4:30–5:45 | Fleet Dashboard |
| 5:45–8:15 | CarSky Signal Watch + Android HMI Safe/Warning/Critical |
| 8:15–9:15 | KPI/rủi ro/kế hoạch |
| 9:15–10:00 | Q&A buffer |
