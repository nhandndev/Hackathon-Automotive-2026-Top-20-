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
  frames?: unknown[];
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
              frames: parsed.frames,
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

  // Saved JSON files often contain the full frame-level local AI output.
  for (const v of savedVehicles) {
    if (v && v.trip_id) {
      mergedMap.set(v.trip_id, { ...v, runtime_status: "completed" });
    }
  }

  // Only include incoming vehicles if their runtime_status is explicitly 'completed'
  for (const v of incomingVehicles) {
    if (v && v.trip_id && v.runtime_status === "completed") {
      const saved = mergedMap.get(v.trip_id);
      mergedMap.set(v.trip_id, {
        ...saved,
        ...v,
        metadata: v.metadata ?? saved?.metadata,
        driver_summary: v.driver_summary ?? saved?.driver_summary,
        trip_aggregate: v.trip_aggregate ?? saved?.trip_aggregate,
        frames: v.frames ?? saved?.frames,
      });
    }
  }

  return Array.from(mergedMap.values());
}

type ChatHistoryItem = { sender: string; text: string };

type CopilotReportType = "compare" | "maintenance" | "safety";
type ReportMode = "safety_detail" | "safety_overview" | "maintenance_detail" | "maintenance_overview";

type CopilotTripInput = {
  tripId: string;
  driverName: string;
  rank: number;
  safety: {
    score: number;
    riskLevel: string;
    avgRisk?: number;
    maxRisk: number;
    highRiskFrames?: number;
    distractedPct: number;
    fatigueEvents: number;
    speedingPct: number;
    tailgatingPct: number;
    nearMissCount: number;
    harshBrakeCount: number;
    safetyAction: string;
  };
  eventSummary: { safe: number; warning: number; danger: number; total: number };
  events: unknown[];
  maintenance: {
    brakeStress: number;
    tireStress: number;
    priority: string;
    dtcCode: string;
    estimatedCostVnd: number;
    estimatedDowntime: string;
    workOrderStatus: string;
  };
};

type CopilotInsightPayload = {
  insight: string;
  fleet_insight: string;
  trip_insights: Record<string, unknown>;
  policy_version: string;
  ai_status: "validated" | "unavailable" | "pending";
  diagnostics?: {
    provider: "bedrock";
    region: string;
    modelId: string;
    durationMs?: number;
    promptBytes?: number;
    cache?: "hit" | "miss" | "inflight";
    reason?: string;
  };
};

const reportInsightCache = new Map<string, { expiresAt: number; payload: CopilotInsightPayload }>();
const reportInsightInflight = new Map<string, Promise<CopilotInsightPayload>>();
const REPORT_INSIGHT_CACHE_TTL_MS = 5 * 60 * 1000;
const REPORT_UNAVAILABLE_CACHE_TTL_MS = 30 * 1000;

function compactTripForBedrock(trip: CopilotTripInput, mode?: string) {
  if (mode?.startsWith("safety")) {
    return {
      tripId: trip.tripId,
      driverName: trip.driverName,
      rank: trip.rank,
      safety: trip.safety,
      eventSummary: trip.eventSummary,
      forbiddenIfZero: {
        harshBrake: trip.safety.harshBrakeCount === 0 ? "Do not mention harsh brake/phanh gap as a problem." : undefined,
        nearMiss: trip.safety.nearMissCount === 0 ? "Do not mention near miss/TTC thấp as a problem." : undefined,
        fatigue: trip.safety.fatigueEvents === 0 ? "Do not mention fatigue/microsleep/vi ngu as a problem." : undefined,
        distracted: trip.safety.distractedPct === 0 ? "Do not mention distracted/xao nhang/phan tam as a problem." : undefined,
        speeding: trip.safety.speedingPct === 0 ? "Do not mention speeding/qua toc as a problem." : undefined,
        tailgating: trip.safety.tailgatingPct === 0 ? "Do not mention tailgating/bam duoi as a problem." : undefined,
      },
    };
  }
  return {
    tripId: trip.tripId,
    driverName: trip.driverName,
    rank: trip.rank,
    safety: trip.safety,
    eventSummary: trip.eventSummary,
    maintenance: trip.maintenance,
  };
}

