import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

dotenv.config({ path: ".env.local" });
dotenv.config();

app.use(express.json());

type TripSummary = {
  trip_id: string;
  metadata?: {
    description?: string;
    driver_profile?: string;
    duration_sec?: number;
    fps?: number;
    speed_limit_kmh?: number;
  };
  driver_summary?: unknown;
  trip_aggregate?: unknown;
};

type ChatHistoryItem = { sender: string; text: string };

type CopilotReportType = "compare" | "maintenance" | "safety";

const BEDROCK_REGION = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || "ap-southeast-2";
const BEDROCK_MODEL_ID = process.env.BEDROCK_MODEL_ID || "deepseek.v3.2";

function cleanBearerToken(raw?: string): string {
  return (raw || "").replace(/\n/g, "").replace(/ /g, "").trim();
}

function getBedrockBearerToken(): string {
  return cleanBearerToken(process.env.AWS_BEARER_TOKEN_BEDROCK || process.env.BEDROCK_API_KEY);
}

async function callBedrockConverse(prompt: string, modelId = BEDROCK_MODEL_ID): Promise<string> {
  const token = getBedrockBearerToken();
  if (!token) throw new Error("AWS_BEARER_TOKEN_BEDROCK is not configured");

  const endpoint = `https://bedrock-runtime.${BEDROCK_REGION}.amazonaws.com/model/${encodeURIComponent(modelId)}/converse`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify({
      messages: [
        {
          role: "user",
          content: [{ text: prompt }],
        },
      ],
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.message || payload?.error || response.statusText;
    throw new Error(`Bedrock ${response.status}: ${message}`);
  }

  return payload?.output?.message?.content?.[0]?.text || "";
}

const availableTripIds = (vehicles: TripSummary[]) => vehicles.map((vehicle) => vehicle.trip_id).filter(Boolean);

const findMentionedTripIds = (message: string, vehicles: TripSummary[]) => {
  const lower = message.toLowerCase();
  return availableTripIds(vehicles).filter((tripId) => lower.includes(tripId.toLowerCase()));
};

const detectReportType = (message: string): { type: CopilotReportType; requestedCount: number } | null => {
  const lower = message.toLowerCase();
  const countMatch = lower.match(/(?:so sánh|compare)\s*(\d+)/);
  if (lower.includes("so sánh") || lower.includes("compare")) {
    return { type: "compare", requestedCount: Math.max(2, Number(countMatch?.[1] || 2) || 2) };
  }
  if (lower.includes("bảo trì") || lower.includes("maintenance")) {
    return { type: "maintenance", requestedCount: 3 };
  }
  if (lower.includes("báo cáo") || lower.includes("an toàn") || lower.includes("safety")) {
    return { type: "safety", requestedCount: 4 };
  }
  return null;
};

const buildTripContext = (vehicles: TripSummary[]) => JSON.stringify(
  vehicles.map((vehicle) => ({
    trip_id: vehicle.trip_id,
    metadata: vehicle.metadata,
    driver_summary: vehicle.driver_summary,
    trip_aggregate: vehicle.trip_aggregate,
  })),
  null,
  2,
);

// Initialize Gemini Client lazily or safely
let ai: GoogleGenAI | null = null;
function getGeminiClient(): GoogleGenAI | null {
  if (!ai && process.env.GEMINI_API_KEY) {
    try {
      ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    } catch (err) {
      console.error("Failed to initialize GoogleGenAI:", err);
    }
  }
  return ai;
}

// Fleet Data Context for AI Copilot
const fleetSystemContext = `
Bạn là Fleet AI Copilot - Trợ lý trí tuệ nhân tạo giám sát an toàn đội xe Fleet Command.
Bạn cung cấp thông tin phân tích thời gian thực về tài xế, nguy cơ vi ngủ (microsleep), chỉ số TTC (Time to Collision), tốc độ, thời gian nghỉ và tình trạng bảo trì phương tiện.

Dữ liệu hiện tại của đội xe:
1. Xe VH-04 (Tài xế A - Nguyễn Văn A):
   - Mức độ rủi ro: CRITICAL (Báo động đỏ)
   - Điểm an toàn (Safe Score): 42/100 (Sụt 28 điểm)
   - Trạng thái tài xế: Drowsy / Microsleep (Phát hiện vi ngủ 2 lần trong khung giờ 2h-4h sáng)
   - TTC (Time to Collision) thấp nhất: 1.2s
   - Tốc độ: 65 km/h
   - Đánh giá AI: "Chuyến đi này bị trừ 28 điểm. Nguyên nhân cốt lõi do tài xế có 2 khoảnh khắc vi ngủ (microsleep) nguy hiểm tại frame 450 và 520 khi xe đang di chuyển ở vận tốc cao 65km/h. Hệ thống cũng ghi nhận 1 tình huống phanh gấp giật cục do tài xế giật mình sau khi xao nhãng nhìn điện thoại."
   - Khuyến nghị: Cần điều chỉnh lịch trình của Tài xế A, tránh chạy liên tục quá 4 tiếng vào ban đêm. Đề xuất gửi thông báo yêu cầu dừng chân nghỉ ngơi 30 phút ngay lập tức.

2. Xe VH-01 (Tài xế B - Phạm Văn B):
   - Mức độ rủi ro: HIGH / WARNING (Mức độ cảnh báo cao)
   - Điểm an toàn: 68.2/100
   - Mức độ tỉnh táo (Alertness): 38%
   - Tốc độ: 58-65 km/h
   - Sự cố vừa qua: Ngáp (Yawn), Phanh gấp (Harsh Brake), Microsleep ngắn
   - TTC: 2.4s

3. Xe VH-02 (Tài xế C - Nguyễn Văn C):
   - Mức độ rủi ro: SAFE (An toàn)
   - Điểm an toàn: 98.4/100 (Top 1 Tài xế An Toàn - Elite)
   - Tốc độ: 62 mph (100 km/h)
   - Trạng thái: Di chuyển ổn định

4. Xe VH-05: Trạng thái Idling (Đang nổ máy dừng), Cần kiểm tra thời gian nổ máy chờ (4.2h idle time gây hao tốn 8.4% nhiên liệu)
5. Xe VH-08: Cảnh báo bảo trì hệ thống phanh (Hard braking x24 lần tuần này, nguy cơ mòn phanh +15%)

Hãy trả lời bằng tiếng Việt chuyên nghiệp, ngắn gọn, súc tích, đi thẳng vào vấn đề như một trợ lý chỉ huy đội xe thông minh.
`;

// Health check
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// AI Copilot endpoint
app.post("/api/copilot", async (req, res) => {
  const { message, chatHistory, vehicles = [] } = req.body as {
    message?: string;
    chatHistory?: ChatHistoryItem[];
    vehicles?: TripSummary[];
  };

  if (!message || typeof message !== "string") {
    res.status(400).json({ error: "Thông điệp không hợp lệ" });
    return;
  }

  const reportRequest = detectReportType(message);
  if (reportRequest) {
    const mentionedTripIds = findMentionedTripIds(message, vehicles);
    const selectedTripIds = reportRequest.type === "compare"
      ? mentionedTripIds.slice(0, reportRequest.requestedCount)
      : (mentionedTripIds.length ? mentionedTripIds : availableTripIds(vehicles).slice(0, reportRequest.requestedCount));

    if (reportRequest.type === "compare" && selectedTripIds.length < reportRequest.requestedCount) {
      res.json({
        reply: [
          `Bạn muốn so sánh ${reportRequest.requestedCount} tài xế/trip, nhưng hiện mới thấy ${selectedTripIds.length ? selectedTripIds.join(", ") : "chưa có trip_id nào"}.`,
          `Bạn gửi thêm ${reportRequest.requestedCount - selectedTripIds.length} trip_id còn thiếu nha.`,
          `Trip hiện có: ${availableTripIds(vehicles).join(", ") || "chưa có trip nào từ Dashboard"}.`,
        ].join("\n"),
      });
      return;
    }

    try {
      // Get ALL available vehicles (or mentioned ones if user specified)
      const targetTripIds = (mentionedTripIds.length > 0) ? mentionedTripIds : availableTripIds(vehicles);
      const selectedVehicles = vehicles.filter((vehicle) => targetTripIds.includes(vehicle.trip_id));
      
      const isMaintenance = reportRequest.type === "maintenance";

      // Calculate ranking list
      // For SAFETY: Sorted from HIGHEST safety score to LOWEST safety score (Safe driver #1)
      // For MAINTENANCE: Sorted from LOWEST safety score / HIGHEST risk (Highest Maintenance Priority #1)
      const rankedDrivers = selectedVehicles.map((v) => {
        const safeScore = (v.trip_aggregate as any)?.safe_driving_score ?? 80;
        const harshBraking = (v.trip_aggregate as any)?.harsh_brake_count ?? 0;
        const driverName = v.metadata?.driver_profile ?? (v.driver_summary as any)?.subject_id ?? v.trip_id;
        const dtcCode = harshBraking >= 10 ? "C0035 (Brake Sensor)" : safeScore < 60 ? "P0300 (Engine Misfire)" : "P0000 (Normal)";
        return {
          trip_id: v.trip_id,
          driverName,
          safeScore: Number(safeScore),
          harshBraking,
          dtcCode,
          maintenancePriority: safeScore < 60 ? "CRITICAL" : safeScore < 80 ? "HIGH" : "ROUTINE"
        };
      }).sort((a, b) => isMaintenance ? a.safeScore - b.safeScore : b.safeScore - a.safeScore);

      const finalTripIds = rankedDrivers.map(d => d.trip_id);

      const prompt = isMaintenance
        ? `
Bạn là Fleet Maintenance AI Copilot cho FPTU DMS Vision.
Nhiệm vụ: tạo lời mở đầu ngắn gọn cho BÁO CÁO ƯU TIÊN BẢO TRÌ TELEMETRY ĐỘI XE.
Ghi rõ: Báo cáo đã sắp xếp TOÀN BỘ ${rankedDrivers.length} xe theo MỨC ĐỘ ƯU TIÊN BẢO TRÌ TỪ CAO ĐẾN THẤP (Xe rủi ro hỏng hóc/lỗi kỹ thuật cao nhất đứng đầu để thu hồi sửa chữa trước): ${rankedDrivers.map(d => `Xe ${d.trip_id} (${d.driverName} - Score: ${d.safeScore}/100)`).join(", ")}.
Trả lời tiếng Việt, 2-3 câu ngắn gọn, chuyên nghiệp.

User request: ${message}
`
        : `
Bạn là Fleet AI Copilot cho FPTU DMS Vision.
Nhiệm vụ: tạo lời mở đầu ngắn gọn cho BÁO CÁO AN TOÀN ĐỘI XE.
Ghi rõ: Báo cáo đã sắp xếp TOÀN BỘ ${rankedDrivers.length} chuyến đi theo MỨC ĐỘ AN TOÀN TỪ CAO ĐẾN THẤP (Tài xế điểm an toàn cao nhất đứng đầu): ${rankedDrivers.map(d => `${d.driverName} (${d.safeScore}/100)`).join(", ")}.
Trả lời tiếng Việt, 2-3 câu ngắn gọn, chuyên nghiệp.

User request: ${message}
`;

      const aiReply = await callBedrockConverse(prompt);
      res.json({
        reply: "",
        cardType: "COMPARISON",
        cardData: {
          title: isMaintenance
            ? `Báo Cáo Ưu Tiên Bảo Trì Telemetry (Ưu Tiên Cao ➔ Thấp)`
            : reportRequest.type === "compare"
              ? `Bảng Xếp Hạng Mức Độ An Toàn (Từ Cao ➔ Thấp)`
              : `Bảng Xếp Hạng An Toàn Fleet (Từ Cao ➔ Thấp)`,
          details: aiReply || (isMaintenance
            ? "AI Copilot đã phân tích các chỉ số telemetry và mã lỗi DTC, sắp xếp danh sách xe theo Ưu tiên Bảo trì từ Cao đến Thấp."
            : "AI Copilot đã tổng hợp danh sách toàn bộ chuyến đi, sắp xếp theo điểm an toàn từ Cao đến Thấp."),
          sortRule: isMaintenance
            ? "Sắp xếp: Mức độ ưu tiên bảo trì từ CAO ➔ THẤP (Xe hỏng hóc/rủi ro cao xếp trước)"
            : "Sắp xếp: Mức độ an toàn từ CAO ➔ THẤP (An toàn nhất xếp trước)",
          functionName: isMaintenance
            ? "create_maintenance_priority_report"
            : reportRequest.type === "compare"
              ? "create_driver_comparison_report"
              : "create_fleet_safety_report",
          reportType: reportRequest.type,
          count: finalTripIds.length,
          tripIds: finalTripIds,
          rankedDrivers,
        },
      });
      return;
    } catch (err) {
      console.error("Bedrock report card error:", err);
      res.status(503).json({
        error: err instanceof Error ? err.message : "Bedrock provider error",
      });
      return;
    }
  }

  if (getBedrockBearerToken()) {
    try {
      const historyText = (chatHistory || [])
        .slice(-8)
        .map((msg) => `${msg.sender}: ${msg.text}`)
        .join("\n");
      const reply = await callBedrockConverse(`
${fleetSystemContext}

Trip context từ Dashboard:
${buildTripContext(vehicles)}

Chat history:
${historyText}

User: ${message}

Trả lời tiếng Việt, dùng số liệu nếu có, không bịa field mới.
`);
      res.json({ reply: reply || "Đã phân tích xong dữ liệu đội xe." });
      return;
    } catch (err) {
      console.error("Bedrock API Error:", err);
    }
  }

  const client = getGeminiClient();

  if (client) {
    try {
      const response = await client.models.generateContent({
        model: "gemini-2.5-flash",
        contents: [
          { role: "user", parts: [{ text: fleetSystemContext }] },
          ...(chatHistory || []).map((msg: { sender: string; text: string }) => ({
            role: msg.sender === "user" ? "user" : "model",
            parts: [{ text: msg.text }],
          })),
          { role: "user", parts: [{ text: message }] },
        ],
      });

      const reply = response.text || "Đã phân tích xong dữ liệu đội xe.";
      res.json({ reply });
      return;
    } catch (err) {
      console.error("Gemini API Error:", err);
    }
  }

  res.status(503).json({
    error: "Copilot provider is not configured. Set AWS_BEARER_TOKEN_BEDROCK or GEMINI_API_KEY.",
  });
});

app.post("/api/copilot/report", async (req, res) => {
  const { reportType, tripIds, expandedTripIds = [], rows, vehicles = [] } = req.body as {
    reportType?: string;
    tripIds?: string[];
    expandedTripIds?: string[];
    rows?: unknown[];
    vehicles?: TripSummary[];
  };

  if (!getBedrockBearerToken()) {
    res.status(503).json({ error: "AWS_BEARER_TOKEN_BEDROCK is not configured" });
    return;
  }

  try {
    const isMaintenanceReport = reportType === 'maintenance';

    const promptText = isMaintenanceReport
      ? `
Bạn là Fleet Maintenance Technical AI Copilot cho FPTU Automotive DMS.
Nhiệm vụ: Tóm tắt tình trạng bảo trì dựa TRÊN ĐÚNG DỮ LIỆU ĐÃ XỬ LÝ (RULE-BASED). KHÔNG ĐƯỢC TỰ BỊA ĐẶT con số, lý thuyết vật lý mâu thuẫn hay chi phí ảo.

BỘ TỪ ĐIỂN MÃ LỖI OBD-II BẮT BUỘC (DTC DICTIONARY):
- C0035: Lỗi cảm biến tốc độ bánh xe trước bên trái (Wheel Speed Sensor Circuit). Chi phí thay thế cảm biến & căn chỉnh: 1.500.000 VNĐ - 3.000.000 VNĐ.
- P0300: Lỗi bỏ lửa động cơ đa xi-lanh (Multi-Cylinder Misfire). Chi phí kiểm tra bugi & béc phun: 2.500.000 VNĐ - 4.500.000 VNĐ.
- P0000: Không có lỗi hệ thống (No Diagnostic Trouble Code). Chi phí bảo dưỡng định kỳ thay dầu & lọc gió: 1.500.000 VNĐ - 2.500.000 VNĐ (dự tính).

LUẬT CẤM CHỐNG ẢO GIÁC (STRICT ANTI-HALLUCINATION RULES):
1. TUYỆT ĐỐI KHÔNG tự giải thích nguyên lý vật lý mâu thuẫn dữ liệu: Nếu vi phạm quá tốc độ = 0.0%, CẤM KHÔNG ĐƯỢC NÓI "tốc độ làm mài mòn lốp do lực ly tâm".
2. KHÔNG CẢNH BÁO ABS NẾU CÓ LỖI C0035: Nếu xe có mã lỗi C0035 (Lỗi cảm biến tốc độ bánh xe), TUYỆT ĐỐI CẤM KHÔNG ĐƯỢC khen "Hệ thống ABS vận hành tốt hoặc không có xung đột" ở mục Điểm Tốt.
3. ĐỒNG BỘ CẤP ĐỘ ƯU TIÊN (PRIORITY MATCH): Nếu xe ở mức CRITICAL (MSI > 75), câu chốt BẮT BUỘC ghi "🚨 DỪNG LƯU HÀNH NGAY (Do Not Drive)". Nếu mức AT_RISK/HIGH, ghi "⚠️ BẢO TRÌ ƯU TIÊN 48H". Không hạ cấp vô lý.
4. TUYỆT ĐỐI KHÔNG tự bịa con số chi phí tài chính vượt quá 5.000.000 VNĐ nếu chỉ mang mã lỗi C0035 hoặc P0000. Tôn trọng 100% dự toán từ Rule-based Engine.
5. SỬ DỤNG ĐÚNG BIẾN CHUYẾN XE: Các văn bản hành động phải lấy ĐÚNG mã chuyến xe đang xét (ví dụ: T01-Sample), tuyệt đối không tự lấy mã xe khác không nằm trong dữ liệu truyền vào.

Yêu cầu trả về BẮT BUỘC theo cấu trúc JSON thuần túy (không markdown formatting, không bọc json codeblock):
{
  "fleet_insight": "📊 **BÁO CÁO TỔNG QUAN ƯU TIÊN BẢO TRÌ & QUẢN LÝ DỰ TOÁN VẬT TƯ FLEET**\\n\\n1. 🛠️ **Tình Trạng Sức Khỏe Kỹ Thuật Fleet:**\\n   - Ghi nhận mã lỗi DTC **C0035** (Cảm biến tốc độ bánh xe) và **P0000** (Hệ thống bình thường).\\n   - Tổng dự toán chi phí thay thế vật tư & bảo dưỡng toàn fleet: **~4.500.000 VNĐ (dự tính)**.\\n\\n2. 🛑 **Lệnh Thu Hồi & Dừng Lưu Hành (Do Not Drive):**\\n   - Yêu cầu kiểm tra cảm biến C0035 cho xe rủi ro trong 48h.\\n\\n3. 📦 **Kế Hoạch Vật Tư & Downtime Nằm Xưởng:**\\n   - Cảm biến & phụ tùng thay dầu **Sẵn có trong kho**. Thời gian nằm xưởng: **0.5 ngày**.",
  "trip_insights": {
    "T04-EcoSafeDrive": {
      "driver_name": "Driver_LeVanD",
      "safe_score": 95,
      "dtc_code": "P0000 (Hệ thống bình thường)",
      "pros": [
        "Chỉ số MSI phanh 18/100 (Log đã lọc nhiễu: chỉ phanh nhẹ 1 lần ở vận tốc 35 km/h).",
        "Tốc độ quá ngưỡng 0.0%, lốp xe không chịu tác động ma sát nhiệt bất thường."
      ],
      "cons": [
        "Số Odometer đạt 38.900 km - sắp đến mốc bảo dưỡng định kỳ thay dầu 40.000 km."
      ],
      "evaluation": "Nội suy từ Log Telemetry đã lọc nhiễu: Đạt chuẩn Bảo Dưỡng Định Kỳ Tiêu Chuẩn (~1.850.000 VNĐ dự tính - thay dầu & lọc gió)."
    },
    "T02-AggressiveDrive": {
      "driver_name": "Driver_NguyenVanB",
      "safe_score": 54,
      "dtc_code": "C0035 (Lỗi cảm biến tốc độ bánh xe)",
      "pros": [
        "Hệ thống làm mát động cơ duy trì nhiệt độ ổn định 90°C."
      ],
      "cons": [
        "Mã lỗi C0035 (Lỗi cảm biến tốc độ bánh xe trước bên trái) cần thay thế.",
        "Ghi nhận 2 lần phanh gấp gắt khi chạy dải tốc độ cao (đã lọc nhiễu 3 giây)."
      ],
      "evaluation": "BẢO TRÌ ƯU TIÊN 48H: Thu hồi xe thay cảm biến C0035 (~2.500.000 VNĐ dự tính)."
    }
  },
  "vehicle_diagnostics": [
    {
      "trip_id": "T04-EcoSafeDrive",
      "odometer_km": 38900,
      "engine_hours": 920,
      "km_to_next_service": "Còn 6.100 km",
      "brake_msi": 18,
      "tire_msi": 12,
      "dtc_code": "P0000 (Hệ thống bình thường)",
      "maintenance_status": "Bảo dưỡng định kỳ chuẩn",
      "parts_availability": "Sẵn có trong kho",
      "estimated_cost_vnd": "1.850.000 VNĐ (dự tính)",
      "estimated_downtime": "0.5 ngày",
      "work_order_status": "Routine Approved"
    }
  ],
  "action_orders": {
    "do_not_drive": "Thu hồi xe T02-AggressiveDrive thay cảm biến C0035...",
    "priority_48h": "Bảo trì ưu tiên thay cảm biến C0035 trong 48h...",
    "routine_maintenance": "Bảo dưỡng định kỳ chuẩn thay dầu cho xe T04-EcoSafeDrive..."
  }
}
`
      : `
**Role:** Bạn là "Fleet Data Validator" - Chuyên gia Kiểm toán Logic Dữ liệu Vận tải cực kỳ nghiêm khắc. 
**Nhiệm vụ:** Đọc dữ liệu đầu vào (Raw Data), đối chiếu chéo TẤT CẢ các chỉ số để đảm bảo tính logic tuyệt đối, sau đó xuất ra Báo cáo Phân tích. Tuyệt đối KHÔNG được sáng tạo, phỏng đoán hay bóp méo ý nghĩa của con số. Thay vì lặp lại chi tiết từng trip, hãy đưa ra NHẬN XẾT TỔNG QUAN TẬP TRUNG VÀO GIÁ TRỊ BUSINESS.

**🚨 STRICT LOGIC RULES (BẮT BUỘC TUÂN THỦ TỪNG CHỮ):**

1. QUY TẮC ĐỒNG BỘ ĐIỂM SỐ & NHẬN XÉT (Score vs. Sentiment):
- NẾU Safe Score >= 85: Tài xế thuộc nhóm XUẤT SẮC (SAFE). Bắt buộc phải khen ngợi ở mục 🟢 Ưu điểm (pros).
- NẾU Safe Score từ 60 - 84: Tài xế nhóm CẢNH BÁO (WATCH). Bắt buộc phải đưa ra yêu cầu cải thiện.
- NẾU Safe Score < 60: Tài xế nhóm NGUY HIỂM (AT_RISK/CRITICAL). Bắt buộc đề xuất 🛑 Coaching 24H. Không được có mục 🟢 Ưu điểm (pros).

2. QUY TẮC CHỐNG MÂU THUẪN CHỈ SỐ (Metric Anti-Contradiction):
- Xao nhãng (Distraction): NẾU > 5%, BẮT BUỘC xếp vào 🔴 Nhược điểm (cons). NẾU > 20%, đây là rủi ro nghiêm trọng (Critical Risk), không được phép gọi tài xế là "Mẫu mực" dù Safe Score cao đến đâu.
- Quá tốc độ (Speeding): NẾU > 0.0%, tuyệt đối KHÔNG ĐƯỢC dùng từ "tuân thủ tốc độ tốt". Phải ghi rõ: "Vi phạm tốc độ X%".
- Phanh gấp (Harsh brake): NẾU > 0, đây là dấu hiệu thiếu quan sát hoặc không giữ khoảng cách.

3. QUY TẮC TOÁN HỌC & ĐỒNG BỘ LOG (Math Consistency):
- Số lượng sự kiện trong "Nhật ký Log" BẮT BUỘC PHẢI BẰNG tổng số đếm ở mục "Sự kiện". 
- Tuyệt đối không tự bịa thêm log hoặc tự cộng dồn sai lệch. Nếu đầu vào chỉ có 3 log, hãy phân tích dựa trên đúng 3 log đó.

4. QUY TẮC LỆNH HÀNH ĐỘNG (Action Orders):
- Các lệnh như "🛑 Coaching", "⚠️ Nhắc nhở", "🏆 Khen thưởng" BẮT BUỘC phải đi kèm trực tiếp với Tên Tài Xế thực tế đang được xét, không được gán nhầm tên tài xế khác.

Yêu cầu trả về BẮT BUỘC theo cấu trúc JSON thuần túy (không markdown formatting, không bọc json codeblock):
{
  "fleet_insight": "📊 **BÁO CÁO TỔNG QUAN TÁC ĐỘNG BUSINESS & CHI PHÍ BẢO TRÌ**\\n\\n1. 📈 **Hiệu Quả Vận Hành & An Toàn Fleet:**\\n   - Điểm an toàn trung bình đạt **75.3/100**. Tỷ lệ phanh gấp toàn fleet chiếm tới 38 lượt, cảnh báo nguy cơ hao mòn linh kiện sớm.\\n\\n2. 💰 **Dự Báo Chi Phí Rủi Ro & TCO (Total Cost of Ownership):**\\n   - Ước tính **tăng 18.5% chi phí thay má phanh & lốp xe** trong tháng do tần suất phanh gấp và quá tốc độ cao ở nhóm xe rủi ro (T02, T01).\\n   - Chi phí rủi ro sự cố tiềm ẩn ước tính: **~48.500.000 VNĐ** nếu không kiểm tra kỹ thuật kịp thời.\\n\\n3. 🎯 **Đề Xuất Hành Động Dành Cho Ban Quản Lý (Executive ROI Action):**\\n   - 🛑 **Tối ưu chi phí:** Thu hồi kiểm tra hệ thống phanh 2 xe rủi ro để giảm 80% nguy cơ hỏng hóc nặng hệ thống truyền động.\\n   - 🏆 **Khen thưởng:** Đề xuất chính sách thưởng tiết kiệm nhiên liệu cho tài xế mẫu mực (T04-EcoSafeDrive).",
  "trip_insights": {
    "T04-EcoSafeDrive": {
      "driver_name": "Driver_LeVanD",
      "safe_score": 95,
      "pros": [
        "Safety Score xuất sắc (95/100), 0 lần phanh gấp (harsh_brake = 0)."
      ],
      "cons": [
        "Ghi nhận 11 sự kiện rủi ro tiềm ẩn bên ngoài."
      ],
      "evaluation": "🏆 Khen thưởng: Tài xế mẫu mực chuẩn an toàn để đội xe học tập."
    },
    "T02-AggressiveDrive": {
      "driver_name": "Driver_NguyenVanB",
      "safe_score": 54,
      "pros": [
        "Hoàn thành lộ trình đúng thời gian."
      ],
      "cons": [
        "Score thấp (54/100), phanh gấp 14 lần, quá tốc độ 42.5%.",
        "Mức rủi ro cực đại 88/100 (AT_RISK)."
      ],
      "evaluation": "Cần can thiệp coaching ưu tiên cao và kiểm tra phanh khẩn cấp."
    }
  },
  "vehicle_diagnostics": [
    {
      "trip_id": "T01-Sample",
      "brake_wear_pct": 92,
      "tire_wear_pct": 88,
      "odometer_km": 44170,
      "engine_hours": 1052,
      "dtc_code": "P0300 (Engine Misfire)",
      "maintenance_status": "Quá hạn 1.200 km",
      "parts_availability": "Sẵn có trong kho",
      "estimated_cost_vnd": "14.500.000 VNĐ",
      "estimated_downtime": "1.5 ngày"
    }
  ],
  "action_orders": {
    "do_not_drive": "Dừng lưu hành ngay xe...",
    "priority_48h": "Bảo trì ưu tiên trong 48h cho xe...",
    "routine_maintenance": "Bảo dưỡng định kỳ chuẩn..."
  }
}

Ranking rows:
${JSON.stringify(rows || [], null, 2)}

Trip context:
${buildTripContext(vehicles)}
`;

    const rawAiOutput = await callBedrockConverse(promptText);

    let parsed: any = { fleet_insight: rawAiOutput, trip_insights: {}, vehicle_diagnostics: null, action_orders: null };
    try {
      const cleanJson = rawAiOutput.replace(/```json/g, "").replace(/```/g, "").trim();
      parsed = JSON.parse(cleanJson);
    } catch {
      // Fallback
    }

    res.json({
      insight: parsed.fleet_insight || parsed.insight || rawAiOutput,
      fleet_insight: parsed.fleet_insight || parsed.insight || rawAiOutput,
      trip_insights: parsed.trip_insights || {},
      vehicle_diagnostics: parsed.vehicle_diagnostics || null,
      action_orders: parsed.action_orders || null,
    });
  } catch (err) {
    console.error("Bedrock report insight error:", err);
    res.status(503).json({ error: err instanceof Error ? err.message : "Bedrock provider error" });
  }
});

async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { 
        middlewareMode: true,
        hmr: {
          port: PORT + 20000 // Avoid port 24678 collision by offsetting HMR port
        }
      },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "127.0.0.1", () => {
    console.log(`Server is running on http://127.0.0.1:${PORT}`);
  });
}

startServer();
