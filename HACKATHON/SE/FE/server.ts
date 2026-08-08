import express from "express";
import path from "path";
import fs from "fs";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

dotenv.config({ path: ".env.local" });
dotenv.config();

app.use(express.json({ limit: "64mb" }));

// ── Trip Persistence Layer ──────────────────────────────────────────────────
// Saved completed trips live in <project>/src/data/saved_trips/{trip_id}.json
const SAVED_TRIPS_DIR = path.join(process.cwd(), "src", "data", "saved_trips");
if (!fs.existsSync(SAVED_TRIPS_DIR)) {
  fs.mkdirSync(SAVED_TRIPS_DIR, { recursive: true });
}

function clearSavedTripFiles(): number {
  if (!fs.existsSync(SAVED_TRIPS_DIR)) return 0;
  const files = fs.readdirSync(SAVED_TRIPS_DIR).filter((f) => f.endsWith(".json"));
  for (const file of files) {
    fs.unlinkSync(path.join(SAVED_TRIPS_DIR, file));
  }
  return files.length;
}

function clearSavedTripsForDemo(reason: string): void {
  try {
    const count = clearSavedTripFiles();
    if (count > 0) {
      console.log(`[trip-clear] Cleared ${count} saved demo trip(s): ${reason}`);
    }
  } catch (err) {
    console.error(`[trip-clear] Failed to clear saved demo trips during ${reason}:`, err);
  }
}

clearSavedTripsForDemo("Fleet Dashboard startup");

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.once(signal, () => {
    clearSavedTripsForDemo(signal);
    process.exit(0);
  });
}

process.once("exit", () => {
  clearSavedTripsForDemo("process exit");
});

type TripSummary = {
  trip_id: string;
  runtime_status?: "pending" | "running" | "completed";
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

function getCompletedSavedVehicles(): TripSummary[] {
  const result: TripSummary[] = [];
  try {
    if (fs.existsSync(SAVED_TRIPS_DIR)) {
      const files = fs.readdirSync(SAVED_TRIPS_DIR).filter((f) => f.endsWith(".json"));
      for (const file of files) {
        try {
          const filePath = path.join(SAVED_TRIPS_DIR, file);
          const content = fs.readFileSync(filePath, "utf-8");
          const parsed = JSON.parse(content);
          if (parsed && parsed.trip_id) {
            result.push({
              trip_id: parsed.trip_id,
              metadata: parsed.metadata,
              driver_summary: parsed.driver_summary,
              trip_aggregate: parsed.trip_aggregate,
            });
          }
        } catch {
          // ignore corrupted json
        }
      }
    }
  } catch (err) {
    console.error("[saved-trips] Error reading saved trips for copilot:", err);
  }
  return result;
}

function resolveCopilotVehicles(incomingVehicles: TripSummary[] = []): TripSummary[] {
  const savedVehicles = getCompletedSavedVehicles();
  const mergedMap = new Map<string, TripSummary>();

  // Only include incoming vehicles if their runtime_status is explicitly 'completed'
  for (const v of incomingVehicles) {
    if (v && v.trip_id && v.runtime_status === "completed") {
      mergedMap.set(v.trip_id, v);
    }
  }

  // Merge saved completed trip JSON files from disk (data/saved_trips/)
  for (const v of savedVehicles) {
    if (v && v.trip_id) {
      if (!mergedMap.has(v.trip_id)) {
        mergedMap.set(v.trip_id, { ...v, runtime_status: "completed" });
      }
    }
  }

  return Array.from(mergedMap.values());
}

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
    signal: AbortSignal.timeout(3500),
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

// ── Trip Persistence API ────────────────────────────────────────────────────

/**
 * POST /api/trips/save
 * Body: full TripData JSON (sent by frontend when a trip completes).
 * Saves to data/saved_trips/{trip_id}.json so future Copilot sessions
 * can access historical trip context without the backend being live.
 */
app.post("/api/trips/save", (req, res) => {
  const tripData = req.body as { trip_id?: string };
  if (!tripData?.trip_id || typeof tripData.trip_id !== "string") {
    res.status(400).json({ error: "trip_id is required" });
    return;
  }
  // Sanitise trip_id to safe filename characters
  const safeId = tripData.trip_id.replace(/[^a-zA-Z0-9_\-\.]/g, "_");
  const filePath = path.join(SAVED_TRIPS_DIR, `${safeId}.json`);
  try {
    fs.writeFileSync(filePath, JSON.stringify(tripData, null, 2), "utf-8");
    console.log(`[trip-save] Saved trip ${tripData.trip_id} → ${filePath}`);
    res.json({ saved: true, trip_id: tripData.trip_id });
  } catch (err) {
    console.error("[trip-save] Failed to write trip file:", err);
    res.status(500).json({ error: "Failed to save trip" });
  }
});

/**
 * GET /api/trips/saved
 * Returns list of all persisted trip IDs (files in data/saved_trips/).
 */
app.get("/api/trips/saved", (_req, res) => {
  try {
    const files = fs.readdirSync(SAVED_TRIPS_DIR).filter((f) => f.endsWith(".json"));
    const trips = files.map((f) => f.slice(0, -5)); // strip .json
    res.json({ count: trips.length, trips });
  } catch {
    res.json({ count: 0, trips: [] });
  }
});

/**
 * GET /api/trips/saved/:trip_id
 * Returns the full TripData JSON for a saved trip.
 */
app.get("/api/trips/saved/:trip_id", (req, res) => {
  const safeId = (req.params.trip_id ?? "").replace(/[^a-zA-Z0-9_\-\.]/g, "_");
  const filePath = path.join(SAVED_TRIPS_DIR, `${safeId}.json`);
  if (!fs.existsSync(filePath)) {
    res.status(404).json({ error: "Trip not found" });
    return;
  }
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    res.setHeader("Content-Type", "application/json");
    res.send(raw);
  } catch (err) {
    console.error("[trip-load] Failed to read trip file:", err);
    res.status(500).json({ error: "Failed to load trip" });
  }
});

/**
 * DELETE /api/trips/saved
 * Clears ALL saved completed trip JSON files in data/saved_trips/.
 */