function textFromInsight(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(textFromInsight).join("\n");
  if (value && typeof value === "object") return Object.values(value).map(textFromInsight).join("\n");
  return "";
}

function hasPositiveMention(text: string, pattern: RegExp, negativePattern?: RegExp) {
  return pattern.test(text) && !(negativePattern && negativePattern.test(text));
}

function validateBedrockInsight(parsed: any, trips: CopilotTripInput[], mode?: string) {
  const fullText = textFromInsight(parsed).toLowerCase();
  if (!String(parsed?.fleet_insight || "").trim()) throw new Error("Bedrock returned no fleet_insight");

  if (mode?.startsWith("safety")) {
    const maintenanceLeak = /(bảo trì|bao tri|lốp|lop|tire|dtc|chi phí|chi phi|downtime|phụ tùng|phu tung|work order|brake stress|tire stress|inspect)/i;
    if (maintenanceLeak.test(fullText)) {
      throw new Error("Bedrock safety insight mentioned maintenance-only fields");
    }
  }

  for (const trip of trips) {
    const tripText = textFromInsight(parsed?.trip_insights?.[trip.tripId]).toLowerCase();
    if (!tripText) continue;
    const checks: Array<[boolean, RegExp, RegExp | undefined, string]> = [
      [trip.safety.harshBrakeCount === 0, /(phanh|brake|harsh brake)/i, /(không|khong|no)[^.]{0,40}(phanh|brake|harsh brake)/i, "harsh brake is zero"],
      [trip.safety.nearMissCount === 0, /(near miss|ttc thấp|ttc thap|suýt va|suyt va)/i, /(không|khong|no)[^.]{0,40}(near miss|ttc|suýt va|suyt va)/i, "near miss is zero"],
      [trip.safety.fatigueEvents === 0, /(mệt mỏi|met moi|vi ngủ|vi ngu|microsleep|fatigue|drowsy|yawning)/i, /(không|khong|no)[^.]{0,40}(mệt|met|vi ngủ|vi ngu|microsleep|fatigue|drowsy|yawning)/i, "fatigue is zero"],
      [trip.safety.distractedPct === 0, /(xao nhãng|xao nhang|phân tâm|phan tam|distract)/i, /(không|khong|no)[^.]{0,40}(xao nhãng|xao nhang|phân tâm|phan tam|distract)/i, "distracted is zero"],
      [trip.safety.speedingPct === 0, /(quá tốc|qua toc|vượt tốc|vuot toc|speeding)/i, /(không|khong|no)[^.]{0,40}(quá tốc|qua toc|vượt tốc|vuot toc|speeding)/i, "speeding is zero"],
      [trip.safety.tailgatingPct === 0, /(bám đuôi|bam duoi|tailgating)/i, /(không|khong|no)[^.]{0,40}(bám đuôi|bam duoi|tailgating)/i, "tailgating is zero"],
    ];
    for (const [shouldCheck, pattern, negativePattern, reason] of checks) {
      if (shouldCheck && hasPositiveMention(tripText, pattern, negativePattern)) {
        throw new Error(`Bedrock contradicted ${trip.tripId}: ${reason}`);
      }
    }
  }
}

function buildUnavailableInsight(reason: string, diagnostics?: Partial<CopilotInsightPayload["diagnostics"]>): CopilotInsightPayload {
  return {
    insight: "AI Copilot chưa có phản hồi Bedrock hợp lệ. Không hiển thị insight giả.",
    fleet_insight: "AI Copilot chưa có phản hồi Bedrock hợp lệ. Không hiển thị insight giả.",
    trip_insights: {},
    policy_version: "report-canonical-v1",
    ai_status: "unavailable",
    diagnostics: {
      provider: "bedrock",
      region: BEDROCK_REGION,
      modelId: BEDROCK_MODEL_ID,
      reason,
      ...diagnostics,
    },
  };
}

