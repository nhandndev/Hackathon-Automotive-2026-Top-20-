import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

app.use(express.json());

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
  const { message, chatHistory } = req.body;

  if (!message || typeof message !== "string") {
    res.status(400).json({ error: "Thông điệp không hợp lệ" });
    return;
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

  // Smart fallback response if API key is not present or API call fails
  const lowerMsg = message.toLowerCase();
  let fallbackReply = "";

  if (lowerMsg.includes("vi ngủ") || lowerMsg.includes("ngủ nhiều") || lowerMsg.includes("tài xế a")) {
    fallbackReply = `**Tài xế A (Xe VH-04) đang có rủi ro cao nhất — Safe Score 42/100**\n\n- 2 lần vi ngủ (microsleep)\n- TTC thấp nhất: 1.2s\n- Khung giờ vi phạm: 2h-4h sáng\n\nTài xế A sụt điểm do 2 khoảnh khắc vi ngủ nguy hiểm vào khung 2h-4h sáng, dẫn đến phanh gấp liên tiếp. Mức độ tỉnh táo giảm xuống dưới 15% trong giai đoạn này. Khuyến nghị can thiệp cho nghỉ 30 phút.`;
  } else if (lowerMsg.includes("bảo trì") || lowerMsg.includes("xe nào")) {
    fallbackReply = `**KHUYẾN NGHỊ BẢO TRÌ & LỊCH TRÌNH:**\n\n1. **Xe VH-04 (Tài xế A):** Cần điều chỉnh ngay lịch trình, tránh chạy liên tục quá 4 tiếng vào ban đêm.\n2. **Xe VH-08:** Phát hiện 24 lần phanh gấp trong tuần này. Cần kiểm tra má phanh và đĩa phanh trước chuyến đi tiếp theo (dự kiến mòn phanh tăng 15%).\n3. **Xe VH-05:** Thời gian chạy không tải (Idle) đạt 4.2h - cần nhắc nhở tắt máy để tiết kiệm nhiên liệu.`;
  } else if (lowerMsg.includes("so sánh") || lowerMsg.includes("tài xế b")) {
    fallbackReply = `**So sánh Tài xế A vs Tài xế B:**\n\n- **Tài xế A (ID: 8842 - VH-04):** Điểm an toàn 42/100. Vi phạm chính: Vi ngủ x2, Phanh gấp x1, Dùng điện thoại x1.\n- **Tài xế B (ID: 9102 - VH-01):** Điểm an toàn 68.2/100. Vi phạm chính: Ngáp liên tục (x4), Mức độ tỉnh táo 38%.\n\n-> Cả 2 tài xế đều thể hiện dấu hiệu kiệt sức trong ca đêm, cần phân công tài xế phụ.`;
  } else {
    fallbackReply = `Hệ thống Fleet AI Copilot đã ghi nhận yêu cầu: "${message}". Dựa trên phân tích telemetry thời gian thực, đội xe có 1 phương tiện (VH-04) ở mức Báo động đỏ CRITICAL và 1 phương tiện (VH-01) ở mức Cảnh báo HIGH. Bạn có muốn thực hiện lệnh can thiệp gửi thông báo đến cabin xe VH-04 không?`;
  }

  res.json({ reply: fallbackReply });
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

  app.listen(PORT, "localhost", () => {
    console.log(`Server is running on http://localhost:${PORT}`);
  });
}

startServer();