app.delete("/api/trips/saved", (_req, res) => {
  try {
    const count = clearSavedTripFiles();
    res.json({ deleted: true, count });
  } catch (err) {
    console.error("[trip-clear] Failed to clear saved trips:", err);
    res.status(500).json({ error: "Failed to clear saved trips" });
  }
});

/**
 * DELETE /api/trips/saved/:trip_id
 * Removes a persisted trip file (useful for cleanup).
 */
app.delete("/api/trips/saved/:trip_id", (req, res) => {
  const safeId = (req.params.trip_id ?? "").replace(/[^a-zA-Z0-9_\-\.]/g, "_");
  const filePath = path.join(SAVED_TRIPS_DIR, `${safeId}.json`);
  if (!fs.existsSync(filePath)) {
    res.status(404).json({ error: "Trip not found" });
    return;
  }
  try {
    fs.unlinkSync(filePath);
    res.json({ deleted: true, trip_id: req.params.trip_id });
  } catch {
    res.status(500).json({ error: "Failed to delete trip" });
  }
});

// AI Copilot endpoint
app.post("/api/copilot", async (req, res) => {
  const { message, chatHistory, vehicles: rawVehicles = [] } = req.body as {
    message?: string;
    chatHistory?: ChatHistoryItem[];
    vehicles?: TripSummary[];
  };
  const vehicles = resolveCopilotVehicles(rawVehicles);

  if (!message || typeof message !== "string") {
    res.status(400).json({ error: "Thông điệp không hợp lệ" });
    return;
  }

  if (vehicles.length === 0) {
    res.json({
      reply: "Chưa có chuyến đi nào hoàn thành (status = completed). AI Copilot chỉ phân tích dữ liệu các chuyến đi đã kết thúc."
    });
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

    const isMaintenance = reportRequest.type === "maintenance";
    const targetTripIds = (mentionedTripIds.length > 0) ? mentionedTripIds : availableTripIds(vehicles);
    const selectedVehicles = vehicles.filter((vehicle) => targetTripIds.includes(vehicle.trip_id));

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

    try {
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
      res.json({
        reply: "",
        cardType: "COMPARISON",
        cardData: {
          title: isMaintenance
            ? `Báo Cáo Ưu Tiên Bảo Trì Telemetry (Ưu Tiên Cao ➔ Thấp)`
            : reportRequest.type === "compare"
              ? `Bảng Xếp Hạng Mức Độ An Toàn (Từ Cao ➔ Thấp)`
              : `Bảng Xếp Hạng An Toàn Fleet (Từ Cao ➔ Thấp)`,
          details: (isMaintenance
            ? "AI Copilot đã phân tích các chỉ số telemetry và mã lỗi DTC, sắp xếp danh sách xe theo Ưu tiên Bảo trì từ Cao đến Thấp (Chế độ mô phỏng ngoại tuyến)."
            : "AI Copilot đã tổng hợp danh sách toàn bộ chuyến đi, sắp xếp theo điểm an toàn từ Cao đến Thấp (Chế độ mô phỏng ngoại tuyến)."),
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

  // Fallback locally when no AI provider is successfully responding
  const lowerMsg = message.toLowerCase();
  let replyFallback = "Tôi là Trợ lý AI Copilot của FPTU DMS. Hiện tại tôi đang chạy ở chế độ mô phỏng ngoại tuyến. ";
  if (lowerMsg.includes("so sánh") || lowerMsg.includes("compare")) {
    replyFallback += "Để so sánh chi tiết các chuyến đi, bạn có thể xem Bảng Xếp Hạng An Toàn trên Dashboard hoặc sử dụng chức năng Báo cáo để so sánh tự động.";
  } else if (lowerMsg.includes("bảo trì") || lowerMsg.includes("hỏng") || lowerMsg.includes("lỗi") || lowerMsg.includes("maintenance")) {
    replyFallback += "Theo dữ liệu telemetry mới nhất, xe VH-04 (Tài xế Nguyễn Văn A) có điểm số 42/100, cần được ưu tiên kiểm tra phanh và rủi ro vi ngủ. Xe VH-08 cũng có tần suất phanh gấp cao.";
  } else if (lowerMsg.includes("an toàn") || lowerMsg.includes("safety") || lowerMsg.includes("tốt nhất") || lowerMsg.includes("nguy hiểm")) {
    replyFallback += "Xe VH-02 (Tài xế Nguyễn Văn C) là xe an toàn nhất với điểm số 98.4/100. Xe VH-04 (Tài xế Nguyễn Văn A) có nguy cơ cao nhất do vi ngủ.";
  } else {
    replyFallback += "Tôi có thể giúp bạn theo dõi trạng thái an toàn, hành vi lái xe (vi ngủ, xao nhãng), và lịch trình bảo trì của đội xe. Hãy hỏi tôi về các tài xế hoặc tình trạng bảo dưỡng của phương tiện nhé!";
  }

  res.json({ reply: replyFallback });
});

app.post("/api/copilot/report", async (req, res) => {
  const { reportType, tripIds, expandedTripIds = [], rows, vehicles: rawVehicles = [] } = req.body as {
    reportType?: string;
    tripIds?: string[];
    expandedTripIds?: string[];
    rows?: unknown[];
    vehicles?: TripSummary[];
  };
  const vehicles = resolveCopilotVehicles(rawVehicles);

  if (vehicles.length === 0) {
    res.json({
      insight: "Chưa có chuyến đi nào hoàn thành (status = completed) để lập báo cáo. AI Copilot chỉ phân tích các chuyến đi đã kết thúc.",
      fleet_insight: "Chưa có chuyến đi nào hoàn thành (status = completed) để lập báo cáo. AI Copilot chỉ phân tích các chuyến đi đã kết thúc.",
      trip_insights: {},
      vehicle_diagnostics: [],
      action_orders: null
    });
    return;
  }

  const isMaintenanceReport = reportType === 'maintenance';
  const targetTripIds = (tripIds && tripIds.length > 0) ? tripIds : vehicles.map(v => v.trip_id).filter(Boolean);
  const finalTripIds = targetTripIds.length > 0 ? targetTripIds : vehicles.map(v => v.trip_id).filter(Boolean);
  const isSingleTrip = finalTripIds.length === 1;
  const singleId = finalTripIds[0] || 'T01-Sample';

  const generateFallbackReport = () => {
    const singleV = isSingleTrip ? vehicles.find(v => v.trip_id === singleId) : null;
    const singleScore = (singleV?.trip_aggregate as any)?.safe_driving_score ?? 80;
    const singleDriver = singleV?.metadata?.driver_profile ?? (singleV?.driver_summary as any)?.subject_id ?? singleId;

    let mockInsight = "";

    if (isMaintenanceReport) {
      if (isSingleTrip) {
        // MODE 4: Maintenance Single Vehicle Diagnostic & Repair Cost
        const harshCount = (singleV?.trip_aggregate as any)?.harsh_brake_count ?? 0;
        const dtcCode = harshCount >= 5 ? "C0035 (Wheel Speed Sensor Circuit)" : singleScore < 60 ? "P0300 (Multi-Cylinder Misfire)" : "P0000 (No Error)";
        const estCost = harshCount >= 5 ? "2.500.000 VNĐ" : singleScore < 60 ? "3.500.000 VNĐ" : "1.850.000 VNĐ";
        const brakeWear = Math.min(98, 15 + harshCount * 5);
        mockInsight = `📊 **BÁO CÁO KHÁM BỆNH KỸ THUẬT XE ${singleId} (MAINTENANCE_DETAIL)**

### 1. Tổng quan Sức khỏe Phương tiện
- **Nhiệt độ động cơ:** 89°C (Dải vận hành chuẩn 88-92°C).
- **Áp suất lốp:** 2.3 bar (TSI 30/100, bề mặt lốp ổn định).
- **Chỉ số mòn phanh MSI:** ${brakeWear}/100 (Ghi nhận ${harshCount} lần rà phanh gắt).
- **Nhiên liệu/Pin:** 78% dung lượng khả dụng.

### 2. Chẩn đoán Mã lỗi Hệ thống (OBD-II / DTCs)
- **Mã lỗi ghi nhận:** **${dtcCode}**.
- **Phân tích rủi ro:** ${dtcCode.includes('C0035') ? 'Lỗi mạch cảm biến tốc độ bánh xe C0035 gây sai lệch hệ thống kiểm soát chống bó cứng phanh ABS khi phanh gấp.' : dtcCode.includes('P0300') ? 'Bỏ lửa động cơ đa xi-lanh P0300 làm giảm công suất kéo và gây hao nhiên liệu bất thường.' : 'Hệ thống điện tử và cảm biến động cơ vận hành hoàn toàn bình thường.'}

### 3. Phân tích Khấu hao & Hao mòn
- **Động cơ & Truyền động:** Áp suất dầu máy duy trì chuẩn, không ghi nhận dấu hiệu quá nhiệt.
- **Hệ thống phanh:** Chỉ số mòn phanh MSI ở mức ${brakeWear}/100. ${harshCount >= 5 ? 'Cần vớt đĩa phanh và kiểm tra đệm lót ngay.' : 'Vận hành ổn định.'}

### 4. Quyết định Bảo trì & Dự toán (Maintenance & Cost)
- **Hành động tức thời:** ${dtcCode.includes('C0035') || singleScore < 60 ? '🛑 Yêu cầu thu hồi xe vào xưởng gara kiểm tra khẩn cấp trong 48h.' : '✅ Xe hoạt động tốt, tiếp tục lưu hành chuẩn.'}
- **Dự toán ngân sách ước tính:** **${estCost} (dự tính)** cho các hạng mục thay thế & căn chỉnh xưởng.`;
      } else {
        // MODE 3: MAINTENANCE_OVERVIEW
        const criticalCount = vehicles.filter(v => ((v.trip_aggregate as any)?.safe_driving_score ?? 100) < 60).length;
        const totalEst = (finalTripIds.length * 2200000).toLocaleString('vi-VN');
        mockInsight = `📊 **BÁO CÁO CHIẾN LƯỢC BẢO TRÌ & TCO TOÀN ĐỘI (MAINTENANCE_OVERVIEW)**

### 1. Đánh giá Khấu hao Toàn hạm đội (${finalTripIds.length} xe)
- **Tỷ lệ xe hoạt động chuẩn:** ${((finalTripIds.length - criticalCount) / finalTripIds.length * 100).toFixed(0)}% (${finalTripIds.length - criticalCount}/${finalTripIds.length} xe).
- **Tỷ lệ xe mang mã lỗi / suy giảm vật lý:** ${(criticalCount / finalTripIds.length * 100).toFixed(0)}% (${criticalCount}/${finalTripIds.length} xe).

### 2. Phân loại Cấp cứu & Bảo dưỡng (Triage System)
- 🛑 **Nhóm Khẩn cấp (Critical):** ${criticalCount > 0 ? `Các xe ${vehicles.filter(v => ((v.trip_aggregate as any)?.safe_driving_score ?? 100) < 60).map(v => v.trip_id).join(", ")} mang rủi ro phanh gắt/mã lỗi kỹ thuật.` : 'Không có xe nào thuộc diện cấp cứu khẩn.'}
- ⚠️ **Nhóm Lịch trình (Scheduled):** Các xe ${finalTripIds.filter(id => !vehicles.find(v => v.trip_id === id && ((v.trip_aggregate as any)?.safe_driving_score ?? 100) < 60)).join(", ")} tới hạn bảo dưỡng định kỳ thay dầu 40.000 km.

### 3. Dự báo Hỏng hóc tiềm ẩn (Predictive Maintenance Insights)
- Cảm biến tốc độ bánh xe và đĩa phanh là bộ phận có tốc độ suy giảm MSI nhanh nhất do tần suất rà phanh khi giao thông đông đúc. Dự báo cần nhập sẵn 5 bộ cảm biến C0035 trong kho xưởng.

### 4. Tối ưu Chi phí Vận hành (TCO Optimization)
- Dự toán tổng ngân sách bảo dưỡng toàn fleet: **~${totalEst} VNĐ**. Việc thu hồi bảo trì sớm giúp giảm 85% rủi ro hỏng hóc nặng hệ thống truyền động.`;
      }
    } else {
      if (isSingleTrip) {
        // MODE 2: SAFETY_DETAIL
        const frames = (singleV as any)?.frames ?? [];
        const totalFrames = Math.max(frames.length, 1);
        let distractedFrames = 0;
        let fatigueFrames = 0;
        let harshCount = 0;
        frames.forEach((f: any) => {
          if (f.driver?.state === 'distracted') distractedFrames++;
          if (f.driver?.state === 'drowsy' || f.driver?.state === 'microsleep') fatigueFrames++;
          if (f.behavior_flags?.harsh_brake) harshCount++;
        });
        const distPct = ((distractedFrames / totalFrames) * 100).toFixed(1);

        mockInsight = `📊 **BÁO CÁO PHÂN TÍCH AN TOÀN CHUYÊN SÂU CHUYẾN XE ${singleId} (SAFETY_DETAIL)**

### 1. Chỉ số cốt lõi (Core Metrics)
- **Safe Score:** **${singleScore.toFixed(0)}/100** (${singleScore >= 80 ? 'An Toàn / Safe' : singleScore >= 60 ? 'Cảnh Báo / Watch' : 'Nguy Hiểm / Critical'}).
- **Tỷ lệ xao nhãng quan sát:** **${distPct}%** | **Số sự kiện vi ngủ:** **${fatigueFrames} lần** | **Phanh gấp:** **${harshCount} lần**.

### 2. Tái hiện dòng thời gian sự kiện (Event Timeline Analysis)
- **Giây 00:15 - 00:45:** Trạng thái tài xế chuyển từ Alert -> Distracted (Xao nhãng quan sát điện thoại), chỉ số khoảng cách va chạm TTC giảm xuống 1.8 giây.
- **Giây 01:20:** Ghi nhận sự kiện phanh gấp gắt do thiếu quan sát khi phương tiện phía trước giảm tốc đột ngột.

### 3. Đánh giá hành vi & Nguyên nhân gốc rễ (Root-cause)
- Tỷ lệ xao nhãng chiếm **${distPct}%** thời gian vận hành là nguyên nhân gốc rễ làm chậm thời gian phản xạ phanh 1.2 giây, dẫn đến sự kiện phanh gắt.

### 4. Khuyến nghị Can thiệp cá nhân (Micro-Coaching Plan)
- ${singleScore < 60 || fatigueFrames > 0 || parseFloat(distPct) > 35 ? `🛑 Ban hành Lệnh Đình Chỉ 24H: Tạm ngưng phân công chuyến và bắt buộc tài xế ${singleDriver} tham gia khóa huấn luyện kỹ năng tập trung.` : `⚠️ Yêu cầu tài xế ${singleDriver} không sử dụng thiết bị di động trong quá trình lái xe.`}`;
      } else {
        // MODE 1: SAFETY_OVERVIEW
        const avgScore = (vehicles.reduce((s, v) => s + ((v.trip_aggregate as any)?.safe_driving_score ?? 80), 0) / Math.max(vehicles.length, 1)).toFixed(1);
        const topSafe = vehicles.filter(v => ((v.trip_aggregate as any)?.safe_driving_score ?? 80) >= 80).map(v => v.trip_id);
        const topRisk = vehicles.filter(v => ((v.trip_aggregate as any)?.safe_driving_score ?? 80) < 60).map(v => v.trip_id);

        mockInsight = `📊 **BÁO CÁO ĐÁNH GIÁ AN TOÀN TOÀN ĐỘI XE (SAFETY_OVERVIEW)**

### 1. Bức tranh toàn cảnh (Fleet Safety Landscape)
- Điểm an toàn trung bình toàn fleet: **${avgScore}/100**. Khái quát vận hành của ${finalTripIds.length} chuyến đi: ${finalTripIds.join(", ")}.

### 2. Xếp hạng & Phân nhóm Tài xế (Driver Ranking)
- 🔴 **Vùng Đỏ (Top Risk):** ${topRisk.length > 0 ? `Các chuyến đi ${topRisk.join(", ")} vi phạm quy tắc an toàn (Score < 60 hoặc có vi ngủ/xao nhãng cao).` : 'Không có chuyến nào ở Vùng Đỏ.'}
- 🟢 **Vùng Xanh (Top Safe):** Các chuyến đi ${topSafe.join(", ")} thể hiện kỹ năng lái xe chuẩn mực.

### 3. Phân tích Xu hướng Vi phạm cốt lõi
- Xao nhãng quan sát nhìn điện thoại là lỗ hổng an toàn lớn nhất toàn đội xe (chiếm 68% tổng số lỗi ghi nhận).

### 4. Quyết định Quản trị (Executive Action)
- **Danh sách Coaching 24H:** ${topRisk.length > 0 ? `Đình chỉ 24h đối với tài xế chuyến ${topRisk.join(", ")}.` : 'Không có.'}
- **Danh sách Khen thưởng:** Vinh danh Safe Driver cho tài xế các chuyến ${topSafe.join(", ")}.`;
      }
    }

    const mockTripInsights: Record<string, any> = {};
    const mockVehicleDiagnostics: any[] = [];

    finalTripIds.forEach((tId) => {
      const v = vehicles.find((vehicle) => vehicle.trip_id === tId);
      const frames = (v as any)?.frames ?? [];
      const totalFrames = Math.max(frames.length, 1);

      let distractedFrames = 0;
      let fatigueFrames = 0;
      let speedingFrames = 0;
      let harshBrakeCount = 0;

      frames.forEach((f: any) => {
        const state = f.driver?.state;
        if (state === 'distracted') distractedFrames++;
        if (state === 'drowsy' || state === 'microsleep' || state === 'yawning') fatigueFrames++;
        if (f.behavior_flags?.speeding) speedingFrames++;
        if (f.behavior_flags?.harsh_brake) harshBrakeCount++;
      });

      const distractedPct = (distractedFrames / totalFrames) * 100;
      const speedingPct = (speedingFrames / totalFrames) * 100;
      const safeScore = (v?.trip_aggregate as any)?.safe_driving_score ?? Math.max(40, Math.round(100 - (distractedPct * 0.4 + fatigueFrames * 5 + harshBrakeCount * 3)));
      const driverName = v?.metadata?.driver_profile ?? (v?.driver_summary as any)?.subject_id ?? tId;
      const dtcCode = harshBrakeCount >= 5 ? "C0035 (Wheel Speed Sensor Circuit)" : safeScore < 60 ? "P0300 (Multi-Cylinder Misfire)" : "P0000 (No Error)";

      const isCriticalRisk = safeScore < 60 || distractedPct > 35 || fatigueFrames > 0;
      const dynamicPros: string[] = [];
      const dynamicCons: string[] = [];

      if (isCriticalRisk) {
        dynamicPros.push(`Chưa ghi nhận hành vi an toàn tiêu biểu do tài xế vi phạm quy tắc an toàn nghiêm trọng.`);
      } else {
        if (safeScore >= 80 && distractedPct <= 20 && fatigueFrames === 0) {
          dynamicPros.push(`Safety Score thuộc nhóm xuất sắc (${safeScore.toFixed(0)}/100), kiểm soát rủi ro tốt.`);
        } else if (safeScore >= 60 && distractedPct <= 25) {
          dynamicPros.push(`Safety Score ở mức chấp nhận được (${safeScore.toFixed(0)}/100).`);
        }

        if (speedingPct === 0) {
          dynamicPros.push(`Tuân thủ giới hạn tốc độ tuyệt đối (0.0%).`);
        }
        if (harshBrakeCount === 0) {
          dynamicPros.push(`Vận hành mượt mà, không ghi nhận phanh gấp nguy hiểm.`);
        }
      }

      if (safeScore < 60) {
        dynamicCons.push(`Điểm an toàn cực kỳ thấp (${safeScore.toFixed(0)}/100), thuộc nhóm rủi ro nguy hiểm.`);
      }
      if (speedingPct > 0) {
        dynamicCons.push(`Vi phạm tốc độ ở mức ${speedingPct.toFixed(1)}% thời gian.`);
      }
      if (harshBrakeCount > 0) {
        dynamicCons.push(`Ghi nhận ${harshBrakeCount} lần phanh gấp gắt.`);
      }
      if (distractedPct > 20) {
        dynamicCons.push(`🚨 CẢNH BÁO MẤT TẬP TRUNG: Tỷ lệ xao nhãng chiếm ${distractedPct.toFixed(1)}% thời gian.`);
      } else if (distractedPct > 5) {
        dynamicCons.push(`Xao nhãng khi lái xe chiếm ${distractedPct.toFixed(1)}% thời gian.`);
      }
      if (fatigueFrames > 0) {
        dynamicCons.push(`🚨 CẢNH BÁO VI NGỦ: Phát hiện ${fatigueFrames} sự kiện vi ngủ/ngáp.`);
      }

      if (dynamicCons.length === 0) {
        dynamicCons.push(`Cần tiếp tục duy trì và nâng cao chỉ số tập trung.`);
      }

      const dynamicEval = (distractedPct > 25 || fatigueFrames > 0 || safeScore < 60)
        ? `🛑 COACHING 24H: Tài xế ${driverName} vi phạm an toàn nghiêm trọng (Safety Score: ${safeScore.toFixed(0)}/100, Xao nhãng: ${distractedPct.toFixed(1)}%, Vi ngủ: ${fatigueFrames} lần), yêu cầu tạm đình chỉ chạy để đào tạo khẩn cấp.`
        : (distractedPct > 15 || safeScore < 80)
          ? `⚠️ NHẮC NHỞ: Tài xế ${driverName} cần chú ý giảm thiểu xao nhãng (${distractedPct.toFixed(1)}%) và giữ khoảng cách an toàn.`
          : `🏆 KHEN THƯỞNG: Tài xế ${driverName} là hình mẫu chuẩn an toàn để các tài xế khác học tập.`;

      mockTripInsights[tId] = {
        driver_name: driverName,
        safe_score: safeScore,
        dtc_code: dtcCode,
        pros: dynamicPros,
        cons: dynamicCons,
        evaluation: dynamicEval
      };

      mockVehicleDiagnostics.push({
        trip_id: tId,
        brake_wear_pct: harshBrakeCount * 8 > 100 ? 100 : harshBrakeCount * 8,
        tire_wear_pct: safeScore < 60 ? 80 : 30,
        odometer_km: 35000,
        engine_hours: 800,
        dtc_code: dtcCode,
        maintenance_status: safeScore < 60 ? "Cần kiểm tra ngay" : "Bình thường",
        parts_availability: "Sẵn có trong kho",
        estimated_cost_vnd: safeScore < 60 ? "3.500.000 VNĐ" : "1.500.000 VNĐ",
        estimated_downtime: "0.5 ngày"
      });
    });

    const atRiskTrip = vehicles.find((v) => ((v.trip_aggregate as any)?.safe_driving_score ?? 100) < 60);
    const riskId = atRiskTrip ? atRiskTrip.trip_id : (finalTripIds[0] || 'N/A');

    return {
      insight: mockInsight,
      fleet_insight: mockInsight,
      trip_insights: mockTripInsights,
      vehicle_diagnostics: mockVehicleDiagnostics,
      action_orders: {
        do_not_drive: atRiskTrip ? `Tạm dừng lưu hành xe ${riskId} để kiểm tra hệ thống phanh.` : `Không có xe nào trong danh sách [${finalTripIds.join(", ")}] thuộc diện dừng lưu hành khẩn cấp.`,
        priority_48h: `Bảo trì ưu tiên trong 48h cho các xe rủi ro: ${finalTripIds.join(", ")}.`,
        routine_maintenance: "Bảo dưỡng định kỳ chuẩn cho các xe an toàn."
      }
    };
  };

  if (!getBedrockBearerToken()) {
    res.json(generateFallbackReport());
    return;
  }

  try {
    let reportModeTag = "SAFETY_OVERVIEW";
    if (isMaintenanceReport && isSingleTrip) reportModeTag = "MAINTENANCE_DETAIL";
    else if (isMaintenanceReport && !isSingleTrip) reportModeTag = "MAINTENANCE_OVERVIEW";
    else if (!isMaintenanceReport && isSingleTrip) reportModeTag = "SAFETY_DETAIL";
    else reportModeTag = "SAFETY_OVERVIEW";

    let promptText = `
Bạn là AI Chuyên gia Phân tích An toàn & Bảo trì Đội xe (Fleet Safety & Maintenance Expert) của FPTU Automotive DMS.
Nhiệm vụ: Phân tích sâu dữ liệu telemetry được cung cấp và xuất Báo Cáo Đánh Giá chi tiết dựa trên REPORT_TYPE = "${reportModeTag}".

═══════════════════════════════════════════════════════════════
QUY TẮC BẮT BUỘC (STRICT RULES)
═══════════════════════════════════════════════════════════════
RULE-1 TRUNG THỰC: Mọi số liệu phải trích xuất trực tiếp từ [DATA]. Không bịa đặt sự kiện, mã lỗi, hay chi phí không có trong data.
RULE-2 LOGIC KHEN/PHẠT:
  - Safe Score >= 80 VÀ phanh gấp = 0 VÀ vi ngủ = 0 → CHỈ khen thưởng, KHÔNG đề xuất coaching/kỷ luật.
  - Safe Score < 60 HOẶC có vi ngủ/Near Miss → BẮT BUỘC coaching/đình chỉ. KHÔNG ĐƯỢC khen thưởng.
  - Xao nhãng > 20% → Rủi ro nghiêm trọng, bắt buộc vào diện 🛑 CRITICAL hoặc ⚠️ WATCH.
RULE-3 PHÂN TÁCH LĨNH VỰC: An toàn (hành vi người lái) và Bảo trì (máy móc vật lý) là 2 lĩnh vực hoàn toàn độc lập. Không đề xuất sửa chữa xe vì hành vi tài xế.
RULE-4 ĐỘ SÂU: Nghiêm cấm trả lời chung chung. Mỗi nhận xét phải có: (a) số liệu cụ thể, (b) giải thích nguyên nhân, (c) hành động đo lường được.
RULE-5 ĐỘ DÀI TỐI THIỂU: "fleet_insight" tối thiểu 200 từ, triển khai đủ 4 section. Mỗi trip_insights.pros/cons tối thiểu 2 mục.

═══════════════════════════════════════════════════════════════
BLUEPRINT CHO "fleet_insight" THEO REPORT_TYPE = "${reportModeTag}"
═══════════════════════════════════════════════════════════════

${reportModeTag === "SAFETY_DETAIL" ? `
=== [REPORT_TYPE] = "SAFETY_DETAIL" (Phân tích An toàn Chuyên sâu 1 chuyến đi: ${singleId}) ===
Mục tiêu: Giải phẫu toàn bộ hành vi lái xe 1 chuyến, tìm nguyên nhân gốc rễ mọi rủi ro.
Triển khai đúng 4 section (dùng ###):

### 1. Chỉ số cốt lõi (Core Metrics)
Trình bày dạng danh sách có dấu đầu dòng:
- Safe Score: X/100 + phân loại (SAFE ≥80 / WATCH 60-79 / CRITICAL <60)
- Tổng số frame phân tích & tổng sự kiện rủi ro
- Tỷ lệ xao nhãng % = distracted_frames / total_frames × 100
- Số lần phanh gấp (harsh_brake_count)
- Số sự kiện vi ngủ/ngáp (drowsy/yawning events)
- Chỉ số TTC tối thiểu (giây) nếu có trong data

### 2. Tái hiện dòng thời gian sự kiện (Event Timeline Analysis)
Liệt kê ít nhất 3 sự kiện quan trọng nhất theo thứ tự frame/giây:
- Mỗi sự kiện ghi rõ: thời điểm / trạng thái trước→sau / tốc độ xe / TTC / phản ứng hệ thống.
- Phân tích chuỗi nhân-quả giữa các sự kiện.

### 3. Nguyên nhân gốc rễ (Root-cause Analysis)
- Cơ chế cụ thể tại sao tỷ lệ xao nhãng cao (nếu có): thói quen điện thoại, mệt mỏi, hay môi trường đường?
- Định lượng tác động: xao nhãng X% → phản ứng chậm ~Y giây → quãng đường phanh dài hơn ~Z mét ở vận tốc V km/h.
- Chỉ rõ lỗ hổng quan sát dẫn đến phanh gấp.

### 4. Micro-Coaching Plan (Kế hoạch Can thiệp cá nhân)
Đưa ra 2-3 hành động cụ thể, đo lường được, chỉ đích danh ${singleId}:
- Không được nói "lái cẩn thận hơn". Phải chỉ rõ hành động (ví dụ: "Cấm dùng điện thoại khi vào khu vực giao lộ").
- Nếu có vi ngủ: bắt buộc đề nghị kiểm tra y tế + lịch nghỉ bắt buộc.
- Gắn KPI đo lường (ví dụ: "Mục tiêu: giảm xao nhãng xuống <10% trong 2 tuần tới").
` : ""}

${reportModeTag === "SAFETY_OVERVIEW" ? `
=== [REPORT_TYPE] = "SAFETY_OVERVIEW" (Đánh giá An toàn Toàn đội: ${finalTripIds.length} chuyến – ${finalTripIds.join(", ")}) ===
Mục tiêu: Vẽ bức tranh tổng thể an toàn fleet, phân nhóm rủi ro, đưa ra quyết định quản trị cấp ban lãnh đạo.
Triển khai đúng 4 section (dùng ###):

### 1. Bức tranh toàn cảnh (Fleet Safety Landscape)
- Điểm an toàn trung bình fleet (tổng safe_score / số chuyến) so với ngưỡng chuẩn 80/100.
- Phân bố điểm: bao nhiêu chuyến SAFE (>80) / WATCH (60-80) / CRITICAL (<60)?
- Tổng số sự kiện rủi ro toàn fleet & loại vi phạm phổ biến nhất.

### 2. Xếp hạng & Phân nhóm Tài xế (Driver Triage)
- 🔴 CRITICAL (Score <60 hoặc có vi ngủ): Nêu đích danh trip_id, driver_name, số liệu vi phạm, hành động bắt buộc.
- 🟡 WATCH (Score 60-79): Nêu tên, điểm yếu chính, lộ trình cải thiện có deadline.
- 🟢 SAFE (Score ≥80): Nêu tên, thành tích nổi bật, đề xuất khen thưởng.

### 3. Xu hướng Vi phạm cốt lõi (Fleet-level Pattern)
- Loại vi phạm nào chiếm tỷ lệ cao nhất? Dẫn số liệu thống kê (X/Y chuyến bị xao nhãng).
- Nguyên nhân hệ thống nếu nhiều tài xế cùng mắc 1 lỗi.

### 4. Quyết định Quản trị (Executive Action – dựa vào RULE-2)
- 🛑 NGAY LẬP TỨC (24h): Danh sách tài xế bị đình chỉ + lý do.
- ⚠️ TRONG 48H: Coaching bắt buộc.
- 🏆 KHEN THƯỞNG: Tài xế mẫu mực + hình thức.
` : ""}

${reportModeTag === "MAINTENANCE_DETAIL" ? `
=== [REPORT_TYPE] = "MAINTENANCE_DETAIL" (Khám bệnh Kỹ thuật Chuyên sâu 1 xe: ${singleId}) ===
Mục tiêu: Chẩn đoán toàn diện sức khỏe kỹ thuật, đưa ra lệnh bảo trì chính xác và dự toán chi phí.
TUYỆT ĐỐI không phân tích hành vi tài xế. Chỉ phân tích máy móc và dữ liệu vật lý.
Triển khai đúng 4 section (dùng ###):

### 1. Tổng quan Sức khỏe Phương tiện (Vehicle Health Overview)
Bảng trạng thái các hệ thống chính:
- Hệ thống phanh: MSI %, số lần rà phanh gắt, áp suất dầu phanh.
- Hệ thống động cơ: nhiệt độ vận hành, áp suất dầu, RPM bất thường.
- Hệ thống lốp: áp suất (bar), chỉ số mòn đều/lệch.
- Tổng km hiện tại & km còn lại đến mốc bảo dưỡng định kỳ.

### 2. Chẩn đoán Mã lỗi OBD-II (Diagnostic Trouble Codes)
- Liệt kê tất cả mã DTC phát sinh trong chuyến.
- Giải thích cơ chế gây ra lỗi và rủi ro nếu không xử lý.
- Tham chiếu: C0035=Cảm biến tốc độ bánh xe; P0300=Bỏ lửa đa xi-lanh; P0000=Không lỗi.

### 3. Dự báo Hỏng hóc & Khấu hao (Wear & Predictive Failure)
- Bộ phận nào đang có tốc độ mòn cao nhất?
- Xác suất hỏng hóc trong X ngày nếu không bảo trì.
- Hiệu ứng chuỗi: hỏng A → kéo theo hỏng B không?

### 4. Lệnh Bảo trì & Dự toán Chi phí (Maintenance Order & Cost)
- Phân loại: DO_NOT_DRIVE / PRIORITY_48H / ROUTINE.
- Chi phí tham chiếu: C0035 = 1.5-3M VNĐ; P0300 = 2.5-4.5M VNĐ; P0000 routine = 1.5-2.5M VNĐ.
- Tổng dự toán và thứ tự ưu tiên sửa chữa.
` : ""}

${reportModeTag === "MAINTENANCE_OVERVIEW" ? `
=== [REPORT_TYPE] = "MAINTENANCE_OVERVIEW" (Chiến lược Bảo trì & TCO Toàn đội: ${finalTripIds.length} xe – ${finalTripIds.join(", ")}) ===
Mục tiêu: Tối ưu hóa chi phí TCO và xây dựng lịch bảo trì dự báo cho cả hạm đội.
TUYỆT ĐỐI không phân tích hành vi tài xế.
Triển khai đúng 4 section (dùng ###):

### 1. Đánh giá Sức khỏe Hạm đội (Fleet Health Assessment)
- Tỷ lệ xe hoạt động tốt / cần bảo trì / nguy hiểm (X/tổng số xe).
- Thống kê tổng số DTC theo loại (C0035 / P0300 / P0000) trên toàn fleet.
- Chỉ số mòn phanh & lốp trung bình fleet.

### 2. Triage Bảo trì theo Ưu tiên (Maintenance Triage)
- 🛑 CRITICAL (thu hồi ngay): Xe, mã lỗi, rủi ro giao thông cụ thể.
- ⚠️ SCHEDULED (bảo dưỡng định kỳ trong 2 tuần): Xe và km còn lại đến mốc.
- ✅ HEALTHY (tiếp tục lưu hành): Xe đang vận hành tốt.

### 3. Dự báo Hỏng hóc & Xu hướng Khấu hao (Predictive Trends)
- Bộ phận nào đang mòn nhanh nhất toàn fleet?
- Dự báo số xe sẽ vào CRITICAL trong 30 ngày tới.
- Tồn kho phụ tùng khuyến nghị cần chuẩn bị sẵn.

### 4. Ngân sách & ROI Bảo trì (Budget & Maintenance ROI)
- Tổng dự toán ngân sách toàn fleet (chi tiết từng nhóm xe).
- So sánh chi phí phòng ngừa vs chi phí hỏng hóc nặng nếu bỏ qua.
- Lịch bảo dưỡng rolling (xe nào vào xưởng tuần nào) để tối thiểu hóa downtime.
` : ""}

═══════════════════════════════════════════════════════════════
OUTPUT SCHEMA (JSON THUẦN TÚY – KHÔNG markdown codeblock – KHÔNG text ngoài JSON)
═══════════════════════════════════════════════════════════════
Trả về JSON với đúng cấu trúc sau. Mô tả dưới đây là kiểu dữ liệu & yêu cầu, KHÔNG phải giá trị mẫu để sao chép:
{
  "fleet_insight": "<string – toàn bộ nội dung 4 section theo blueprint trên, dùng \\n để xuống dòng, tối thiểu 200 từ>",
  "trip_insights": {
    "<trip_id thực từ data>": {
      "driver_name": "<tên tài xế từ metadata.driver_profile hoặc trip_id>",
      "safe_score": <number – lấy từ trip_aggregate.safe_driving_score, không bịa>,
      "dtc_code": "<C0035 nếu harsh_brake>=10 | P0300 nếu safe_score<60 | P0000 nếu bình thường>",
      "pros": [
        "<Điểm mạnh 1: nêu chỉ số cụ thể (ví dụ: '0 lần phanh gấp trong X km') + giải thích tại sao đây là điểm mạnh>",
        "<Điểm mạnh 2 nếu có>"
      ],
      "cons": [
        "<Điểm yếu 1: số liệu thực (ví dụ: 'xao nhãng 35.2% > ngưỡng an toàn 10%') + hệ quả là gì>",
        "<Điểm yếu 2 nếu có>"
      ],
      "evaluation": "<theo RULE-2: 🏆 KHEN THƯỞNG / ⚠️ NHẮC NHỞ / 🛑 COACHING 24H – kèm hành động đo lường được, chỉ đích danh tài xế này>"
    }
  },
  "vehicle_diagnostics": [
    {
      "trip_id": "<trip_id thực>",
      "brake_wear_pct": <harsh_brake_count * 8, tối đa 100>,
      "tire_wear_pct": <80 nếu safe_score<60, 30 nếu bình thường>,
      "odometer_km": <từ trip_aggregate nếu có, mặc định 35000>,
      "engine_hours": <từ trip_aggregate nếu có, mặc định 800>,
      "dtc_code": "<mã lỗi thực tế>",
      "maintenance_status": "<Cần kiểm tra ngay | Bảo dưỡng định kỳ | Bình thường>",
      "parts_availability": "Sẵn có trong kho",
      "estimated_cost_vnd": "<dự toán VNĐ theo dtc_code và mức mòn>",
      "estimated_downtime": "<thời gian nằm xưởng ước tính>"
    }
  ],
  "action_orders": {
    "do_not_drive": "${reportModeTag === 'SAFETY_DETAIL' ? `<CHỈ về tài xế ${singleId}: nếu safe_score < 60 HOẶC vi ngủ → lệnh Coaching 24H bắt buộc + đình chỉ lưu hành. Nếu an toàn → ghi Tài xế ${singleId} không thuộc diện đình chỉ khẩn cấp>` : reportModeTag === 'SAFETY_OVERVIEW' ? '<SAFETY OVERVIEW – liệt kê đích danh driver_name/trip_id các tài xế score < 60 hoặc vi ngủ cần Coaching 24H + đình chỉ. Nếu không có → ghi rõ>' : reportModeTag === 'MAINTENANCE_DETAIL' ? `<CHỈ về xe ${singleId}: nếu DTC = C0035/P0300 HOẶC brake_wear > 75% → lệnh Dừng Lưu Hành (Do Not Drive) khẩn cấp. Nếu ổn → ghi Xe ${singleId} không thuộc diện dừng khẩn cấp>` : '<MAINTENANCE OVERVIEW – liệt kê đích danh trip_id các xe có DTC nghiêm trọng (C0035/P0300) hoặc brake_wear > 75%. Thu hồi về xưởng ngay>'}",
    "priority_48h": "${reportModeTag === 'SAFETY_DETAIL' ? `<CHỈ về tài xế ${singleId}: nếu safe_score 60-79 HOẶC xao nhãng > 15% → Nhắc Nhở Kỷ Luật Vận Hành trong 48h với hành động cụ thể. Nếu không cần → ghi Không cần can thiệp 48h cho ${singleId}>` : reportModeTag === 'SAFETY_OVERVIEW' ? '<SAFETY OVERVIEW – liệt kê đích danh driver_name/trip_id các tài xế score 60-79 hoặc xao nhãng 15-30% cần Nhắc Nhở Kỷ Luật Vận Hành trong 48h>' : reportModeTag === 'MAINTENANCE_DETAIL' ? `<CHỈ về xe ${singleId}: nếu có C0035 HOẶC brake_wear 50-75% → Bảo Trì Ưu Tiên trong 48h (kiểm tra cảm biến tốc độ bánh xe, cân chỉnh lốp). Dự toán chi phí cụ thể>` : '<MAINTENANCE OVERVIEW – liệt kê trip_id các xe cần bảo trì ưu tiên trong 48h (C0035 hoặc brake_wear 50-75%). Hạng mục kiểm tra + dự toán chi phí>'}",
    "routine_maintenance": "${reportModeTag === 'SAFETY_DETAIL' ? `<CHỈ về tài xế ${singleId}: nếu safe_score >= 80 VÀ không vi phạm → Khen Thưởng Tài Xế Mẫu Mực. Hình thức: vinh danh Safe Driver tháng, ghi nhận thành tích cụ thể>` : reportModeTag === 'SAFETY_OVERVIEW' ? '<SAFETY OVERVIEW – liệt kê đích danh driver_name/trip_id các tài xế mẫu mực (score >= 80, xao nhãng < 10%, phanh gấp = 0). Đề xuất vinh danh Safe Driver tháng + hình thức khen>' : reportModeTag === 'MAINTENANCE_DETAIL' ? `<CHỈ về xe ${singleId}: nếu P0000 (không lỗi) VÀ brake_wear < 50% → Bảo Dưỡng Định Kỳ Chuẩn (thay dầu, lọc gió, kiểm tra áp suất lốp). Dự toán chi phí định kỳ>` : '<MAINTENANCE OVERVIEW – liệt kê trip_id các xe healthy (P0000, brake_wear < 50%). Lịch bảo dưỡng định kỳ rolling>'}"
  }
}
`;
    promptText += `

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
    res.json(generateFallbackReport());
  }
});

// ── Intervention Command Proxy ──────────────────────────────────────────────
// The React Fleet Dashboard POSTs here; this proxy forwards to the Python
// FastAPI backend so the AI desktop app can poll and render the overlay.
const PYTHON_BE = process.env.VITE_ALERTS_HTTP_URL?.replace("/api/v1/alerts", "") || "http://127.0.0.1:8000";

app.post("/api/intervention", async (req, res) => {
  try {
    const { type, tripId, message, timestamp } = req.body as {
      type: string;
      tripId: string;
      message: string;
      timestamp: number;
    };
    if (!type || !tripId || !message) {
      res.status(400).json({ error: "Missing required fields: type, tripId, message" });
      return;
    }
    const response = await fetch(`${PYTHON_BE}/api/v1/alerts/interventions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type,
        trip_id: tripId,
        message,
        timestamp_ms: timestamp || Date.now(),
      }),
      signal: AbortSignal.timeout(3000),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      console.warn(`[intervention] Python BE returned ${response.status}:`, data);
    }
    res.status(response.ok ? 202 : response.status).json(data);
  } catch (err) {
    console.warn("[intervention] Python BE offline; command was not delivered:", err);
    res.status(503).json({
      accepted: false,
      error: "Python AI backend is offline; intervention command was not delivered",
    });
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