function buildPendingInsight(diagnostics?: Partial<CopilotInsightPayload["diagnostics"]>): CopilotInsightPayload {
  return {
    insight: "AI Copilot đang chờ Bedrock phản hồi hợp lệ. Không hiển thị insight giả.",
    fleet_insight: "AI Copilot đang chờ Bedrock phản hồi hợp lệ. Không hiển thị insight giả.",
    trip_insights: {},
    policy_version: "report-canonical-v1",
    ai_status: "pending",
    diagnostics: {
      provider: "bedrock",
      region: BEDROCK_REGION,
      modelId: BEDROCK_MODEL_ID,
      reason: "background-inflight",
      ...diagnostics,
    },
  };
}

const BEDROCK_REGION = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || "ap-southeast-2";
const BEDROCK_MODEL_ID = process.env.BEDROCK_MODEL_ID || "deepseek.v3.2";

function cleanBearerToken(raw?: string): string {
  return (raw || "").replace(/\n/g, "").replace(/ /g, "").trim();
}

function getBedrockBearerToken(): string {
  return cleanBearerToken(process.env.AWS_BEARER_TOKEN_BEDROCK || process.env.BEDROCK_API_KEY);
}

async function callBedrockConverse(prompt: string, modelId = BEDROCK_MODEL_ID, timeoutMs = 3500): Promise<string> {
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
    signal: AbortSignal.timeout(timeoutMs),
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

const finiteNumber = (value: unknown, fallback = 0) =>
  typeof value === "number" && Number.isFinite(value) ? value : fallback;

const pct = (count: number, total: number) => total > 0 ? (count / total) * 100 : 0;

const clampScore = (value: number, min = 0, max = 100) => Math.min(Math.max(value, min), max);

const isFatigueState = (state?: string) => (
  state === "drowsy" || state === "yawning" || state === "microsleep"
);

const lowTtcFrame = (frame: any) => {
  const value = finiteNumber(frame?.min_ttc, Number.POSITIVE_INFINITY);
  return value > 0 && value <= 2.5;
};

const riskLabelForScore = (score: number) => {
  if (score < 45) return "CRITICAL";
  if (score < 65) return "AT_RISK";
  if (score < 82) return "WATCH";
  return "SAFE";
};

function buildCopilotRankingRow(v: TripSummary) {
  const frames = Array.isArray(v.frames) ? v.frames as any[] : [];
  const totalFrames = frames.length;
  const aggregate = v.trip_aggregate as any;
  const driverSummary = v.driver_summary as any;
  const risks = frames.map((frame) => finiteNumber(frame?.risk?.final_risk_score));
  const avgRisk = totalFrames
    ? risks.reduce((sum, value) => sum + value, 0) / totalFrames
    : finiteNumber(aggregate?.avg_risk_score);
  const maxRisk = totalFrames
    ? risks.reduce((max, value) => Math.max(max, value), 0)
    : finiteNumber(aggregate?.max_risk_score);

  const distractedPct = totalFrames
    ? pct(frames.filter((frame) => frame?.driver?.state === "distracted").length, totalFrames)
    : finiteNumber(driverSummary?.state_distribution_pct?.distracted);
  const speedingPct = totalFrames
    ? pct(frames.filter((frame) => frame?.behavior_flags?.speeding).length, totalFrames)
    : finiteNumber(aggregate?.speeding_pct_time);
  const tailgatingPct = totalFrames
    ? pct(frames.filter((frame) => frame?.behavior_flags?.tailgating).length, totalFrames)
    : finiteNumber(aggregate?.tailgating_pct_time);
  const fatigueEvents = totalFrames
    ? frames.filter((frame) => isFatigueState(frame?.driver?.state)).length
    : finiteNumber(driverSummary?.microsleep_count);
  const nearMissCount = totalFrames
    ? frames.filter(lowTtcFrame).length
    : finiteNumber(aggregate?.near_miss_count);

  let harshBraking = 0;
  let lastHarshTs = -999;
  for (const frame of frames) {
    if (frame?.behavior_flags?.harsh_brake) {
      const ts = finiteNumber(frame?.timestamp);
      if (ts - lastHarshTs >= 3) {
        harshBraking += 1;
        lastHarshTs = ts;
      }
    }
  }
  if (!totalFrames) {
    harshBraking = finiteNumber(aggregate?.harsh_brake_count)
      + finiteNumber(aggregate?.harsh_accel_count)
      + finiteNumber(aggregate?.harsh_corner_count);
  }

  const criticalEvents = totalFrames
    ? frames.filter((frame) => finiteNumber(frame?.risk?.final_risk_score) >= 80 || lowTtcFrame(frame)).length
    : maxRisk >= 80 ? 1 : 0;
  const criticalEventPct = pct(criticalEvents, totalFrames);
  const harshEventPct = pct(harshBraking, totalFrames);
  const fatigueEventPct = pct(fatigueEvents, totalFrames);
  const nearMissPct = pct(nearMissCount, totalFrames);

  const rankingScore = clampScore(100
    - (avgRisk * 0.45)
    - (maxRisk * 0.20)
    - (criticalEventPct * 0.15)
    - (distractedPct * 0.10)
    - (fatigueEventPct * 0.05)
    - (speedingPct * 0.03)
    - (tailgatingPct * 0.04)
    - (harshEventPct * 0.03)
    - (nearMissPct * 0.05));
  const dtcCodes = aggregate?.dtc_codes;
  const dtcCode = Array.isArray(dtcCodes) && dtcCodes.length > 0 ? dtcCodes.join(", ") : "N/A";
  const maintenancePriority = rankingScore < 45 || maxRisk >= 95 || harshBraking >= 10
    ? "CRITICAL"
    : rankingScore < 65 || maxRisk >= 75 || harshBraking > 0
      ? "HIGH"
      : "ROUTINE";

  return {
    trip_id: v.trip_id,
    driverName: v.metadata?.driver_profile ?? driverSummary?.subject_id ?? "N/A",
    safeScore: Number(rankingScore.toFixed(1)),
    rankingScore: Number(rankingScore.toFixed(1)),
    riskLevel: riskLabelForScore(rankingScore),
    maxRisk: Number(maxRisk.toFixed(1)),
    avgRisk: Number(avgRisk.toFixed(1)),
    criticalEventPct: Number(criticalEventPct.toFixed(1)),
    distractedPct: Number(distractedPct.toFixed(1)),
    fatigueEvents,
    nearMissCount,
    harshBraking,
    dtcCode,
    maintenancePriority,
  };
}

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
Chỉ dùng dữ liệu có trong Trip context từ Dashboard.
Không được bịa trip_id, tài xế, score, DTC, chi phí, phụ tùng, work order hoặc timeline.
Nếu thiếu dữ liệu, nói rõ là chưa có dữ liệu.
Bạn chỉ diễn giải và khuyến nghị bằng tiếng Việt chuyên nghiệp; số liệu authoritative thuộc JSON/local AI telemetry.
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

    const rankedDrivers = selectedVehicles
      .map(buildCopilotRankingRow)
      .sort((a, b) => isMaintenance
        ? (a.safeScore - b.safeScore) || (b.maxRisk - a.maxRisk)
        : (b.safeScore - a.safeScore) || (a.avgRisk - b.avgRisk) || (a.maxRisk - b.maxRisk) || (a.criticalEventPct - b.criticalEventPct));

    const finalTripIds = rankedDrivers.map(d => d.trip_id);
    const criticalCount = rankedDrivers.filter((driver) => driver.safeScore < 45 || driver.maxRisk >= 95).length;
    const allCritical = rankedDrivers.length > 0 && criticalCount === rankedDrivers.length;

    try {
      const prompt = isMaintenance
        ? `
Bạn là Fleet Maintenance AI Copilot cho FPTU DMS Vision.
Nhiệm vụ: tạo lời mở đầu ngắn gọn cho BÁO CÁO ƯU TIÊN BẢO TRÌ TELEMETRY ĐỘI XE.
Ghi rõ: Báo cáo đã sắp xếp TOÀN BỘ ${rankedDrivers.length} xe theo telemetry JSON/local AI, từ ưu tiên cao đến thấp: ${rankedDrivers.map(d => `Xe ${d.trip_id} (${d.driverName} - Score: ${d.safeScore}/100, Max risk: ${d.maxRisk}/100, Harsh brake: ${d.harshBraking}, DTC: ${d.dtcCode})`).join(", ")}.
Không được bịa mã DTC, chi phí, phụ tùng hoặc work order nếu không có trong JSON.
Trả lời tiếng Việt, 2-3 câu ngắn gọn, chuyên nghiệp.

User request: ${message}
`
        : `
Bạn là Fleet AI Copilot cho FPTU DMS Vision.
Nhiệm vụ: tạo lời mở đầu ngắn gọn cho BÁO CÁO AN TOÀN ĐỘI XE.
Ghi rõ: Báo cáo đã sắp xếp TOÀN BỘ ${rankedDrivers.length} chuyến đi theo điểm an toàn Ranking Score từ JSON/local AI risk và behavior fields. ${allCritical ? "Tất cả chuyến đều thuộc nhóm nguy hiểm/rủi ro cao; không được gọi là an toàn tuyệt đối." : "Nếu có chuyến an toàn hơn, chỉ nói là tương đối an toàn hơn trong nhóm."} Danh sách: ${rankedDrivers.map(d => `${d.trip_id} (${d.safeScore}/100, avg risk ${d.avgRisk}/100, max risk ${d.maxRisk}/100, ${d.riskLevel})`).join(", ")}.
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
            ? "AI Copilot đã diễn giải telemetry JSON/local AI; DTC chỉ hiển thị khi có dữ liệu thật."
            : allCritical
              ? "Tất cả trip trong JSON/local AI đang thuộc nhóm rủi ro cao; danh sách vẫn xếp theo điểm an toàn Ranking Score từ cao xuống thấp."
              : "AI Copilot đã diễn giải danh sách trip theo điểm an toàn Ranking Score từ JSON/local AI."),
          sortRule: isMaintenance
            ? "Sắp xếp: Mức độ ưu tiên bảo trì từ CAO ➔ THẤP (Xe hỏng hóc/rủi ro cao xếp trước)"
            : allCritical
              ? "Xếp hạng theo điểm an toàn Ranking Score từ CAO ➔ THẤP; Avg Risk/Max Risk dùng để audit"
              : "Xếp hạng theo điểm an toàn Ranking Score từ CAO ➔ THẤP",
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
            ? "Đang chờ AI Copilot/Bedrock diễn giải. Card chỉ dùng telemetry JSON/local AI; không hiển thị DTC giả."
            : allCritical
              ? "Đang chờ AI Copilot/Bedrock diễn giải. Tất cả trip trong JSON/local AI đang ở nhóm rủi ro cao; list vẫn xếp theo điểm an toàn Ranking Score."
              : "Đang chờ AI Copilot/Bedrock diễn giải. Card chỉ dùng telemetry JSON/local AI; không hiển thị dữ liệu giả."),
          sortRule: isMaintenance
            ? "Sắp xếp: Mức độ ưu tiên bảo trì từ CAO ➔ THẤP (Xe hỏng hóc/rủi ro cao xếp trước)"
            : allCritical
              ? "Xếp hạng theo điểm an toàn Ranking Score từ CAO ➔ THẤP; Avg Risk/Max Risk dùng để audit"
              : "Xếp hạng theo điểm an toàn Ranking Score từ CAO ➔ THẤP",
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

  const replyFallback = [
    "AI Copilot chưa có phản hồi hợp lệ từ Bedrock/Gemini.",
    "Không hiển thị nhận xét thay thế hoặc số liệu giả.",
    `Dashboard hiện có ${vehicles.length} trip completed từ JSON/local AI: ${availableTripIds(vehicles).join(", ") || "chưa có"}.`,
    "Bạn có thể mở report card để xem số liệu deterministic từ JSON/local AI; phần insight sẽ chờ AI provider phản hồi.",
  ].join("\n");

  res.json({ reply: replyFallback });
});

app.post("/api/copilot/report", async (req, res) => {
  const { reportMode, canonicalInput, tripIds = [] } = req.body as {
    reportMode?: string;
    canonicalInput?: {
      request_id?: string;
      policy_version?: string;
      input_signature?: string;
      trips?: CopilotTripInput[];
    };
    tripIds?: string[];
  };

  const trips = (canonicalInput?.trips ?? []).filter((trip) => trip && trip.tripId);
  const startedAt = Date.now();
  if (trips.length === 0) {
    res.json({
      insight: "Chưa có canonical JSON/local AI input để lập AI Copilot insight.",
      fleet_insight: "Chưa có canonical JSON/local AI input để lập AI Copilot insight.",
      trip_insights: {},
      policy_version: "report-canonical-v1",
      ai_status: "unavailable",
    });
    return;
  }

  const cacheKey = canonicalInput?.input_signature || `${reportMode || "unknown"}:${trips.map((trip) => trip.tripId).join(",")}`;
  const cached = reportInsightCache.get(cacheKey);
  if (cached && cached.expiresAt > Date.now()) {
    res.json({
      ...cached.payload,
      diagnostics: {
        ...cached.payload.diagnostics,
        cache: "hit",
        durationMs: Date.now() - startedAt,
      },
    });
    return;
  }

  const inflight = reportInsightInflight.get(cacheKey);
  if (inflight) {
    res.json(buildPendingInsight({
      cache: "inflight",
      durationMs: Date.now() - startedAt,
    }));
    return;
  }

  const allowedTripIds = new Set(trips.map((trip) => trip.tripId));
  const invalidTripIds = tripIds.filter((tripId) => !allowedTripIds.has(tripId));
  if (invalidTripIds.length > 0) {
    res.status(400).json({ error: `Invalid tripIds for canonical input: ${invalidTripIds.join(", ")}` });
    return;
  }

  if (!getBedrockBearerToken()) {
    res.json(buildUnavailableInsight("missing-token", { durationMs: Date.now() - startedAt }));
    return;
  }

  const requestPromise = (async (): Promise<CopilotInsightPayload> => {
    const promptText = [
      "You are DMS Fleet Copilot. You are an explanation engine only.",
      "The canonical JSON/local AI input supplied by the app is authoritative.",
      "Never recalculate or replace scores, risk levels, event counts, TTC, DTC, maintenance priority, cost, downtime, or action orders.",
      "If a metric is 0, do not describe it as a risk, problem, violation, or event.",
      "For safety reports, do not mention maintenance, tires, DTC, cost, downtime, workshop, parts, or INSPECT/WATCH/NORMAL maintenance priority.",
      "Write detailed Vietnamese operational evaluation, but never invent metrics.",
      "For every trip insight, include: 2-3 pros if supported by nonzero/zero metrics, 3-5 concerns with exact numbers, and a concrete recommendation with why/priority/action.",
      "For safety reports, explain why the trip is risky using score, avgRisk, maxRisk, highRiskFrames, eventSummary, distractedPct, fatigueEvents, nearMissCount, harshBrakeCount, speedingPct, tailgatingPct.",
      "For maintenance reports, explain brakeStress, tireStress, DTC, priority, estimatedCostVnd, estimatedDowntime, and workOrderStatus only.",
      "Return JSON only: {\"fleet_insight\":\"detailed string\",\"trip_insights\":{\"TRIP_ID\":{\"pros\":[\"detailed string\"],\"concerns\":[\"detailed string\"],\"recommendation\":\"detailed string\"}}}.",
      `Report mode: ${reportMode || "unknown"}`,
      `Request id: ${canonicalInput?.request_id || "N/A"}`,
      `Policy version: ${canonicalInput?.policy_version || "report-canonical-v1"}`,
      "Compact canonical JSON/local AI input:",
      JSON.stringify({
        request_id: canonicalInput?.request_id,
        policy_version: canonicalInput?.policy_version || "report-canonical-v1",
        report_mode: reportMode,
        trips: trips.map((trip) => compactTripForBedrock(trip, reportMode)),
      }),
    ].join("\n\n");

    try {
      const rawAiOutput = await callBedrockConverse(promptText, BEDROCK_MODEL_ID, 5000);
      const cleanJson = rawAiOutput.replace(/```json/g, "").replace(/```/g, "").trim();
      const parsed = JSON.parse(cleanJson);
      validateBedrockInsight(parsed, trips, reportMode);
      const fleetInsight = typeof parsed.fleet_insight === "string" ? parsed.fleet_insight : "";
      if (!fleetInsight.trim()) throw new Error("Bedrock returned no fleet_insight");

      return {
        insight: fleetInsight,
        fleet_insight: fleetInsight,
        trip_insights: parsed.trip_insights && typeof parsed.trip_insights === "object" ? parsed.trip_insights : {},
        policy_version: "report-canonical-v1",
        ai_status: "validated",
        diagnostics: {
          provider: "bedrock",
          region: BEDROCK_REGION,
          modelId: BEDROCK_MODEL_ID,
          durationMs: Date.now() - startedAt,
          promptBytes: Buffer.byteLength(promptText, "utf8"),
          cache: "miss",
        },
      };
    } catch (err) {
      const reason = err instanceof Error ? err.name === "TimeoutError" ? "timeout" : err.message : "unknown-error";
      console.error("Bedrock report insight error:", {
        reason,
        durationMs: Date.now() - startedAt,
        promptBytes: Buffer.byteLength(promptText, "utf8"),
        region: BEDROCK_REGION,
        modelId: BEDROCK_MODEL_ID,
      });
      return buildUnavailableInsight(reason, {
        durationMs: Date.now() - startedAt,
        promptBytes: Buffer.byteLength(promptText, "utf8"),
        cache: "miss",
      });
    }
  })();

  reportInsightInflight.set(cacheKey, requestPromise);
  requestPromise.then((payload) => {
    if (payload.ai_status === "validated" || payload.ai_status === "unavailable") {
      reportInsightCache.set(cacheKey, {
        expiresAt: Date.now() + (payload.ai_status === "validated" ? REPORT_INSIGHT_CACHE_TTL_MS : REPORT_UNAVAILABLE_CACHE_TTL_MS),
        payload,
      });
    }
  }).finally(() => {
    reportInsightInflight.delete(cacheKey);
  });

  const foregroundResult = await Promise.race<CopilotInsightPayload>([
    requestPromise,
    new Promise((resolve) => setTimeout(() => resolve(buildPendingInsight({
      cache: "miss",
      durationMs: Date.now() - startedAt,
    })), 1200)),
  ]);

  if (foregroundResult.ai_status === "validated") {
    reportInsightCache.set(cacheKey, {
      expiresAt: Date.now() + REPORT_INSIGHT_CACHE_TTL_MS,
      payload: foregroundResult,
    });
    reportInsightInflight.delete(cacheKey);
  }
  res.json(foregroundResult);
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
