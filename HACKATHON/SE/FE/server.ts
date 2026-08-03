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
      const prompt = `
Bạn là Fleet AI Copilot cho FPTU DMS Vision.
Nhiệm vụ: tạo lời mở đầu ngắn gọn cho report ${reportRequest.type}.
Không bịa field mới. Chỉ dựa trên trip_id, metadata, driver_summary, trip_aggregate.
Trả lời tiếng Việt, 2-3 câu, chuyên nghiệp.

User request: ${message}
Selected trip_ids: ${selectedTripIds.join(", ")}
Trip context:
${buildTripContext(vehicles.filter((vehicle) => selectedTripIds.includes(vehicle.trip_id)))}
`;
      const aiReply = await callBedrockConverse(prompt);
      res.json({
        reply: "",
        cardType: "COMPARISON",
        cardData: {
          title: reportRequest.type === "compare"
            ? `Đã tạo báo cáo so sánh ${selectedTripIds.length} tài xế`
            : reportRequest.type === "maintenance"
              ? "Đã tạo báo cáo xe cần bảo trì"
              : "Đã tạo báo cáo an toàn fleet",
          details: aiReply || "AI Copilot đã tổng hợp dữ liệu fleet để tạo report chi tiết.",
          functionName: reportRequest.type === "compare"
            ? "create_driver_comparison_report"
            : reportRequest.type === "maintenance"
              ? "create_maintenance_priority_report"
              : "create_fleet_safety_report",
          reportType: reportRequest.type,
          count: selectedTripIds.length,
          tripIds: selectedTripIds,
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
  const { reportType, tripIds, rows, vehicles = [] } = req.body as {
    reportType?: string;
    tripIds?: string[];
    rows?: unknown[];
    vehicles?: TripSummary[];
  };

  if (!getBedrockBearerToken()) {
    res.status(503).json({ error: "AWS_BEARER_TOKEN_BEDROCK is not configured" });
    return;
  }

  try {
    const insight = await callBedrockConverse(`
Bạn là Fleet AI Copilot Insight cho dashboard quản lý đội xe.
Hãy phân tích report ${reportType || "compare"} cho các trip: ${(tripIds || []).join(", ")}.

Yêu cầu nội dung:
- So sánh các driver/trip với nhau.
- Nêu ưu điểm và nhược điểm từng tài xế.
- Chỉ ra tài xế tốt nhất và tài xế cần coaching trước.
- Giải thích dựa trên Safety Score, risk.final_risk_score, driver.state, driver.alertness_score, min_ttc, headway_sec, behavior_flags nếu có.
- Viết tiếng Việt, giọng chuyên nghiệp, phù hợp business report.
- Không nói "mock", không bịa field mới.

Ranking rows:
${JSON.stringify(rows || [], null, 2)}

Trip context:
${buildTripContext(vehicles)}
`);
    res.json({ insight });
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
