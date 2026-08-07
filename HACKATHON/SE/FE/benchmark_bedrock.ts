import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '.env.local') });
dotenv.config({ path: path.join(__dirname, '.env') });

const BEDROCK_REGION = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'ap-southeast-2';
const BEDROCK_MODEL_ID = process.env.BEDROCK_MODEL_ID || 'deepseek.v3.2';
const TOKEN = (process.env.AWS_BEARER_TOKEN_BEDROCK || '').replace(/\n/g, '').replace(/ /g, '').trim();

if (!TOKEN) {
  console.error('❌ AWS_BEARER_TOKEN_BEDROCK is not set in environment or env files');
  process.exit(1);
}

const ENDPOINT = `https://bedrock-runtime.${BEDROCK_REGION}.amazonaws.com/model/${encodeURIComponent(BEDROCK_MODEL_ID)}/converse`;

const PROMPTS = {
  'quick_chat': 'Xe nào trong fleet đang có rủi ro cao nhất? Trả lời ngắn gọn 2 câu.',
  'single_driver_report': `Bạn là Fleet AI Copilot.
Tài xế T01-Sample có safe_driving_score=0, harsh_brake_count=14, speeding_pct_time=0.0, max_risk_score=88.
Hãy tạo báo cáo đánh giá ngắn tài xế này gồm: điểm mạnh, điểm yếu, và khuyến nghị hành động.
Trả lời tiếng Việt, tối đa 150 từ.`,
  'fleet_maintenance_report': `Bạn là Fleet Maintenance Validator.
Có 1 xe trong fleet:
- T01-Sample: safe_score=0, harsh_brake=14, speeding_pct=0, max_risk=88, risk_classification=low
Tính toán MSI phanh = 15% + 14*3.5% + 0*5% = 64%. TSI lốp = 10% + 0*0.4% + 0*2% = 10%.
Sinh báo cáo bảo trì ngắn gọn dạng JSON:
{"fleet_insight": "...", "trip_insights": {"T01-Sample": {"pros":[],"cons":[],"evaluation":"..."}}, "vehicle_diagnostics": [{"trip_id":"T01-Sample","brake_msi":64,"tire_msi":10,"dtc_code":"C0035","maintenance_status":"..."}], "action_orders":{"do_not_drive":"...","priority_48h":"...","routine_maintenance":"..."}}
Trả về JSON thuần túy, không markdown.`
};

async function callBedrock(prompt: string): Promise<{ latencyMs: number; text: string; inputChars: number; outputChars: number; inputTokens: number; outputTokens: number }> {
  const t0 = Date.now();
  const inputChars = prompt.length;

  const response = await fetch(ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${TOKEN}`,
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content: [{ text: prompt }] }],
    }),
  });

  const latencyMs = Date.now() - t0;
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${payload?.message || response.statusText}`);
  }

  const text = payload?.output?.message?.content?.[0]?.text || '';
  const outputChars = text.length;
  const inputTokens = payload?.usage?.inputTokens || 0;
  const outputTokens = payload?.usage?.outputTokens || 0;

  return { latencyMs, text, inputChars, outputChars, inputTokens, outputTokens };
}

const RUNS = 3;

async function benchmark() {
  console.log(`\n🚀 Fleet AI Copilot — Bedrock Latency Benchmark`);
  console.log(`   Model: ${BEDROCK_MODEL_ID} @ ${BEDROCK_REGION}`);
  console.log(`   Endpoint: ${ENDPOINT}`);
  console.log(`   Runs per prompt: ${RUNS}\n`);

  const results: Record<string, number[]> = {};

  for (const [label, prompt] of Object.entries(PROMPTS)) {
    console.log(`\n📊 Testing: ${label}`);
    console.log(`   Prompt length: ${prompt.length} chars (~${Math.round(prompt.length / 4)} tokens est.)`);
    const latencies: number[] = [];
    let lastOutputTokens = 0;
    let lastInputTokens = 0;
    let lastText = '';

    for (let i = 0; i < RUNS; i++) {
      try {
        process.stdout.write(`   Run ${i + 1}/${RUNS}... `);
        const { latencyMs, text, inputTokens, outputTokens } = await callBedrock(prompt);
        latencies.push(latencyMs);
        lastInputTokens = inputTokens;
        lastOutputTokens = outputTokens;
        lastText = text;
        console.log(`✅ ${latencyMs}ms (input tokens: ${inputTokens}, output tokens: ${outputTokens})`);
        if (i < RUNS - 1) await new Promise(r => setTimeout(r, 500));
      } catch (err) {
        console.log(`❌ Error: ${err instanceof Error ? err.message : err}`);
        latencies.push(-1);
      }
    }

    const validLatencies = latencies.filter(l => l > 0).sort((a, b) => a - b);
    if (validLatencies.length > 0) {
      const p50 = validLatencies[Math.floor(validLatencies.length * 0.5)];
      const p95 = validLatencies[validLatencies.length - 1];
      const avg = Math.round(validLatencies.reduce((a, b) => a + b, 0) / validLatencies.length);
      const costUSD = (lastInputTokens * 0.0008 / 1000) + (lastOutputTokens * 0.0016 / 1000);

      console.log(`\n   ✅ Results for [${label}]:`);
      console.log(`      Latency → avg=${avg}ms | p50=${p50}ms | p95=${p95}ms`);
      console.log(`      Tokens real → input=${lastInputTokens} | output=${lastOutputTokens}`);
      console.log(`      Cost real → ~$${costUSD.toFixed(5)} per request`);
      console.log(`      Sample output (first 200 chars):\n      "${lastText.slice(0, 200).replace(/\n/g, ' ')}..."`);
      results[label] = validLatencies;
    } else {
      console.log(`\n   ❌ All runs failed for [${label}]`);
    }
  }

  console.log('\n\n' + '='.repeat(60));
  console.log('📋 SUMMARY TABLE (Copy vào báo cáo 14.3)');
  console.log('='.repeat(60));
  for (const [label, latencies] of Object.entries(results)) {
    if (latencies.length > 0) {
      const sorted = [...latencies].sort((a, b) => a - b);
      const p50 = sorted[Math.floor(sorted.length * 0.5)];
      const p95 = sorted[sorted.length - 1];
      console.log(`${label.padEnd(30)} | p50: ${String(p50).padStart(6)}ms | p95: ${String(p95).padStart(6)}ms`);
    }
  }
  console.log('='.repeat(60));
}

benchmark().catch(console.error);
