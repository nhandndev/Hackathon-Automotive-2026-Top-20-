import React, { useEffect, useMemo, useState, useRef } from 'react';
import { CalendarDays, Download, FileText, Shield, UserRound, Wrench, FileDown, FileCode, Check, ChevronDown, ChevronUp, Eye } from 'lucide-react';
import { TripData } from '../types';
import { buildRankingRows } from './DriverRankingView';
import { buildCopilotInput, buildVehicleReportModels, inferReportMode, VehicleReportModel } from '../reportModel';
// @ts-ignore
import html2pdf from 'html2pdf.js';

interface CopilotFleetReportPageProps {
  vehicles: TripData[];
  reportType: string | null;
  tripIds: string | null;
  dataReady?: boolean;
}

const panel = 'rounded-lg border border-[#1E293B] bg-[#111827] shadow-lg shadow-black/20';

const finite = (value: unknown, digits = 1) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';

const displayScore = (value: number) => value.toFixed(1);

const normalizeScoreText = (text: string, canonicalScore: number) =>
  text
    .replace(/(Ranking Score|Trip Ranking Score|Score|Điểm an toàn)\s*(:|là|đạt)?\s*\d+(?:\.\d+)?\/100/gi, (_match, label, separator = ':') => {
      const sep = String(separator).trim() || ':';
      return `${label} ${sep} ${displayScore(canonicalScore)}/100`;
    })
    .replace(/\d+\.\d{2,}\/100/g, `${displayScore(canonicalScore)}/100`);

const normalizeLongScoreText = (text: string) =>
  text.replace(/\d+\.\d{2,}\/100/g, (match) => `${Number.parseFloat(match).toFixed(1)}/100`);

const severityClass = (level: string) => {
  if (level === 'CRITICAL') return 'border-red-500/50 bg-red-950/30 text-red-200';
  if (level === 'AT_RISK') return 'border-orange-500/50 bg-orange-950/30 text-orange-200';
  if (level === 'WATCH') return 'border-amber-500/50 bg-amber-950/30 text-amber-200';
  return 'border-emerald-500/50 bg-emerald-950/30 text-emerald-200';
};

const columnClass = (count: number) => {
  if (count <= 1) return 'grid-cols-1';
  return 'grid-cols-1 md:grid-cols-2';
};

const eventRowsFor = (trip: TripData) => {
  const frames = trip.frames ?? [];
  const events: Array<{ time: string; type: string; severity: string; detail: string; rawTimestamp: number }> = [];
  let previousState: string | undefined = undefined;
  const lastEventTimeByType: Record<string, number> = {};

  for (const frame of frames) {
    const currentState = frame.driver?.state ?? 'alert';
    const isStateChanged = previousState !== undefined && previousState !== currentState;
    const hasBehaviorFlag = frame.behavior_flags?.harsh_brake || frame.behavior_flags?.tailgating || frame.behavior_flags?.speeding;
    const isHighRisk = Number(frame.risk?.final_risk_score ?? 0) >= 50;
    const isLowTtc = Number.isFinite(frame.min_ttc) && (frame.min_ttc as number) <= 3;
    const currentTs = Number(frame.timestamp ?? 0);

    if (isStateChanged || hasBehaviorFlag || isHighRisk || isLowTtc) {
      let eventTitle = 'Sự kiện an toàn';
      const riskScore = Number(frame.risk?.final_risk_score ?? 0);

      // Determine category
      let category = 'Sự kiện an toàn';
      if (riskScore >= 70 || currentState === 'microsleep' || currentState === 'yawning') {
        category = 'Sự kiện nguy hiểm';
      } else if (riskScore >= 40 || currentState === 'drowsy' || currentState === 'distracted' || hasBehaviorFlag) {
        category = 'Sự kiện cảnh báo';
      }

      if (isStateChanged) {
        eventTitle = `Chuyển trạng thái: ${previousState} ➔ ${currentState}`;
      } else if (frame.behavior_flags?.harsh_brake) {
        eventTitle = 'Phanh gấp (Harsh brake)';
      } else if (frame.behavior_flags?.tailgating) {
        eventTitle = 'Bám đuôi gần (Tailgating)';
      } else if (frame.behavior_flags?.speeding) {
        eventTitle = 'Vượt quá tốc độ (Speeding)';
      } else if (currentState !== 'alert') {
        eventTitle = `Driver state ${currentState}`;
      }

      // DATA DEBOUNCE FILTER (3.0s window): Filter out sensor noise (e.g. 14 harsh brakes in 0.7s)
      const lastTs = lastEventTimeByType[eventTitle] ?? -999;
      if (currentTs - lastTs >= 3.0) {
        lastEventTimeByType[eventTitle] = currentTs;
        events.push({
          time: `${finite(frame.timestamp, 1)}s`,
          type: eventTitle,
          severity: category,
          detail: `risk=${finite(frame.risk?.final_risk_score)}, ttc=${Number.isFinite(frame.min_ttc) ? `${(frame.min_ttc as number).toFixed(2)}s` : 'Infinity'}, alertness=${finite(frame.driver?.alertness_score, 2)}`,
          rawTimestamp: currentTs,
        });
      }
    }
    previousState = currentState;
  }

  // Fallback if no transitions
  if (events.length === 0 && frames.length > 0) {
    return frames.map(f => ({
      time: `${finite(f.timestamp, 1)}s`,
      type: `Driver state ${f.driver?.state ?? 'alert'}`,
      severity: 'Sự kiện an toàn',
      detail: `risk=${finite(f.risk?.final_risk_score)}, ttc=${Number.isFinite(f.min_ttc) ? `${(f.min_ttc as number).toFixed(2)}s` : 'Infinity'}`,
    }));
  }

  return events;
};

const reportForRow = (models: VehicleReportModel[], tripId: string) => models.find((model) => model.tripId === tripId);

const COPILOT_REPORT_CACHE_PREFIX = 'copilot-report-ai:';

const readCachedCopilotInsight = (signature: string) => {
  try {
    const cached = window.sessionStorage.getItem(`${COPILOT_REPORT_CACHE_PREFIX}${signature}`);
    return cached ? JSON.parse(cached) : null;
  } catch {
    return null;
  }
};

const writeCachedCopilotInsight = (signature: string, payload: unknown) => {
  try {
    window.sessionStorage.setItem(`${COPILOT_REPORT_CACHE_PREFIX}${signature}`, JSON.stringify(payload));
  } catch {
    // Cache is an optimization only; report data still renders from JSON/local AI.
  }
};

const textFromInsightPayload = (value: any): string => {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(textFromInsightPayload).join('\n');
  if (value && typeof value === 'object') return Object.values(value).map(textFromInsightPayload).join('\n');
  return '';
};

const hasPositiveAiMention = (text: string, pattern: RegExp, negativePattern?: RegExp) =>
  pattern.test(text) && !(negativePattern && negativePattern.test(text));

const isValidBedrockPayloadForRows = (payload: any, rows: ReturnType<typeof buildRankingRows>, reportType: string | null) => {
  const allText = textFromInsightPayload(payload).toLowerCase();
  if (reportType === 'safety' && /(bảo trì|bao tri|lốp|lop|tire|dtc|chi phí|chi phi|downtime|phụ tùng|phu tung|work order|brake stress|tire stress|inspect)/i.test(allText)) {
    return false;
  }
  for (const row of rows) {
    const tripText = textFromInsightPayload(payload?.trip_insights?.[row.trip_id]).toLowerCase();
    if (!tripText) continue;
    const checks: Array<[boolean, RegExp, RegExp | undefined]> = [
      [row.harshEvents === 0, /(phanh|brake|harsh brake)/i, /(không|khong|no)[^.]{0,40}(phanh|brake|harsh brake)/i],
      [row.nearMissCount === 0, /(near miss|ttc thấp|ttc thap|suýt va|suyt va)/i, /(không|khong|no)[^.]{0,40}(near miss|ttc|suýt va|suyt va)/i],
      [row.fatigueEvents === 0, /(mệt mỏi|met moi|vi ngủ|vi ngu|microsleep|fatigue|drowsy|yawning)/i, /(không|khong|no)[^.]{0,40}(mệt|met|vi ngủ|vi ngu|microsleep|fatigue|drowsy|yawning)/i],
      [row.distractedPct === 0, /(xao nhãng|xao nhang|phân tâm|phan tam|distract)/i, /(không|khong|no)[^.]{0,40}(xao nhãng|xao nhang|phân tâm|phan tam|distract)/i],
      [row.speedingPct === 0, /(quá tốc|qua toc|vượt tốc|vuot toc|speeding)/i, /(không|khong|no)[^.]{0,40}(quá tốc|qua toc|vượt tốc|vuot toc|speeding)/i],
      [row.tailgatingPct === 0, /(bám đuôi|bam duoi|tailgating)/i, /(không|khong|no)[^.]{0,40}(bám đuôi|bam duoi|tailgating)/i],
    ];
    if (checks.some(([enabled, pattern, negativePattern]) => enabled && hasPositiveAiMention(tripText, pattern, negativePattern))) return false;
  }
  return true;
};

const aiLoadingCopy = {
  pros: 'AI Copilot đang tạo insight từ Bedrock...',
  cons: 'AI Copilot đang phân tích dữ liệu rủi ro...',
  evaluation: 'AI Copilot đang xử lý nhận xét đánh giá chuyên sâu...',
  dtc: 'AI đang kiểm tra dữ liệu DTC có sẵn...',
  maintenanceStatus: 'AI đang phân loại inspection triage...',
  parts: 'Chưa có dữ liệu kho phụ tùng...',
  workOrder: 'Recommended - not created',
  doNotDrive: 'AI Copilot đang tổng hợp safety review...',
  priority48h: 'AI Copilot đang xếp loại kiểm tra kỹ thuật...',
  coaching: 'AI Copilot đang đề xuất coaching an toàn...',
  reward: 'AI Copilot đang đánh giá mức độ xuất sắc...',
  fleet: 'AI Copilot đang tổng hợp dữ liệu số liệu toàn bộ trip...',
};

type AiInsightStatus = 'loading' | 'pending' | 'validated' | 'unavailable';

const aiStatusLabel = (status: AiInsightStatus) => (
  status === 'validated'
    ? 'Bedrock insight đã xác thực'
    : status === 'loading' || status === 'pending'
      ? 'Đánh giá JSON/local AI - Bedrock chạy nền'
      : 'Đánh giá JSON/local AI - chờ Bedrock hợp lệ'
);

const aiStatusClass = (status: AiInsightStatus) => (
  status === 'validated'
    ? 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30'
    : status === 'loading' || status === 'pending'
      ? 'bg-sky-950/60 text-sky-300 border-sky-500/30'
      : 'bg-slate-900 text-slate-300 border-slate-700'
);

const buildLocalReportNarrative = (models: VehicleReportModel[], mode: string) => {
  if (models.length === 0) return 'Chưa có dữ liệu canonical để lập báo cáo.';
  const sortedByScore = [...models].sort((a, b) => b.score - a.score);
  const sortedByAvgRisk = [...models].sort((a, b) => b.avgRisk - a.avgRisk);
  const sortedByHighRiskFrames = [...models].sort((a, b) => b.rawCriticalRiskFrames - a.rawCriticalRiskFrames);
  const avgScore = models.reduce((sum, model) => sum + model.score, 0) / models.length;
  const avgRisk = models.reduce((sum, model) => sum + model.avgRisk, 0) / models.length;
  const maxRisk = Math.max(...models.map((model) => model.maxRisk));
  const totalHighRiskFrames = models.reduce((sum, model) => sum + model.rawCriticalRiskFrames, 0);
  const totalNearMiss = models.reduce((sum, model) => sum + model.nearMissCount, 0);
  const totalHarshBrake = models.reduce((sum, model) => sum + model.harshBrakeCount, 0);
  const totalDistractedTrips = models.filter((model) => model.distractedPct > 0).length;
  const totalEvents = models.reduce((sum, model) => sum + model.eventSummary.total, 0);
  const dangerEvents = models.reduce((sum, model) => sum + model.eventSummary.danger, 0);
  const warningEvents = models.reduce((sum, model) => sum + model.eventSummary.warning, 0);
  const reviewRequired = models.filter((model) => model.safetyAction === 'COACHING_24H').map((model) => model.tripId);
  const inspect = models.filter((model) => model.maintenance.priority === 'INSPECT').map((model) => model.tripId);
  const watch = models.filter((model) => model.maintenance.priority === 'WATCH').map((model) => model.tripId);
  const normal = models.filter((model) => model.maintenance.priority === 'NORMAL').map((model) => model.tripId);

  if (mode.startsWith('maintenance')) {
    return [
      mode === 'maintenance_detail' ? `### 1. Inspection triage detail - ${models[0].tripId}` : `### 1. Safety-based inspection triage - ${models.length} trip`,
      'Báo cáo này là ưu tiên kiểm tra kỹ thuật dựa trên safety telemetry, không phải chẩn đoán hỏng hóc. AI chỉ diễn giải, không tạo DTC, không tạo wear %, không tạo work order hoặc báo giá sửa chữa.',
      '### 2. Triage kiểm tra kỹ thuật',
      `INSPECT: ${inspect.join(', ') || 'Không có'}. WATCH: ${watch.join(', ') || 'Không có'}. NORMAL: ${normal.join(', ') || 'Không có'}.`,
      '### 3. Vehicle health data availability',
      models.map((model) => `${model.tripId}: Brake Stress Estimate ${model.maintenance.brakeStress}/100, Tire Stress Estimate ${model.maintenance.tireStress}/100, DTC ${model.maintenance.dtcCode}, priority ${model.maintenance.priority}, repair cost N/A until workshop inspection.`).join('\n'),
      '### 4. Khuyến nghị',
      'Các hạng mục là Recommended - not created. Nếu không có DTC/odometer/engine-hours/brake-wear/tire-pressure telemetry, báo cáo chỉ đề xuất review an toàn và kiểm tra kỹ thuật cơ bản trước chuyến tiếp theo.',
    ].join('\n\n');
  }

  if (mode === 'safety_detail') {
    const model = models[0];
    const mainReasons = [
      model.avgRisk >= 70 ? `avg risk rất cao (${model.avgRisk.toFixed(1)}/100)` : null,
      model.rawCriticalRiskFrames > 0 ? `${model.rawCriticalRiskFrames} khung rủi ro cao` : null,
      model.harshBrakeCount > 0 ? `${model.harshBrakeCount} phanh gấp thật` : null,
      model.distractedPct > 0 ? `${model.distractedPct.toFixed(1)}% distracted` : null,
      model.nearMissCount > 0 ? `${model.nearMissCount} near miss/TTC thấp` : null,
    ].filter(Boolean).join(', ');

    return [
      `### 1. Đánh giá an toàn chi tiết - ${model.tripId}`,
      `Trip đạt Ranking Score ${displayScore(model.score)}/100, mức Trip Safety Risk: ${model.riskLevel}. Nếu trip đang xếp #${model.rank} trong fleet hiện tại, đây chỉ là relative fleet rank, không có nghĩa là safe nếu score dưới ngưỡng an toàn.`,
      '### 2. Kết luận chính',
      mainReasons
        ? `Rủi ro chính đến từ ${mainReasons}. Max risk đạt ${model.maxRisk.toFixed(1)}/100 nên trip cần được xem là nguy hiểm dù một số event hành vi như near miss hoặc phanh gấp có thể bằng 0.`
        : `Không ghi nhận event hành vi lớn; tiếp tục theo dõi vì điểm ranking vẫn phụ thuộc avg/max risk.`,
      '### 3. Quyết định vận hành',
      model.safetyAction === 'COACHING_24H'
        ? 'Safety review required before next dispatch. Review high-risk segments và xác minh road/environment/model context; không kết luận lỗi vận hành nếu chưa có evidence từ frame review.'
        : model.safetyAction === 'WARNING'
          ? 'Cần nhắc nhở và theo dõi trong chuyến kế tiếp.'
          : 'Có thể dùng làm benchmark tương đối trong fleet hiện tại.',
    ].join('\n\n');
  }

  const allNeedReview = reviewRequired.length === models.length;
  const best = sortedByScore[0];
  const worst = sortedByScore.at(-1);
  const highestRisk = sortedByAvgRisk[0];
  const mostHighRiskFrames = sortedByHighRiskFrames[0];

  return [
    `### 1. Đánh giá tổng quan an toàn fleet - ${models.length} trip`,
    `Fleet Ranking Score trung bình là ${avgScore.toFixed(1)}/100, avg risk trung bình ${avgRisk.toFixed(1)}/100 và max risk cao nhất ${maxRisk.toFixed(1)}/100. Kết luận: ${allNeedReview ? 'toàn bộ fleet đang ở ngưỡng cần safety review, không có trip đủ điều kiện gọi là an toàn.' : 'fleet có phân hóa rủi ro, cần ưu tiên theo ranking score.'}`,
    '### 2. Đánh giá thống kê',
    `Tổng cộng có ${totalHighRiskFrames} khung rủi ro cao, ${totalHarshBrake} phanh gấp thật, ${totalNearMiss} near miss/TTC thấp. Event canonical sau debounce là ${totalEvents} log (${dangerEvents} danger, ${warningEvents} warning), dùng để audit diễn biến chứ không thay thế các tổng frame-level.`,
    '### 3. Nhận định xếp hạng',
    `${best.tripId} đứng cao nhất với ${best.score.toFixed(1)}/100, nghĩa là ít rủi ro tương đối nhất trong fleet chứ không phải an toàn tuyệt đối. ${worst ? `${worst.tripId} đứng cuối với ${worst.score.toFixed(1)}/100.` : ''} Trip có avg risk cao nhất là ${highestRisk.tripId} (${highestRisk.avgRisk.toFixed(1)}/100); trip có nhiều khung rủi ro cao nhất là ${mostHighRiskFrames.tripId} (${mostHighRiskFrames.rawCriticalRiskFrames} frames).`,
    '### 4. Nguyên nhân chính',
    `Yếu tố kéo điểm fleet xuống là risk.final_risk_score duy trì cao trên nhiều frame. ${totalDistractedTrips > 0 ? `${totalDistractedTrips}/${models.length} trip có distracted.` : 'Không có distracted đáng kể trong fleet này.'} ${totalHarshBrake > 0 ? `Có ${totalHarshBrake} phanh gấp thật cần coaching kỹ thuật giữ khoảng cách/phản ứng.` : 'Không ghi nhận phanh gấp thật ở một số trip rủi ro, nên nguyên nhân chính của các trip đó là risk model/frame-level chứ không phải brake event.'}`,
    '### 5. Khuyến nghị vận hành',
    allNeedReview
      ? `Không chọn SAFE benchmark trong batch này. Ưu tiên safety review trước chuyến tiếp theo theo thứ tự rủi ro: ${sortedByScore.slice().reverse().map((model) => model.tripId).join(' -> ')}.`
      : `Safety review required: ${reviewRequired.join(', ') || 'Không có'}. Nhóm còn lại theo dõi theo ranking score và max risk.`,
  ].join('\n\n');
};

const buildPendingReportNarrative = (models: VehicleReportModel[], mode: string) => {
  if (models.length === 0) return 'Đang chờ dữ liệu JSON/local AI trước khi tạo đánh giá.';
  if (mode === 'safety_detail') {
    const model = models[0];
    return [
      `### AI Copilot đang đánh giá an toàn trip ${model.tripId}`,
      `Đã tải số liệu JSON/local AI: Ranking Score ${model.score.toFixed(1)}/100, max risk ${model.maxRisk.toFixed(1)}/100, ${model.rawCriticalRiskFrames} khung rủi ro cao.`,
      'Bedrock đang chạy nền để tạo nhận xét chi tiết. Trong lúc chờ, hệ thống chỉ hiển thị KPI thật từ JSON/local AI và không tự bịa ưu/nhược điểm.',
    ].join('\n\n');
  }
  if (mode === 'safety_overview') {
    const avgScore = models.reduce((sum, model) => sum + model.score, 0) / models.length;
    const totalHighRiskFrames = models.reduce((sum, model) => sum + model.rawCriticalRiskFrames, 0);
    return [
      `### AI Copilot đang đánh giá an toàn toàn fleet`,
      `Đã tải ${models.length} trip từ JSON/local AI: Fleet Ranking Score ${avgScore.toFixed(1)}/100, tổng ${totalHighRiskFrames} khung rủi ro cao.`,
      'Bedrock đang chạy nền để tạo đánh giá thống kê đầy đủ. Trong lúc chờ, hệ thống chỉ hiển thị KPI thật và không hiển thị insight thay thế.',
    ].join('\n\n');
  }
  if (mode === 'maintenance_detail') {
    const model = models[0];
    return [
      `### AI Copilot đang đánh giá ưu tiên kiểm tra kỹ thuật trip ${model.tripId}`,
      `Đã tải số liệu JSON/local AI: Brake Stress Estimate ${model.maintenance.brakeStress}/100, Tire Stress Estimate ${model.maintenance.tireStress}/100, DTC ${model.maintenance.dtcCode}.`,
      'Bedrock đang chạy nền để diễn giải triage. Trong lúc chờ, hệ thống không tạo mã lỗi, phụ tùng, work order, chi phí hoặc kết luận hỏng hóc.',
    ].join('\n\n');
  }
  const inspectCount = models.filter((model) => model.maintenance.priority === 'INSPECT').length;
  return [
    `### AI Copilot đang đánh giá ưu tiên kiểm tra kỹ thuật toàn fleet`,
    `Đã tải ${models.length} trip từ JSON/local AI: ${inspectCount} trip ở mức INSPECT do DTC/stress threshold, các chỉ số estimate/DTC giữ nguyên từ dữ liệu thật.`,
    'Bedrock đang chạy nền để bổ sung nhận xét triage. Trong lúc chờ, hệ thống không tạo chẩn đoán, báo giá hoặc action order thay thế.',
  ].join('\n\n');
};

export const CopilotFleetReportPage: React.FC<CopilotFleetReportPageProps> = ({ vehicles, reportType, tripIds, dataReady = true }) => {
  const [copilotInsight, setCopilotInsight] = useState('Đang chờ phản hồi AI Copilot từ Bedrock...');
  const [aiInsightStatus, setAiInsightStatus] = useState<AiInsightStatus>('loading');
  const [aiTripInsights, setAiTripInsights] = useState<Record<string, any>>({});
  const [isLoadingInsight, setIsLoadingInsight] = useState(true);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);
  const [expandedTrips, setExpandedTrips] = useState<Record<string, boolean>>({});
  const menuRef = useRef<HTMLDivElement>(null);

  const toggleTripExpand = (tripId: string) => {
    setExpandedTrips(prev => ({ ...prev, [tripId]: !prev[tripId] }));
  };

  const selectedIds = (tripIds ?? '').split(',').filter(Boolean);
  const selectedTrips = useMemo(() => (
    selectedIds.length
      ? vehicles.filter((vehicle) => selectedIds.includes(vehicle.trip_id))
      : reportType === 'compare'
        ? vehicles.slice(0, 2)
        : vehicles.filter((vehicle) => vehicle.runtime_status === 'completed')
  ), [selectedIds.join(','), vehicles, reportType]);
  const missingSelectedIds = useMemo(
    () => selectedIds.filter((tripId) => !selectedTrips.some((trip) => trip.trip_id === tripId)),
    [selectedIds.join(','), selectedTrips],
  );
  
  const rows = useMemo(() => {
    // 1. Compute true global fleet ranking across ALL vehicles in system
    const allFleetRows = buildRankingRows(vehicles);
    
    // 2. Filter for selected trips while preserving global rank (#1..#N)
    const selectedTripSet = new Set(selectedTrips.map(t => t.trip_id));
    const rawRows = allFleetRows.filter(r => selectedTripSet.has(r.trip_id));

    if (reportType === 'maintenance') {
      // Sort by Wear Damage Percentage (descending: highest wear / damage first)
      return [...rawRows].sort((a, b) => {
        const aHarsh = a.harshEvents;
        const aCrit = a.criticalEvents;
        const aSpeed = a.speedingPct;
        const aBrakeWear = Math.min(98, Math.max(12, Math.round(15 + aHarsh * 3 + aCrit * 8)));
        const aTireWear = Math.min(95, Math.max(10, Math.round(10 + aSpeed * 0.4 + aHarsh * 2)));
        const aTotalWear = aBrakeWear + aTireWear;

        const bHarsh = b.harshEvents;
        const bCrit = b.criticalEvents;
        const bSpeed = b.speedingPct;
        const bBrakeWear = Math.min(98, Math.max(12, Math.round(15 + bHarsh * 3 + bCrit * 8)));
        const bTireWear = Math.min(95, Math.max(10, Math.round(10 + bSpeed * 0.4 + bHarsh * 2)));
        const bTotalWear = bBrakeWear + bTireWear;

        return bTotalWear - aTotalWear;
      });
    }
    if (reportType === 'safety' && rawRows.length > 1) {
      return [...rawRows].sort((a, b) =>
        (a.score - b.score)
        || (b.maxRisk - a.maxRisk)
        || (b.avgRisk - a.avgRisk)
        || (b.criticalEvents - a.criticalEvents)
      );
    }
    return rawRows;
  }, [vehicles, selectedTrips, reportType]);

  const reportModels = useMemo(() => {
    const models = buildVehicleReportModels(vehicles, selectedTrips);
    if (reportType === 'maintenance') {
      return [...models].sort((a, b) => {
        const priorityRank = { INSPECT: 3, WATCH: 2, NORMAL: 1 };
        return (priorityRank[b.maintenance.priority] - priorityRank[a.maintenance.priority])
          || (b.maintenance.brakeStress + b.maintenance.tireStress) - (a.maintenance.brakeStress + a.maintenance.tireStress);
      });
    }
    if (reportType === 'safety' && models.length > 1) {
      return [...models].sort((a, b) =>
        (a.score - b.score)
        || (b.maxRisk - a.maxRisk)
        || (b.avgRisk - a.avgRisk)
        || (b.rawCriticalRiskFrames - a.rawCriticalRiskFrames)
      );
    }
    return models;
  }, [vehicles, selectedTrips, reportType]);

  const reportMode = useMemo(() => inferReportMode(reportType, reportModels.length), [reportType, reportModels.length]);
  const canRequestBedrockInsight = dataReady && reportModels.length > 0 && missingSelectedIds.length === 0;
  const localReportNarrative = useMemo(
    () => buildLocalReportNarrative(reportModels, reportMode),
    [reportModels, reportMode],
  );
  const pendingReportNarrative = useMemo(
    () => buildPendingReportNarrative(reportModels, reportMode),
    [reportModels, reportMode],
  );
  
  const reportTitle = reportType === 'maintenance'
    ? 'Safety-Based Inspection Priority Report'
    : reportType === 'safety'
      ? 'Fleet Safety Executive Report'
      : 'Trip Safety Comparison Report';
      
  const subtitle = reportType === 'maintenance'
    ? 'Ưu tiên kiểm tra kỹ thuật dựa trên safety telemetry JSON/local AI; Bedrock chỉ diễn giải insight, không chẩn đoán hỏng hóc.'
    : reportType === 'safety'
      ? 'Tổng hợp an toàn từ JSON/local AI telemetry, trip risk, TTC/headway và safety review priority.'
      : `So sánh và đánh giá mức độ an toàn của ${rows.length} trip`;

  const allFleetRows = useMemo(() => buildRankingRows(vehicles), [vehicles]);
  const fleetAverage = allFleetRows.length ? allFleetRows.reduce((sum, row) => sum + row.score, 0) / allFleetRows.length : 0;
  const isSafetyOverview = reportType === 'safety' && rows.length > 1;
  const selectedFleetAverage = rows.length ? rows.reduce((sum, row) => sum + row.score, 0) / rows.length : 0;
  const safeTripCount = rows.filter((row) => row.riskLevel === 'SAFE' || row.score >= 80).length;
  const selectedHighRiskFrames = rows.reduce((sum, row) => sum + row.criticalEvents, 0);
  const fleetStatus = rows.some((row) => row.riskLevel === 'CRITICAL')
    ? 'CRITICAL'
    : rows.some((row) => row.riskLevel === 'AT_RISK')
      ? 'AT_RISK'
      : rows.some((row) => row.riskLevel === 'WATCH')
        ? 'WATCH'
        : 'SAFE';
  const highestRankedRow = [...rows].sort((a, b) => a.rank - b.rank)[0] ?? rows[0];
  const reviewPriorityPath = rows.map((row) => row.trip_id).join(' → ');
  const aiIsLoading = isLoadingInsight || aiInsightStatus === 'loading' || aiInsightStatus === 'pending';

  useEffect(() => {
    let cancelled = false;
    const loadInsight = async () => {
      if (!dataReady) {
        setIsLoadingInsight(true);
        setAiInsightStatus('loading');
        setAiTripInsights({});
        setCopilotInsight('Đang tải saved trips từ backend trước khi gọi Bedrock...');
        return;
      }

      if (!canRequestBedrockInsight) {
        setIsLoadingInsight(false);
        setAiInsightStatus('unavailable');
        setAiTripInsights({});
        setCopilotInsight(
          missingSelectedIds.length > 0
            ? `Chưa tìm thấy dữ liệu JSON/local AI cho trip: ${missingSelectedIds.join(', ')}. Không gọi Bedrock khi thiếu canonical input.`
            : localReportNarrative,
        );
        return;
      }

      setIsLoadingInsight(true);
      setAiInsightStatus('loading');
      setCopilotInsight(localReportNarrative);
      try {
        const canonicalInput = buildCopilotInput(reportModels, reportMode);
        const inputSignature = JSON.stringify({
          validator: 'bedrock-contract-v4-score-format-trip-risk',
          reportType,
          reportMode,
          tripIds: rows.map((row) => row.trip_id),
          trips: canonicalInput.trips,
        });
        const cachedPayload = readCachedCopilotInsight(inputSignature);
        if (cachedPayload) {
          if (!cancelled && isValidBedrockPayloadForRows(cachedPayload, rows, reportType)) {
            setAiInsightStatus('validated');
            setCopilotInsight(cachedPayload.fleet_insight || cachedPayload.insight || 'AI Copilot chưa trả insight.');
            setAiTripInsights(cachedPayload.trip_insights ?? {});
            setIsLoadingInsight(false);
          }
          if (isValidBedrockPayloadForRows(cachedPayload, rows, reportType)) return;
        }

        let lastPayload: any = null;
        for (let attempt = 0; attempt < 4; attempt += 1) {
          const response = await fetch('/api/copilot/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              reportType,
              reportMode,
              canonicalInput: {
                ...canonicalInput,
                input_signature: inputSignature,
              },
              tripIds: rows.map((row) => row.trip_id),
            }),
          });

          const payload = await response.json();
          lastPayload = payload;
          if (!response.ok) throw new Error(payload.error || `Copilot report HTTP ${response.status}`);
          if (cancelled) return;

          if (payload.ai_status === 'validated' && !payload.vehicle_diagnostics && !payload.action_orders && isValidBedrockPayloadForRows(payload, rows, reportType)) {
            setAiInsightStatus('validated');
            setCopilotInsight(payload.fleet_insight || payload.insight || 'AI Copilot chưa trả insight.');
            setAiTripInsights(payload.trip_insights ?? {});
            writeCachedCopilotInsight(inputSignature, payload);
            return;
          }

          setAiInsightStatus(payload.ai_status === 'pending' ? 'pending' : 'unavailable');
          setCopilotInsight(localReportNarrative);
          setAiTripInsights({});
          if (attempt < 3 && payload.ai_status === 'pending') {
            await new Promise(resolve => setTimeout(resolve, 2200));
          } else {
            break;
          }
        }

        if (!cancelled && lastPayload?.ai_status !== 'validated') {
          setAiInsightStatus('unavailable');
          setCopilotInsight(localReportNarrative);
        }
      } catch (err) {
        if (!cancelled) {
          setAiInsightStatus('unavailable');
          setCopilotInsight(localReportNarrative);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingInsight(false);
        }
      }
    };
    void loadInsight();
    return () => {
      cancelled = true;
    };
  }, [
    dataReady,
    canRequestBedrockInsight,
    reportType,
    reportMode,
    localReportNarrative,
    pendingReportNarrative,
    rows.map(r => r.trip_id).join(','),
    reportModels.map(m => `${m.tripId}:${m.score}:${m.maxRisk}:${m.eventSummary.total}:${m.maintenance.priority}`).join('|'),
    missingSelectedIds.join(','),
  ]);

  // Click outside listener for export menu
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const generateReportHTML = () => {
    const nowStr = new Date().toLocaleString('vi-VN');
    const rowsHTML = rows.map((row, idx) => {
      const tripId = row.trip_id;
      const tripAi = aiTripInsights[tripId];
      const model = reportForRow(reportModels, row.trip_id);
      const safeScore = row.score;

      const logEvents = eventRowsFor(row.trip);
      const brakeLogCount = row.harshEvents;
      const speedingPct = row.speedingPct;

      const hasHighDistraction = row.distractedPct > 25;
      const hasFatigue = row.fatigueEvents > 0;

      let defaultPros: string[] = [];
      let defaultCons: string[] = [];

      if (safeScore >= 80 && !hasHighDistraction && !hasFatigue) {
        defaultPros.push(`Ranking Score thuộc nhóm xuất sắc (${displayScore(safeScore)}/100), kiểm soát rủi ro cực tốt.`);
      } else if (safeScore >= 60 && !hasHighDistraction) {
        defaultPros.push(`Ranking Score ở mức trung bình khá (${displayScore(safeScore)}/100).`);
      }

      if (speedingPct === 0) {
        defaultPros.push(`Tuân thủ giới hạn tốc độ tuyệt đối (0.0%).`);
      } else {
        defaultCons.push(`Vi phạm tốc độ ở mức ${speedingPct.toFixed(1)}%, gây nguy hiểm nghiêm trọng.`);
      }

      if (brakeLogCount === 0) {
        defaultPros.push(`Trip không ghi nhận tình huống phanh gấp nguy hiểm.`);
      } else {
        defaultCons.push(`Ghi nhận ${brakeLogCount} sự kiện phanh gấp, dấu hiệu thiếu quan sát hoặc không giữ khoảng cách an toàn.`);
      }

      if (hasHighDistraction) {
        defaultCons.push(`CẢNH BÁO NGHIÊM TRỌNG: Tỷ lệ xao nhãng mất tập trung lên tới ${row.distractedPct.toFixed(1)}% (cao gấp đôi mức trung bình Fleet), nguy cơ va chạm rất cao.`);
      } else if (row.distractedPct > 5) {
        defaultCons.push(`Driver state distracted chiếm ${row.distractedPct.toFixed(1)}% thời gian trong trip.`);
      }

      if (hasFatigue) {
        defaultCons.push(`CẢNH BÁO VI NGỦ: Phát hiện ${row.fatigueEvents} sự kiện vi ngủ/ngáp nguy hiểm.`);
      }

      if (row.criticalEvents > 0) {
        defaultCons.push(`Phát hiện ${row.criticalEvents} khung hình rủi ro cao theo risk.final_risk_score; đây không đồng nghĩa với ${row.criticalEvents} sự kiện phanh gấp hoặc near-miss.`);
      }

      if (defaultPros.length === 0) {
        defaultPros.push(`Duy trì tốc độ theo giới hạn tuyến đường.`);
      }

      const defaultEval = (hasHighDistraction || hasFatigue || safeScore < 60)
        ? `🛑 SAFETY REVIEW BẮT BUỘC TRƯỚC CHUYẾN TIẾP THEO: Trip ${row.trip_id} đạt Ranking Score ${displayScore(safeScore)}/100 và có ${row.criticalEvents} khung rủi ro cao. Cần review high-risk frames; không kết luận lỗi vận hành nếu chưa xác minh evidence.`
        : (row.distractedPct > 15 || safeScore < 80)
          ? `⚠️ NHẮC NHỞ: Trip ${row.trip_id} cần review các đoạn xao nhãng (${row.distractedPct.toFixed(1)}%) và khoảng cách an toàn.`
          : `🏆 BENCHMARK: Trip ${row.trip_id} là trip có hành vi an toàn tương đối tốt trong batch hiện tại.`;

      const prosList = aiInsightStatus === 'validated'
        ? (tripAi?.pros ?? defaultPros)
        : [aiLoadingCopy.pros, ...defaultPros];
      const consList = aiInsightStatus === 'validated'
        ? (tripAi?.cons ?? defaultCons)
        : [aiLoadingCopy.cons, ...defaultCons];
      const evalText = aiInsightStatus === 'validated'
        ? (tripAi?.evaluation ?? defaultEval)
        : `${aiLoadingCopy.evaluation}\n${defaultEval}`;

      return `
        <div style="border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #f8fafc;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 12px;">
            <div>
              <span style="font-weight: bold; color: #0284c7; font-size: 12px; text-transform: uppercase;">TRIP ${String(idx + 1).padStart(2, '0')}</span>
              <h3 style="margin: 4px 0 0 0; color: #0f172a; font-size: 20px;">Trip ID: ${row.trip_id}</h3>
            </div>
            <span style="background-color: ${row.riskLevel === 'CRITICAL' ? '#fee2e2' : row.riskLevel === 'AT_RISK' ? '#ffedd5' : '#dcfce7'}; color: ${row.riskLevel === 'CRITICAL' ? '#991b1b' : row.riskLevel === 'AT_RISK' ? '#9a3412' : '#166534'}; border: 1px solid ${row.riskLevel === 'CRITICAL' ? '#f87171' : row.riskLevel === 'AT_RISK' ? '#fb923c' : '#4ade80'}; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 12px;">
              TRIP RISK: ${row.riskLevel}
            </span>
          </div>

          <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px;">
            <tr>
              <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Ranking Score:</strong> ${displayScore(row.score)}/100</td>
              <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Relative Fleet Rank:</strong> #${row.rank}/${allFleetRows.length || rows.length}</td>
              <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Risk Cao Nhất:</strong> ${row.maxRisk.toFixed(1)}</td>
              <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Khung rủi ro cao:</strong> ${row.criticalEvents}</td>
            </tr>
          </table>

          <div style="margin-bottom: 12px; background-color: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <h5 style="margin: 0 0 4px 0; color: #166534; font-size: 12px; font-weight: bold;">🟢 Ưu điểm:</h5>
            <ul style="margin: 0 0 8px 0; padding-left: 18px; font-size: 12px; color: #334155;">
              ${prosList.map(p => `<li>${normalizeScoreText(String(p), safeScore)}</li>`).join('')}
            </ul>
            <h5 style="margin: 0 0 4px 0; color: #991b1b; font-size: 12px; font-weight: bold;">🔴 Nhược điểm / Cảnh báo:</h5>
            <ul style="margin: 0 0 8px 0; padding-left: 18px; font-size: 12px; color: #334155;">
              ${consList.map(c => `<li>${normalizeScoreText(String(c), safeScore)}</li>`).join('')}
            </ul>
            <h5 style="margin: 0 0 4px 0; color: #9a3412; font-size: 12px; font-weight: bold;">💡 Đánh giá & Khuyến nghị:</h5>
            <p style="margin: 0; font-size: 12px; font-weight: bold; color: #1e293b;">${normalizeScoreText(String(evalText), safeScore)}</p>
          </div>

          <h4 style="margin: 8px 0 6px 0; color: #334155; font-size: 14px;">Lịch sử Cảnh báo Gần nhất:</h4>
          <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
            <thead>
              <tr style="background-color: #e2e8f0; text-align: left;">
                <th style="padding: 6px; border: 1px solid #cbd5e1;">Thời gian</th>
                <th style="padding: 6px; border: 1px solid #cbd5e1;">Loại Cảnh Báo</th>
                <th style="padding: 6px; border: 1px solid #cbd5e1;">Chi Tiết Số Liệu</th>
                <th style="padding: 6px; border: 1px solid #cbd5e1;">Mức Độ</th>
              </tr>
            </thead>
            <tbody>
              ${eventRowsFor(row.trip).map(evt => `
                <tr>
                  <td style="padding: 6px; border: 1px solid #cbd5e1; font-family: monospace;">${evt.time}</td>
                  <td style="padding: 6px; border: 1px solid #cbd5e1; font-weight: bold;">${evt.type}</td>
                  <td style="padding: 6px; border: 1px solid #cbd5e1; color: #475569;">${evt.detail}</td>
                  <td style="padding: 6px; border: 1px solid #cbd5e1; color: ${
                    evt.severity === 'Sự kiện nguy hiểm'
                      ? '#dc2626'
                      : evt.severity === 'Sự kiện cảnh báo'
                        ? '#d97706'
                        : '#16a34a'
                  }; font-weight: bold;">${evt.severity}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }).join('');

    const atRiskTrip = rows.find(r => r.riskLevel === 'CRITICAL' || r.riskLevel === 'AT_RISK');
    const exportComparisonRow = rows.length === 1 ? rows[0] : highestRankedRow;

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>${reportTitle}</title>
        <style>
          body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #0f172a; line-height: 1.5; padding: 30px; max-width: 900px; margin: 0 auto; }
          h1 { color: #0284c7; font-size: 24px; margin-bottom: 4px; border-bottom: 3px solid #0284c7; padding-bottom: 8px; }
          .header-meta { font-size: 12px; color: #64748b; margin-bottom: 20px; display: flex; justify-content: space-between; }
          .subtitle { font-size: 14px; color: #475569; margin-bottom: 24px; font-style: italic; }
          .section-title { font-size: 16px; font-weight: bold; color: #0f172a; border-left: 4px solid #0284c7; padding-left: 8px; margin: 24px 0 12px 0; }
          table.kpi-table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
          table.kpi-table th, table.kpi-table td { padding: 10px; border: 1px solid #cbd5e1; font-size: 13px; text-align: left; }
          table.kpi-table th { background-color: #0f172a; color: #ffffff; }
          .insight-box { background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 16px; margin-top: 20px; }
          .insight-box p { margin: 0; font-size: 13px; color: #0369a1; white-space: pre-line; }
          .footer { margin-top: 40px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 12px; }
        </style>
      </head>
      <body>
        <h1>${reportTitle}</h1>
        <div class="header-meta">
          <span><strong>DMS Safety AI Platform</strong> | Báo Cáo Phân Tích Trip</span>
          <span>Thời gian xuất: ${nowStr}</span>
        </div>
        <p class="subtitle">${subtitle}</p>

        ${isSafetyOverview ? `
          <div class="section-title">Fleet Summary</div>
          <table class="kpi-table">
            <tbody>
              <tr><td><strong>Fleet Status</strong></td><td>${fleetStatus}</td></tr>
              <tr><td><strong>Trips analyzed</strong></td><td>${rows.length}</td></tr>
              <tr><td><strong>Safe trips</strong></td><td>${safeTripCount}</td></tr>
              <tr><td><strong>Fleet Avg Ranking Score</strong></td><td>${displayScore(selectedFleetAverage)}/100</td></tr>
              <tr><td><strong>High-risk frames</strong></td><td>${selectedHighRiskFrames}</td></tr>
              <tr><td><strong>Review Priority</strong></td><td>${reviewPriorityPath}</td></tr>
            </tbody>
          </table>
        ` : ''}

        <div class="section-title">1. Tổng Quan Chỉ Số KPI Fleet</div>
        <table class="kpi-table">
          <thead>
            <tr>
              <th>Chỉ Số An Toàn</th>
              <th>${rows.length === 1 ? 'Trip Đang Xét' : 'Trung Bình Toàn Bộ Trip'}</th>
	              <th>${rows.length === 1 ? 'Trip Đang Xét' : 'Highest-Ranked Trip (Relative)'}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Tổng Điểm An Toàn</strong></td>
              <td>${(rows.length === 1 ? rows[0].score : fleetAverage).toFixed(1)}/100</td>
	              <td>${exportComparisonRow ? `${exportComparisonRow.trip_id} · ${exportComparisonRow.score.toFixed(1)}/100 · Still ${exportComparisonRow.riskLevel}` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>TTC / Rủi Ro Suy Suýt Va Chạm</strong></td>
              <td>${rows.reduce((sum, row) => sum + row.nearMissCount, 0)} lượt near-miss</td>
	              <td>${exportComparisonRow ? `${exportComparisonRow.nearMissCount} lượt` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Tỉ Lệ Mất Tập Trung (Distracted)</strong></td>
              <td>${(rows.reduce((sum, row) => sum + row.distractedPct, 0) / Math.max(rows.length, 1)).toFixed(1)}%</td>
	              <td>${exportComparisonRow ? `${exportComparisonRow.distractedPct.toFixed(1)}%` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Sự Kiện An Toàn (Bình thường)</strong></td>
              <td>${(rows.flatMap(r => eventRowsFor(r.trip)).filter(e => e.severity === 'Sự kiện an toàn').length / Math.max(rows.length, 1)).toFixed(0)} sự kiện</td>
	              <td>${exportComparisonRow ? `${eventRowsFor(exportComparisonRow.trip).filter(e => e.severity === 'Sự kiện an toàn').length} sự kiện` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Sự Kiện Cảnh Báo (Chú ý)</strong></td>
              <td>${(rows.flatMap(r => eventRowsFor(r.trip)).filter(e => e.severity === 'Sự kiện cảnh báo').length / Math.max(rows.length, 1)).toFixed(0)} sự kiện</td>
	              <td>${exportComparisonRow ? `${eventRowsFor(exportComparisonRow.trip).filter(e => e.severity === 'Sự kiện cảnh báo').length} sự kiện` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Sự Kiện Nguy Hiểm (Khẩn cấp)</strong></td>
              <td>${(rows.flatMap(r => eventRowsFor(r.trip)).filter(e => e.severity === 'Sự kiện nguy hiểm').length / Math.max(rows.length, 1)).toFixed(0)} sự kiện</td>
	              <td>${exportComparisonRow ? `${eventRowsFor(exportComparisonRow.trip).filter(e => e.severity === 'Sự kiện nguy hiểm').length} sự kiện` : 'N/A'}</td>
            </tr>
          </tbody>
        </table>

        <div class="section-title">2. Mức Sẵn Có Dữ Liệu Kỹ Thuật Trip</div>
        <table class="kpi-table">
          <thead>
            <tr>
              <th>Trip</th>
              <th>Brake Stress Estimate</th>
              <th>Tire Stress Estimate</th>
              <th>Thời gian (s)</th>
              <th>Mã Lỗi DTC (OBD-II)</th>
              <th>Inspection Triage</th>
              <th>Repair Cost / Downtime</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((row, idx) => {
              const model = reportForRow(reportModels, row.trip_id);
              const brakeWear = model?.maintenance.brakeStress ?? 0;
              const tireWear = model?.maintenance.tireStress ?? 0;
              const dtcCode = model?.maintenance.dtcCode ?? 'N/A';
              const serviceOverdue = model?.maintenance.priority ?? 'NORMAL';
              const estCost = `N/A — requires workshop inspection`;
              const downtime = model?.maintenance.estimatedDowntime ?? 'N/A';
              return `
                <tr>
                  <td><strong>TRIP ${String(idx + 1).padStart(2, '0')} (${row.trip_id})</strong></td>
                  <td style="color: #d97706; font-weight: bold;">${brakeWear}/100</td>
                  <td style="color: #0284c7; font-weight: bold;">${tireWear}/100</td>
                  <td>${row.trip.metadata?.duration_sec ?? 0}s</td>
                  <td style="font-family: monospace; color: ${row.riskLevel === 'CRITICAL' ? '#dc2626' : '#16a34a'}; font-weight: bold;">${dtcCode}</td>
                  <td>${serviceOverdue}</td>
                  <td>${estCost} | ~${downtime}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>

        <div class="section-title">3. Khuyến Nghị Review / Kiểm Tra Kỹ Thuật (Recommended - Not Created)</div>
        <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
          <strong style="color: #1d4ed8;">🛡 Safety Review Required Before Next Dispatch:</strong> ${atRiskTrip ? `Chuyến <strong>${atRiskTrip.trip_id}</strong> có risk cao nên cần review an toàn trước chuyến tiếp theo. Đây không phải kết luận hỏng hóc.` : `Không có trip nào cần safety review khẩn theo dữ liệu hiện tại.`}
        </div>
        <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
          <strong style="color: #9a3412;">⚠️ Technical Inspection Suggested:</strong> Kiểm tra cơ bản các trip WATCH/INSPECT theo DTC thật hoặc stress estimate. Chi phí sửa chữa để N/A cho tới khi có kiểm tra xưởng.
        </div>

        <div class="section-title">4. Chi Tiết Đánh Giá Theo Trip (${rows.length} trip)</div>
        ${rowsHTML}

        <div class="section-title">5. Khuyến Nghị & Insight Từ AI Copilot (Bedrock Engine)</div>
        <div class="insight-box">
          <p>${normalizeLongScoreText(copilotInsight).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
        </div>

        <div class="footer">
          Báo cáo tự động tạo bởi Hệ Thống Giám Sát Trip Safety DMS (VinFast Automotive Hackathon 2026).
        </div>
      </body>
      </html>
    `;
  };

  const handleExportPDF = async () => {
    setShowExportMenu(false);
    const tripLabel = rows.length === 1 ? rows[0].trip_id : 'Fleet';
    const fileName = `DMS_Fleet_Report_${tripLabel}_${new Date().toISOString().slice(0, 10)}.pdf`;

    // Expand all trip cards temporarily so entire detailed report is captured in screenshot
    const previousExpandedState = { ...expandedTrips };
    const allExpandedState: Record<string, boolean> = {};
    rows.forEach(r => { allExpandedState[r.trip_id] = true; });
    setExpandedTrips(allExpandedState);

    // Wait 200ms for React DOM to render all expanded cards
    await new Promise(resolve => setTimeout(resolve, 200));

    const targetElement = document.getElementById('copilot-report-print-target') || document.body;

    const opt = {
      margin: 5,
      filename: fileName,
      image: { type: 'jpeg' as const, quality: 0.98 },
      html2canvas: { 
        scale: 2, 
        useCORS: true, 
        backgroundColor: '#070A12',
        logging: false 
      },
      jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'portrait' as const }
    };

    try {
      await html2pdf().set(opt).from(targetElement).save();
      setDownloadSuccess(`Đã chụp toàn bộ màn hình giao diện & tải xuống file ${fileName} thành công!`);
    } catch (err) {
      console.error('PDF screenshot export error:', err);
    } finally {
      // Restore user's previous expand state
      setExpandedTrips(previousExpandedState);
      setTimeout(() => setDownloadSuccess(null), 4000);
    }
  };

  const handleExportWord = () => {
    setShowExportMenu(false);
    const htmlContent = generateReportHTML();

    const header = "<html xmlns:o='urn:schemas-microsoft-com:office:office' " +
      "xmlns:w='urn:schemas-microsoft-com:office:word' " +
      "xmlns='http://www.w3.org/TR/REC-html40'>" +
      "<head><meta charset='utf-8'><title>" + reportTitle + "</title></head><body>";
    const footer = "</body></html>";
    const sourceHTML = header + htmlContent + footer;

    const blob = new Blob(['\ufeff', sourceHTML], {
      type: 'application/msword;charset=utf-8'
    });

    const tripLabel = rows.length === 1 ? rows[0].trip_id : 'Fleet';
    const fileName = `DMS_Fleet_Report_${tripLabel}_${new Date().toISOString().slice(0, 10)}.doc`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);

    setDownloadSuccess(`Đã tải xuống báo cáo Word (${fileName}) thành công!`);
    setTimeout(() => setDownloadSuccess(null), 4000);
  };

  return (
    <div id="copilot-report-print-target" className="min-h-screen overflow-y-auto bg-[#070A12] px-6 py-7 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        {downloadSuccess && (
          <div className="flex items-center gap-2 rounded-lg border border-emerald-500/50 bg-emerald-950/80 px-4 py-3 text-sm font-bold text-emerald-200 shadow-lg">
            <Check className="h-5 w-5 text-emerald-400" />
            {downloadSuccess}
          </div>
        )}

        <header className="flex items-center justify-between gap-4 border-b border-[#1E293B] pb-5">
          <div className="flex items-start gap-4">
            <a
              href="/?view=MAP"
              className="flex items-center gap-2 rounded-xl bg-slate-800/80 px-3.5 py-3 text-xs font-bold text-slate-300 border border-slate-700 hover:bg-slate-700 hover:text-white transition-all shadow-md shrink-0"
              title="Quay lại Dashboard Trang Chủ"
            >
              <Eye className="h-4 w-4 text-sky-400" />
              <span>Trang Chủ Command</span>
            </a>
            <div className="grid h-12 w-12 place-items-center rounded-xl bg-sky-500/10 text-sky-300 shrink-0">
              {reportType === 'maintenance' ? <Wrench className="h-7 w-7" /> : <Shield className="h-7 w-7" />}
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight">{reportTitle}</h1>
              <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`${panel} flex items-center gap-3 px-4 py-2 text-sm text-slate-300`}>
              <CalendarDays className="h-4 w-4 text-slate-500" />
              03/08/2026 ~ 03/08/2026
            </div>
            <div className="relative" ref={menuRef}>
              <button 
                onClick={() => setShowExportMenu(!showExportMenu)}
                className={`${panel} flex items-center gap-2 px-4 py-2 text-sm font-bold text-slate-200 transition-colors hover:bg-slate-800 active:scale-95`}
              >
                <Download className="h-4 w-4 text-sky-400" />
                Export Report
              </button>

              {showExportMenu && (
                <div className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-lg border border-[#1E293B] bg-[#0F172A] p-1 shadow-2xl backdrop-blur-md">
                  <button
                    onClick={handleExportPDF}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium text-slate-200 transition-colors hover:bg-sky-500/10 hover:text-sky-400"
                  >
                    <FileDown className="h-4 w-4 text-red-400" />
                    <span>Xuất báo cáo PDF (.pdf)</span>
                  </button>
                  <button
                    onClick={handleExportWord}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium text-slate-200 transition-colors hover:bg-sky-500/10 hover:text-sky-400"
                  >
                    <FileCode className="h-4 w-4 text-blue-400" />
                    <span>Xuất báo cáo Word (.doc)</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {isSafetyOverview && (
          <section className={`${panel} p-5 space-y-4 border-red-500/30 bg-red-950/10`}>
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="text-xs font-black uppercase tracking-widest text-red-300">Fleet Summary</div>
                <h2 className="mt-1 text-xl font-black text-slate-100">Fleet Status: {fleetStatus}</h2>
                <p className="mt-1 max-w-4xl text-sm leading-relaxed text-slate-400">
                  Review priority shows lowest score / highest risk first. Relative rank shows highest Ranking Score first, so #1 does not mean safe when Trip Safety Risk is CRITICAL.
                </p>
              </div>
              <span className={`w-fit rounded border px-3 py-1 text-xs font-black ${severityClass(fleetStatus)}`}>
                TRIP RISK OVERVIEW: {fleetStatus}
              </span>
            </div>
            <div className="grid gap-3 md:grid-cols-5">
              <MiniMetric label="Trips analyzed" value={String(rows.length)} />
              <MiniMetric label="Safe trips" value={String(safeTripCount)} />
              <MiniMetric label="Fleet Avg Ranking Score" value={`${displayScore(selectedFleetAverage)}/100`} />
              <MiniMetric label="High-risk frames" value={String(selectedHighRiskFrames)} />
              <MiniMetric label="Highest-ranked trip" value={highestRankedRow ? `${highestRankedRow.trip_id} · ${displayScore(highestRankedRow.score)}/100` : 'N/A'} />
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3">
              <div className="mb-1 text-[10px] font-black uppercase tracking-widest text-slate-500">Review Priority</div>
              <div className="font-mono text-sm font-black text-red-200">{reviewPriorityPath || 'N/A'}</div>
            </div>
          </section>
        )}

        {/* --- SECTION 1: TOP ABSTRACT TRIP SUMMARY CARDS --- */}
        <section className={`${panel} p-4 space-y-3`}>
          {isSafetyOverview && (
            <div className="border-b border-slate-800 pb-3">
              <div className="text-xs font-black uppercase tracking-widest text-sky-300">Review Priority Trip Cards</div>
              <p className="mt-1 text-xs text-slate-400">Sorted by Review Priority, highest risk first. Relative Fleet Rank inside each card is the separate ranking-score order.</p>
            </div>
          )}
          <div className={`grid gap-4 ${columnClass(rows.length)}`}>
          {rows.map((row, index) => {
            const isExpanded = !!expandedTrips[row.trip_id];
            return (
              <div key={row.trip_id} className={`${panel} min-w-0 overflow-hidden p-4 ${index % 2 === 0 ? 'bg-sky-950/20' : 'bg-emerald-950/20'} transition-all`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                      <span className={`h-2.5 w-2.5 rounded-full ${index % 2 === 0 ? 'bg-sky-400' : 'bg-emerald-400'}`} />
                      TRIP {String(index + 1).padStart(2, '0')}
                    </div>
                    <h2 className="mt-2 truncate text-2xl font-black">{row.trip_id}</h2>
                    <p className="mt-1 truncate text-xs text-slate-400">{row.trip.metadata?.description ?? 'AI trip session'}</p>
                  </div>
                  <span className={`shrink-0 rounded border px-2 py-1 text-[10px] font-black ${severityClass(row.riskLevel)}`}>TRIP RISK: {row.riskLevel}</span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  {reportType === 'maintenance' ? (
                    <>
                      <MiniMetric label="Mã lỗi DTC" value={reportForRow(reportModels, row.trip_id)?.maintenance.dtcCode ?? 'N/A'} />
                      <MiniMetric label="Brake Stress Estimate" value={`${reportForRow(reportModels, row.trip_id)?.maintenance.brakeStress ?? 0}/100`} />
                      <MiniMetric label="Tire Stress Estimate" value={`${reportForRow(reportModels, row.trip_id)?.maintenance.tireStress ?? 0}/100`} />
                      <MiniMetric label="Inspection Triage" value={reportForRow(reportModels, row.trip_id)?.maintenance.priority ?? 'NORMAL'} />
                    </>
                  ) : (
                    <>
                      <MiniMetric label="Ranking Score" value={`${displayScore(row.score)}/100`} />
                      <MiniMetric label="Relative Fleet Rank" value={`#${row.rank}/${allFleetRows.length || rows.length}`} />
                      <MiniMetric label="Max Risk" value={row.maxRisk.toFixed(1)} />
                      <MiniMetric label="Khung rủi ro cao" value={String(row.criticalEvents)} />
                    </>
                  )}
                </div>
	                {reportType !== 'maintenance' && (
	                  <div className="mt-3 rounded border border-red-500/20 bg-red-950/20 px-3 py-2 text-[11px] font-bold leading-relaxed text-red-100">
	                    Rank ≠ safe · Still {row.riskLevel}
	                  </div>
	                )}

                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-xs gap-2">
                  <div className="flex items-center gap-2 text-slate-300 truncate">
                    <UserRound className="h-4 w-4 text-sky-400 shrink-0" />
                    <span className="truncate">{row.trip_id}</span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={`/?view=TRIP_DETAIL&trip_id=${row.trip_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 rounded-lg bg-emerald-600/20 px-2.5 py-1.5 font-bold text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600 hover:text-white transition-all active:scale-95"
                      title="Xem chi tiết hành trình Telemetry live tại Tab mới"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      <span>Trip Detail (Tab mới)</span>
                    </a>

                    <button
                      onClick={() => toggleTripExpand(row.trip_id)}
                      className="flex items-center gap-1.5 rounded-lg bg-sky-600/20 px-3 py-1.5 font-bold text-sky-300 border border-sky-500/30 hover:bg-sky-600 hover:text-white transition-all active:scale-95"
                    >
                      {isExpanded ? (
                        <>
                          <span>Thu gọn</span>
                          <ChevronUp className="h-4 w-4" />
                        </>
                      ) : (
                        <>
                          <span>Báo cáo trip</span>
                          <ChevronDown className="h-4 w-4" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
          </div>
        </section>

        {/* --- SECTION A & B: TRIP DETAILS SECTION (EXPANDED BY BÁO CÁO TRIP BUTTON OR SINGLE TRIP VIEW) --- */}
        {(rows.length === 1 || rows.some(r => expandedTrips[r.trip_id])) && (
          <section className={`${panel} p-5 space-y-4`}>
            {reportType === 'maintenance' ? (
              /* --- MAINTENANCE MODE: SAFETY-BASED INSPECTION TRIAGE --- */
              <>
                <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                  <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-amber-400">
                    <Wrench className="h-5 w-5" />
                    Mức Sẵn Có Dữ Liệu Kỹ Thuật Trip
                  </div>
                  <span className="rounded bg-amber-500/10 px-2.5 py-1 text-xs font-bold text-amber-300 border border-amber-500/20">
                    Safety-Based Inspection Triage
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((row, idx) => {
                    const model = reportForRow(reportModels, row.trip_id);
                    const harshCount = row.harshEvents;
                    const criticalCount = row.criticalEvents;
                    const speedingPct = row.speedingPct;
                    const logEvents = eventRowsFor(row.trip);
                    const brakeLogCount = harshCount;
                    const tireLogCount = logEvents.filter(e => e.type.toLowerCase().includes('tốc độ') || e.type.toLowerCase().includes('speed') || e.type.toLowerCase().includes('làn')).length;

                    const brakeWear = model?.maintenance.brakeStress ?? Math.min(100, Math.max(12, Math.round(15 + brakeLogCount * 3.5 + Math.max(0, row.maxRisk - 60) * 0.2)));
                    const tireWear = model?.maintenance.tireStress ?? Math.min(100, Math.max(10, Math.round(10 + speedingPct * 0.4 + tireLogCount * 2.0)));
                    const dtcCode = model?.maintenance.dtcCode ?? 'N/A';
                    const priority = model?.maintenance.priority ?? 'NORMAL';
                    const isRoutine = priority === 'NORMAL';
                    const serviceOverdue = priority === 'INSPECT' ? `INSPECT - DTC/stress vượt ngưỡng (${brakeWear}/100)` : priority === 'WATCH' ? `WATCH - safety review / kiểm tra cơ bản (${brakeWear}/100)` : 'NORMAL - theo lịch định kỳ';
                    const estCost = 'N/A - requires workshop inspection';
                    const downtime = model?.maintenance.estimatedDowntime ?? 'N/A';
                    const parts = 'N/A - chưa tích hợp kho phụ tùng';
                    const workOrderStatus = model?.maintenance.workOrderStatus ?? 'Recommended - not created';
                    const dtcDisplay = aiIsLoading ? `${aiLoadingCopy.dtc} (${dtcCode})` : dtcCode;
                    const serviceDisplay = aiIsLoading ? `${aiLoadingCopy.maintenanceStatus} (${serviceOverdue})` : serviceOverdue;
                    const partsDisplay = aiIsLoading ? `${aiLoadingCopy.parts} (${parts})` : parts;
                    const workOrderDisplay = aiIsLoading ? `${aiLoadingCopy.workOrder} (${workOrderStatus})` : workOrderStatus;

                    return (
                      <div key={row.trip_id} className="rounded-lg border border-amber-500/40 bg-[#0A0F1D] p-4 space-y-3 shadow-xl">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-amber-300 text-sm">TRIP {String(idx + 1).padStart(2, '0')} - {row.trip_id}</span>
                            <span className="text-[10px] text-slate-400">({row.trip_id})</span>
                          </div>
                          <span className={`text-xs font-black px-2 py-0.5 rounded ${isRoutine ? 'bg-sky-500/20 text-sky-300' : 'bg-red-500/20 text-red-300 border border-red-500/40'}`}>
                            {serviceDisplay}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="space-y-1">
                            <div className="flex justify-between text-slate-400">
                              <span>Brake Stress Estimate:</span>
                              <span className={`font-mono font-bold ${brakeWear > 70 ? 'text-red-400' : brakeWear > 40 ? 'text-amber-300' : 'text-emerald-400'}`}>{brakeWear}/100</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${brakeWear > 70 ? 'bg-red-500' : brakeWear > 40 ? 'bg-amber-400' : 'bg-emerald-400'}`} style={{ width: `${brakeWear}%` }} />
                            </div>
                            <span className="text-[9px] text-slate-400 block">
                              Estimate: Cơ sở 15% + {brakeLogCount} phanh/lái gắt thật (+{(brakeLogCount * 3.5).toFixed(1)}%) + max risk {row.maxRisk.toFixed(1)}. Khung rủi ro cao ({criticalCount}) là safety context, không phải bằng chứng phanh/lốp hỏng.
                            </span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-slate-400">
                              <span>Tire Stress Estimate:</span>
                              <span className={`font-mono font-bold ${tireWear > 70 ? 'text-red-400' : 'text-sky-300'}`}>{tireWear}/100</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-sky-400 h-full rounded-full" style={{ width: `${tireWear}%` }} />
                            </div>
                            <span className="text-[9px] text-slate-400 block">
                              Estimate: Cơ sở 10% + {speedingPct.toFixed(1)}% quá tốc độ (+{(speedingPct * 0.4).toFixed(1)}%) + {tireLogCount} lần lái gấp (+{(tireLogCount * 2.0).toFixed(1)}%). Không có cảm biến áp suất/mòn lốp trong dataset hiện tại.
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t border-slate-800/80 pt-2">
                          <div><span className="text-slate-400">Odometer hiện tại:</span> <b className="font-mono text-slate-200">N/A</b></div>
                          <div><span className="text-slate-400">Engine Hours:</span> <b className="font-mono text-slate-200">N/A</b></div>
                          <div><span className="text-slate-400">Inspection triage:</span> <b className="font-mono text-amber-300">{isRoutine ? 'Theo lịch định kỳ' : 'Cần review/kiểm tra'}</b></div>
                          <div><span className="text-slate-400">Mã lỗi OBD-II (DTC):</span> <b className={`font-mono ${dtcCode === 'N/A' ? 'text-emerald-400' : 'text-red-400 font-bold'}`}>{dtcDisplay}</b></div>
                          <div><span className="text-slate-400">Trạng thái Phụ tùng:</span> <b className="text-slate-200">{partsDisplay}</b></div>
                          <div><span className="text-slate-400">Trạng thái Work Order:</span> <b className="font-mono text-sky-300">{workOrderDisplay}</b></div>
                        </div>

                        <div className="flex items-center justify-between bg-slate-900/90 rounded p-2 text-xs border border-slate-800">
                          <span className="text-slate-400">Repair Cost & Downtime:</span>
                          <span className="font-bold text-amber-300 font-mono">{estCost} | Downtime {downtime}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              /* --- SAFETY MODE: TRIP SAFETY BEHAVIOR & RISK METRICS --- */
              <>
                <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                  <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-sky-400">
                    <UserRound className="h-5 w-5" />
                    Chỉ Số Hành Vi & Điểm An Toàn Chi Tiết Theo Trip
                  </div>
                  <span className="rounded bg-sky-500/10 px-2.5 py-1 text-xs font-bold text-sky-300 border border-sky-500/20">
                    Safety Evaluation Mode
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((row, idx) => (
                    <div key={row.trip_id} className="rounded-lg border border-sky-500/40 bg-[#0A0F1D] p-4 space-y-3 shadow-xl">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sky-300 text-sm">TRIP {String(idx + 1).padStart(2, '0')} - {row.trip_id}</span>
                          <span className="text-[10px] text-slate-400">({row.trip_id})</span>
                        </div>
                        <span className={`text-xs font-black px-2 py-0.5 rounded ${row.score >= 80 ? 'bg-emerald-500/20 text-emerald-300' : row.score >= 60 ? 'bg-amber-500/20 text-amber-300' : 'bg-red-500/20 text-red-300'}`}>
                          Ranking Score: {displayScore(row.score)}/100
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="space-y-1">
                          <div className="flex justify-between text-slate-400">
                            <span>Tỷ lệ xao nhãng:</span>
                            <span className="font-mono text-amber-300 font-bold">{row.distractedPct.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-amber-400 h-full rounded-full" style={{ width: `${Math.min(100, row.distractedPct)}%` }} />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-slate-400">
                            <span>Vi phạm quá tốc độ:</span>
                            <span className="font-mono text-sky-300 font-bold">{row.speedingPct.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-sky-400 h-full rounded-full" style={{ width: `${Math.min(100, row.speedingPct)}%` }} />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t border-slate-800/80 pt-2">
                        <div><span className="text-slate-400">Hành vi lái gắt:</span> <b className="font-mono text-slate-200">{row.harshEvents} sự kiện</b></div>
                        <div><span className="text-slate-400">Near miss / TTC risk:</span> <b className="font-mono text-slate-200">{row.nearMissCount} sự kiện</b></div>
                        <div><span className="text-slate-400">Khung rủi ro cao:</span> <b className="font-mono text-amber-300">{row.criticalEvents} frames</b></div>
                        <div><span className="text-slate-400">Mức rủi ro cực đại:</span> <b className="font-mono text-red-400 font-bold">{row.maxRisk.toFixed(1)}/100</b></div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        )}

        {/* --- SECTION C: WORKFLOW & ACTION ORDERS (DÀNH RIÊNG CHO AN TOÀN VÀ BẢO TRÌ) --- */}
        <section className={`${panel} p-5 space-y-3`}>
          {reportType === 'maintenance' ? (
            /* --- MAINTENANCE ACTION ORDERS --- */
            <>
              <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-amber-400 border-b border-[#1E293B] pb-3">
                <Wrench className="h-5 w-5" />
                Khuyến Nghị Review / Kiểm Tra Kỹ Thuật (Recommended - Not Created)
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {(() => {
                  const activeModels = rows.map(r => reportForRow(reportModels, r.trip_id)).filter(Boolean) as VehicleReportModel[];
                  const criticalVehicles = activeModels.filter(m => m.maintenance.priority === 'INSPECT');
                  const warningVehicles = activeModels.filter(m => m.maintenance.priority === 'WATCH');
                  const normalVehicles = activeModels.filter(m => m.maintenance.priority === 'NORMAL');
                  const reviewText = aiIsLoading
                    ? aiLoadingCopy.doNotDrive
                    : criticalVehicles.length > 0
                    ? `Recommended - not created: review an toàn và kiểm tra kỹ thuật cho [${criticalVehicles.map(v => v.tripId).join(', ')}] do DTC thật hoặc stress estimate vượt ngưỡng INSPECT.`
                    : 'Không có trip nào trong báo cáo này có DTC/stress estimate vượt ngưỡng INSPECT.';
                  const inspectionText = aiIsLoading
                    ? aiLoadingCopy.priority48h
                    : warningVehicles.length > 0
                    ? `Recommended - not created: kiểm tra kỹ thuật cơ bản / safety review cho [${warningVehicles.map(v => v.tripId).join(', ')}] trước chuyến tiếp theo. Priority driven by trip safety risk, not confirmed mechanical failure.`
                    : 'Không có trip WATCH cần kiểm tra kỹ thuật ưu tiên trong báo cáo này.';
                  const routineText = normalVehicles.length > 0
                    ? `Recommended - not created: trip [${normalVehicles.map(v => v.tripId).join(', ')}] duy trì lịch review định kỳ.`
                    : 'Tất cả các trip trong báo cáo này đều cần theo dõi hoặc kiểm tra kỹ thuật.';

                  return (
                    <>
                      <div className="rounded-lg border border-sky-500/30 bg-sky-950/20 p-3 space-y-1">
                        <span className="font-bold text-sky-300 uppercase block">🛡 Safety Review Required Before Next Dispatch</span>
                        <p className="text-slate-300 leading-relaxed">{reviewText}</p>
                      </div>
                      <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 space-y-1">
                        <span className="font-bold text-amber-400 uppercase block">⚠️ Technical Inspection Suggested</span>
                        <p className="text-slate-300 leading-relaxed">{inspectionText}</p>
                      </div>
                      <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-3 space-y-1">
                        <span className="font-bold text-emerald-400 uppercase block">✅ Routine Schedule</span>
                        <p className="text-slate-300 leading-relaxed">{routineText}</p>
                      </div>
                    </>
                  );
                })()}
              </div>
            </>
          ) : (
            /* --- SAFETY ACTION ORDERS --- */
            <>
              <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-sky-400 border-b border-[#1E293B] pb-3">
                <Shield className="h-5 w-5" />
                Khuyến Nghị Can Thiệp An Toàn Theo Trip
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {(() => {
                  const highRiskTrips = rows.filter(r => r.score < 60 || r.distractedPct > 30 || r.maxRisk >= 80 || r.criticalEvents > 0);
                  const midRiskTrips = rows.filter(r => r.score >= 60 && r.score < 80);
                  const safeTrips = rows.filter(r => r.score >= 80);
                  const safetyReasonFor = (r: typeof rows[number]) => {
                    const reasons = [];
                    if (r.maxRisk >= 80) reasons.push(`max risk ${r.maxRisk.toFixed(1)}/100`);
                    if (r.criticalEvents > 0) reasons.push(`${r.criticalEvents} khung rủi ro cao`);
                    if (r.distractedPct > 0) reasons.push(`${r.distractedPct.toFixed(1)}% xao nhãng`);
                    if (r.harshEvents > 0) reasons.push(`${r.harshEvents} phanh/lái gắt`);
                    if (r.nearMissCount > 0) reasons.push(`${r.nearMissCount} near miss/TTC thấp`);
                    return reasons.join(', ') || 'điểm ranking thấp';
                  };

                  const reviewUrgent = aiIsLoading
                    ? aiLoadingCopy.coaching
                    : highRiskTrips.length > 0
                    ? `Review priority: ${highRiskTrips.map(v => v.trip_id).join(' → ')}. All trips are ${fleetStatus}; main contributors are high average risk, max risk 100, and high-risk frame exposure.`
                    : 'Tất cả trip đạt ngưỡng điểm an toàn chấp nhận được.';

                  const briefingText = aiIsLoading
                    ? aiLoadingCopy.priority48h
                    : midRiskTrips.length > 0
                    ? `Safety briefing / coaching nhẹ sau khi review cho trip [${midRiskTrips.map(v => v.trip_id).join(', ')}].`
                    : 'Không có trip nào ở ngưỡng cảnh báo trung bình.';

                  const rewardText = aiIsLoading
                    ? aiLoadingCopy.reward
                    : safeTrips.length > 0
                    ? `Đề xuất dùng trip [${safeTrips.map(v => v.trip_id).join(', ')}] làm benchmark an toàn tương đối trong batch.`
                    : 'Cần nỗ lực cải thiện chỉ số an toàn toàn fleet.';

                  return (
                    <>
                      <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-3 space-y-1">
                        <span className="font-bold text-red-400 uppercase block">🛑 Safety Review Bắt Buộc Trước Chuyến Tiếp Theo</span>
                        <p className="text-slate-300 leading-relaxed">{reviewUrgent}</p>
                      </div>
                      <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 space-y-1">
                        <span className="font-bold text-amber-400 uppercase block">⚠️ Safety Briefing Sau Review</span>
                        <p className="text-slate-300 leading-relaxed">{briefingText}</p>
                      </div>
                      <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-3 space-y-1">
                        <span className="font-bold text-emerald-400 uppercase block">🏆 Benchmark Trip Tương Đối</span>
                        <p className="text-slate-300 leading-relaxed">{rewardText}</p>
                      </div>
                    </>
                  );
                })()}
              </div>
            </>
          )}
        </section>

        <section className={`${panel} overflow-hidden`}>
          {(() => {
            const activeExpandedRows = rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]);
            const isSingleExpanded = activeExpandedRows.length === 1;
            const targetRow = isSingleExpanded ? activeExpandedRows[0] : null;

            const allFleetEvents = allFleetRows.flatMap(r => eventRowsFor(r.trip));
            const fleetSafeCountAvg = allFleetEvents.filter(e => e.severity === 'Sự kiện an toàn').length / Math.max(allFleetRows.length, 1);
            const fleetWarningCountAvg = allFleetEvents.filter(e => e.severity === 'Sự kiện cảnh báo').length / Math.max(allFleetRows.length, 1);
            const fleetDangerCountAvg = allFleetEvents.filter(e => e.severity === 'Sự kiện nguy hiểm').length / Math.max(allFleetRows.length, 1);

            const fleetNearMissAvg = allFleetRows.reduce((sum, row) => sum + row.nearMissCount, 0) / Math.max(allFleetRows.length, 1);
            const fleetDistractionAvg = allFleetRows.reduce((sum, row) => sum + row.distractedPct, 0) / Math.max(allFleetRows.length, 1);

            const comparisonRow = targetRow ?? highestRankedRow;
            const targetEvents = comparisonRow ? eventRowsFor(comparisonRow.trip) : [];
            const targetSafe = targetEvents.filter(e => e.severity === 'Sự kiện an toàn').length;
            const targetWarning = targetEvents.filter(e => e.severity === 'Sự kiện cảnh báo').length;
            const targetDanger = targetEvents.filter(e => e.severity === 'Sự kiện nguy hiểm').length;

            const column2Header = targetRow ? `Trip ${targetRow.trip_id}` : 'Highest-ranked trip (relative)';

            return (
              <>
                <div className="grid grid-cols-[1fr_180px_200px] border-b border-[#1E293B] px-5 py-4 text-xs font-black uppercase tracking-widest text-slate-400">
                  <span>Safety KPI Context</span>
                  <span className="text-center">Fleet Average</span>
                  <span className="text-center text-sky-400">{column2Header}</span>
                </div>
                {[
                  ['Trip', `${rows.length} trips`, comparisonRow ? `${comparisonRow.trip_id} · Still ${comparisonRow.riskLevel}` : 'N/A'],
                  ['Điểm an toàn ranking', `${fleetAverage.toFixed(1)}/100`, comparisonRow ? `${comparisonRow.score.toFixed(1)}/100` : 'N/A'],
                  ['TTC / near miss risk', `${fleetNearMissAvg.toFixed(1)} near misses`, comparisonRow ? `${comparisonRow.nearMissCount} near misses` : 'N/A'],
                  ['Distraction theo trip', `${fleetDistractionAvg.toFixed(1)}% distracted`, comparisonRow ? `${comparisonRow.distractedPct.toFixed(1)}% distracted` : 'N/A'],
                  ['Sự kiện an toàn (Bình thường)', `${fleetSafeCountAvg.toFixed(1)} sự kiện`, `${targetSafe} sự kiện`],
                  ['Sự kiện cảnh báo (Chú ý)', `${fleetWarningCountAvg.toFixed(1)} sự kiện`, `${targetWarning} sự kiện`],
                  ['Sự kiện nguy hiểm (Khẩn cấp)', `${fleetDangerCountAvg.toFixed(1)} sự kiện`, `${targetDanger} sự kiện`],
                ].map(([label, avg, targetVal]) => (
                  <div key={label} className="grid grid-cols-[1fr_180px_200px] border-b border-[#1E293B] px-5 py-4 text-sm">
                    <span className="font-bold text-slate-200">{label}</span>
                    <span className="text-center font-mono text-sky-300">{avg}</span>
                    <span className="text-center font-mono text-emerald-300 font-bold">{targetVal}</span>
                  </div>
                ))}
              </>
            );
          })()}
        </section>

        {(rows.length === 1 || rows.some(r => expandedTrips[r.trip_id])) && (
          <section className={`grid gap-4 ${columnClass(rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).length)}`}>
            {rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((row) => {
              const events = eventRowsFor(row.trip);
              const isMaint = reportType === 'maintenance';
              return (
                <div key={row.trip_id} className={`${panel} overflow-hidden`}>
                  <div className="flex items-center justify-between border-b border-[#1E293B] px-4 py-3">
                    <h3 className="truncate text-sm font-black text-slate-100 flex items-center gap-2">
                      {isMaint ? <Wrench className="h-4 w-4 text-amber-400" /> : null}
                      <span>{isMaint ? `Nhật ký Log chi tiết của trip ${row.trip_id} (+% hao mòn phanh & lốp)` : `Nhật ký sự kiện của trip ${row.trip_id}`}</span>
                    </h3>
                    <span className="text-xs font-bold text-amber-400 font-mono">{events.length} sự kiện log</span>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    <div className={`grid ${isMaint ? 'grid-cols-[70px_1fr_130px_90px]' : 'grid-cols-[70px_1fr_82px]'} text-xs`}>
                      {events.map((event, idx) => {
                        let wearImpactBadge = null;
                        if (isMaint) {
                          if (event.type.toLowerCase().includes('phanh') || event.type.toLowerCase().includes('brake')) {
                            wearImpactBadge = <span className="font-bold text-red-400 bg-red-950/60 px-1.5 py-0.5 rounded border border-red-800/60">+3.5% phanh</span>;
                          } else if (event.type.toLowerCase().includes('tốc độ') || event.type.toLowerCase().includes('speed') || event.type.toLowerCase().includes('làn')) {
                            wearImpactBadge = <span className="font-bold text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800/60">+2.0% lốp</span>;
                          } else {
                            wearImpactBadge = <span className="text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded">không cộng hao mòn</span>;
                          }
                        }

                        return (
                          <React.Fragment key={`${event.time}-${event.type}-${idx}`}>
                            <span className="border-b border-[#1E293B] px-3 py-2 font-mono text-slate-400">{event.time}</span>
                            <span className="border-b border-[#1E293B] px-3 py-2 text-slate-300">
                              <b className="block text-slate-100">{event.type}</b>
                              {event.detail}
                            </span>
                            {isMaint && (
                              <span className="border-b border-[#1E293B] px-2 py-2 text-center text-[10px] font-mono flex items-center justify-center">
                                {wearImpactBadge}
                              </span>
                            )}
                            <span className={`border-b border-[#1E293B] px-3 py-2 text-center text-[11px] font-bold ${
                              event.severity === 'Sự kiện nguy hiểm'
                                ? 'text-red-400'
                                : event.severity === 'Sự kiện cảnh báo'
                                  ? 'text-amber-400'
                                  : 'text-emerald-400'
                            }`}>
                              {event.severity}
                            </span>
                          </React.Fragment>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </section>
        )}

        {/* --- SECTION 4A: FLEET OVERVIEW / SINGLE TRIP SUMMARY (ĐỘNG THEO CHẾ ĐỘ XEM) --- */}
        <section className={`${panel} p-5 space-y-4`}>
          <div className="flex flex-col gap-2 border-b border-slate-800 pb-3 md:flex-row md:items-start md:justify-between">
            <div className="flex min-w-0 items-start gap-2 text-xs font-black uppercase tracking-widest text-slate-400">
              <FileText className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
              <span className="min-w-0 text-sky-300">
                {rows.length === 1
                  ? `${reportType === 'maintenance' ? 'Inspection triage detail' : 'Đánh giá an toàn chi tiết'} - ${rows[0].trip_id}`
                  : `${reportType === 'maintenance' ? 'Inspection triage toàn fleet' : 'Đánh giá an toàn toàn fleet'} (Statistical Evaluation)`}
              </span>
            </div>
            <span className={`w-fit shrink-0 rounded border px-2 py-0.5 font-mono text-[10px] ${aiStatusClass(aiInsightStatus)}`}>
              {aiStatusLabel(aiInsightStatus)}
            </span>
          </div>

          {/* Quick Aggregate Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Trip Ranking Score' : 'Fleet Ranking Score'}</span>
              <span className="text-xl font-black font-mono text-sky-400 mt-1 block">{(rows.length === 1 ? rows[0].score : fleetAverage).toFixed(1)}/100</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Trip đang đánh giá' : 'Trip ít rủi ro nhất'}</span>
              <span className="text-sm font-bold font-mono text-emerald-400 mt-1 block truncate">
                {rows[0] ? `${rows[0].trip_id} (${displayScore(rows[0].score)}/100)` : 'N/A'}
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Hành vi lái gắt chuyến' : 'Tổng hành vi lái gắt'}</span>
              <span className="text-xl font-black font-mono text-amber-400 mt-1 block">
                {rows.reduce((sum, r) => sum + r.harshEvents, 0)} lần
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Mức độ rủi ro trip' : 'Phân loại rủi ro chính'}</span>
              <span className="text-sm font-bold font-mono text-red-400 mt-1 block truncate">
                {rows.length === 1 ? rows[0].riskLevel : `${rows.filter(r => r.riskLevel === 'CRITICAL' || r.riskLevel === 'AT_RISK').length} trip rủi ro`}
              </span>
            </div>
          </div>

          <div className="rounded-lg bg-slate-950/80 p-4 border border-slate-800/80 leading-relaxed text-sm text-slate-200">
            {aiInsightStatus !== 'validated' && (
              <div className="mb-3 rounded border border-sky-500/20 bg-sky-950/20 px-3 py-2 text-xs font-semibold text-sky-200">
                Đánh giá hiện tại lấy từ JSON/local AI. Bedrock đang chạy nền; nếu phản hồi hợp lệ, nhận xét AI sẽ được cập nhật sau.
              </div>
            )}
            <p className="whitespace-pre-line font-medium leading-relaxed">
              {normalizeLongScoreText(copilotInsight || aiLoadingCopy.fleet)}
            </p>
          </div>
        </section>

        {/* --- SECTION 4B: INDIVIDUAL DETAILED TRIP AI INSIGHTS (ƯU ĐIỂM, NHƯỢC ĐIỂM / CHẨN ĐOÁN KỸ THUẬT BEDROCK) --- */}
        {(rows.length === 1 || rows.some(r => expandedTrips[r.trip_id])) && rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((expandedRow) => {
          const tripId = expandedRow.trip_id;
          const tripAi = aiTripInsights[tripId];
          const model = reportForRow(reportModels, tripId);
          const safeScore = expandedRow.score;
          const isMaint = reportType === 'maintenance';

          const logEvents = eventRowsFor(expandedRow.trip);
          const brakeLogCount = expandedRow.harshEvents;
          const tireLogCount = logEvents.filter(e => e.type.toLowerCase().includes('tốc độ') || e.type.toLowerCase().includes('speed') || e.type.toLowerCase().includes('làn')).length;
          const speedingPct = expandedRow.speedingPct;

          const brakeWear = model?.maintenance.brakeStress ?? Math.min(100, Math.max(12, Math.round(15 + brakeLogCount * 3.5 + Math.max(0, expandedRow.maxRisk - 60) * 0.2)));
          const tireWear = model?.maintenance.tireStress ?? Math.min(100, Math.max(10, Math.round(10 + speedingPct * 0.4 + tireLogCount * 2.0)));
          const dtcCode = model?.maintenance.dtcCode ?? 'N/A';
          const hasRealDtc = dtcCode !== 'N/A';

          let defaultPros: string[] = [];
          let defaultCons: string[] = [];

          if (isMaint) {
            defaultPros = [
              `DTC hiện tại: ${dtcCode}. Odometer, engine hours, áp suất lốp và cảm biến mòn phanh chưa có trong dataset.`,
              brakeWear < 50 && tireWear < 50
                ? `Brake/Tire Stress Estimate đang thấp (${brakeWear}/100, ${tireWear}/100); chưa đủ bằng chứng kết luận lỗi cơ khí.`
                : `Stress estimate cần được dùng như tín hiệu triage, không phải chẩn đoán hỏng hóc.`
            ];
            defaultCons = [
              hasRealDtc ? `Phát hiện mã lỗi OBD-II từ dữ liệu trip: ${dtcCode}.` : `Không có DTC thật trong dữ liệu; không được kết luận lỗi kỹ thuật nếu chỉ dựa trên safety telemetry.`,
              speedingPct > 0
                ? `Tỷ lệ quá tốc độ ở mức ${speedingPct.toFixed(1)}% chỉ tạo Tire Stress Estimate ${tireWear}/100, cần kiểm tra thực tế trước khi kết luận mòn lốp.`
                : brakeLogCount > 0
                  ? `Ghi nhận ${brakeLogCount} lượt lái/phanh gắt từ behavior_flags; đây là lý do đề xuất kiểm tra cơ bản, chưa phải xác nhận hỏng phanh.`
                  : `Không ghi nhận phanh/lái gắt thật trong JSON; ưu tiên review nếu có là do safety risk/frame-level risk, không phải lỗi kỹ thuật xác nhận.`
            ];
          } else {
            // STRICT SAFETY LOGIC RULES
            const isCriticalRisk = safeScore < 60 || expandedRow.riskLevel === 'CRITICAL' || expandedRow.distractedPct > 35 || expandedRow.fatigueEvents > 0;
            const hasHighDistraction = expandedRow.distractedPct > 25;
            const hasFatigue = expandedRow.fatigueEvents > 0;

            if (isCriticalRisk) {
              // No positive pros for critical-risk trips.
              defaultPros = [`Chưa ghi nhận hành vi an toàn tiêu biểu vì trip đang ở nhóm rủi ro nghiêm trọng.`];
            } else {
              if (safeScore >= 80 && !hasHighDistraction && !hasFatigue) {
                defaultPros.push(`Ranking Score thuộc nhóm xuất sắc (${displayScore(safeScore)}/100), kiểm soát rủi ro cực tốt.`);
              } else if (safeScore >= 60 && !hasHighDistraction) {
                defaultPros.push(`Ranking Score ở mức trung bình khá (${displayScore(safeScore)}/100).`);
              }

              if (speedingPct === 0) {
                defaultPros.push(`Tuân thủ giới hạn tốc độ tuyệt đối (0.0%).`);
              }
              if (brakeLogCount === 0) {
                defaultPros.push(`Trip không ghi nhận tình huống phanh gấp nguy hiểm.`);
              }
            }

            // CONS ALWAYS DETAILED
            if (safeScore < 60) {
              defaultCons.push(`Điểm an toàn thuộc nhóm cực kỳ nguy hiểm (${displayScore(safeScore)}/100).`);
            }
            if (speedingPct > 0) {
              defaultCons.push(`Vi phạm tốc độ ở mức ${speedingPct.toFixed(1)}%, gây nguy hiểm nghiêm trọng.`);
            }
            if (brakeLogCount > 0) {
              defaultCons.push(`Ghi nhận ${brakeLogCount} sự kiện phanh gấp, dấu hiệu thiếu quan sát hoặc không giữ khoảng cách an toàn.`);
            }
            if (hasHighDistraction) {
              defaultCons.push(`🚨 CẢNH BÁO NGHIÊM TRỌNG: Tỷ lệ xao nhãng mất tập trung lên tới ${expandedRow.distractedPct.toFixed(1)}% (cao gấp đôi mức trung bình Fleet ${fleetAverage.toFixed(1)}%), nguy cơ va chạm rất cao.`);
            } else if (expandedRow.distractedPct > 5) {
              defaultCons.push(`Driver state distracted chiếm ${expandedRow.distractedPct.toFixed(1)}% thời gian trong trip.`);
            }
            if (hasFatigue) {
              defaultCons.push(`🚨 CẢNH BÁO VI NGỦ: Phát hiện ${expandedRow.fatigueEvents} sự kiện vi ngủ/ngáp nguy hiểm.`);
            }
            if (expandedRow.criticalEvents > 0) {
              defaultCons.push(`Phát hiện ${expandedRow.criticalEvents} khung hình rủi ro cao theo risk.final_risk_score; đây là frame-level risk, không đồng nghĩa với ${expandedRow.criticalEvents} sự kiện phanh gấp/near-miss.`);
            }

            if (defaultCons.length === 0) {
              defaultCons.push(`Cần tiếp tục duy trì và nâng cao chỉ số tập trung.`);
            }
          }

          // STRICT PRIORITY MATCHING
          const defaultEval = isMaint
            ? (model?.maintenance.priority === 'INSPECT'
                ? `TRIP ${tripId}: INSPECT - Recommended - not created. Kiểm tra kỹ thuật vì có DTC thật hoặc stress estimate vượt ngưỡng. Không kết luận hỏng phanh/lốp nếu chưa có dữ liệu xưởng.`
                : model?.maintenance.priority === 'WATCH'
                  ? `TRIP ${tripId}: WATCH - Recommended - not created. Safety review / kiểm tra kỹ thuật cơ bản trước chuyến tiếp theo; chi phí N/A cho tới khi có workshop inspection.`
                  : `TRIP ${tripId}: NORMAL - duy trì lịch định kỳ, không có DTC thật hoặc stress estimate vượt ngưỡng trong dữ liệu.`)
            : (safeScore >= 80 
                ? `🏆 BENCHMARK: Trip ${tripId} là trip có hành vi an toàn tương đối tốt trong batch hiện tại.`
                : safeScore >= 60
                ? `⚠️ NHẮC NHỞ: Trip ${tripId} cần review các hành vi vi phạm để nâng Ranking Score.`
                : `🛑 SAFETY REVIEW REQUIRED BEFORE NEXT DISPATCH: Trip ${tripId} có rủi ro nghiêm trọng (Ranking Score: ${displayScore(safeScore)}/100). Review high-risk segments trước; không kết luận lỗi vận hành nếu chưa xác minh evidence từ frame review.`);

          const prosList: string[] = aiInsightStatus === 'validated'
            ? (tripAi?.pros ?? defaultPros)
            : defaultPros;
          const consList: string[] = aiInsightStatus === 'validated'
            ? (tripAi?.cons ?? tripAi?.concerns ?? defaultCons)
            : defaultCons;
          const evaluationText: string = aiInsightStatus === 'validated'
            ? (tripAi?.evaluation ?? tripAi?.recommendation ?? defaultEval)
            : defaultEval;
          const insightSourceLabel = aiInsightStatus === 'validated'
            ? 'Bedrock insight đã xác thực'
            : aiInsightStatus === 'loading'
              ? 'Đánh giá JSON/local AI - Bedrock chạy nền'
              : 'Đánh giá JSON/local AI - chờ Bedrock hợp lệ';

          return (
            <section key={`insight-${tripId}`} className={`${panel} p-5 space-y-4 border-amber-500/40 bg-amber-950/10 shadow-2xl`}>
              <div className="flex flex-col gap-2 border-b border-amber-900/60 pb-3 md:flex-row md:items-start md:justify-between">
                <div className="flex min-w-0 items-start gap-2 text-sm font-black uppercase tracking-widest text-amber-300">
                  {isMaint ? <Wrench className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" /> : <UserRound className="mt-0.5 h-5 w-5 shrink-0 text-sky-400" />}
                  <span className="min-w-0">
                    {isMaint ? 'Inspection triage detail' : 'Đánh giá an toàn chi tiết'} - {tripId}
                    <span className="ml-2 text-[10px] text-slate-400 normal-case tracking-normal">(trip-level)</span>
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`w-fit rounded border px-2 py-0.5 font-mono text-[10px] ${aiStatusClass(aiInsightStatus)}`}>
                    {insightSourceLabel}
                  </span>
                  <span className={`w-fit rounded px-2.5 py-1 font-mono text-xs font-extrabold ${
                    safeScore >= 80 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : safeScore >= 60 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-red-500/20 text-red-300 border border-red-500/30'
                  }`}>
                    {isMaint ? `Ưu tiên: ${reportForRow(reportModels, tripId)?.maintenance.priority ?? 'N/A'}` : `Ranking Score: ${displayScore(safeScore)}/100`}
                  </span>
                </div>
              </div>

              <div className="space-y-3 bg-[#0A0F1D] p-4 rounded-lg border border-amber-900/40 text-xs leading-relaxed">
                <div className="rounded border border-slate-800 bg-slate-950/70 px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-slate-400">
                  {insightSourceLabel}
                </div>
                {/* 🟢 Ưu điểm / Điểm kỹ thuật tốt */}
                <div className="space-y-1.5">
                  <h4 className="font-bold text-emerald-400 text-xs uppercase flex items-center gap-1.5">
                    <span>{isMaint ? '🟢 Dữ Liệu Kỹ Thuật Hiện Có:' : '🟢 Ưu điểm:'}</span>
                  </h4>
                  <ul className="space-y-1 list-disc list-inside text-slate-200 pl-1">
                    {prosList.map((pro, idx) => (
                      <li key={idx} className="leading-relaxed">
                        <span>{normalizeScoreText(String(pro), safeScore)}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 🔴 Nhược điểm / Nguyên nhân tạo ưu tiên kiểm tra kỹ thuật */}
                <div className="space-y-1.5 border-t border-slate-800/80 pt-3">
                  <h4 className="font-bold text-red-400 text-xs uppercase flex items-center gap-1.5">
                    <span>{isMaint ? '🔴 Nguyên Nhân Tạo Ưu Tiên Kiểm Tra Kỹ Thuật:' : '🔴 Nhược điểm:'}</span>
                  </h4>
                  <ul className="space-y-1 list-disc list-inside text-slate-200 pl-1">
                    {consList.map((con, idx) => (
                      <li key={idx} className="leading-relaxed">
                        <span>{normalizeScoreText(String(con), safeScore)}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 💡 Đánh giá / Khuyến nghị */}
                <div className="border-t border-slate-800/80 pt-3 flex items-start gap-2 bg-amber-950/30 p-2.5 rounded border border-amber-900/30">
                  <span className="font-bold text-amber-300 shrink-0">{isMaint ? '🛠️ Inspection Triage Recommendation:' : '💡 Đánh giá:'}</span>
                  <p className="text-slate-200 font-medium leading-relaxed">{normalizeScoreText(String(evaluationText), safeScore)}</p>
                </div>
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
};

const MiniMetric = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-2">
    <span className="block text-[10px] font-bold uppercase text-slate-500">{label}</span>
    <span className="mt-1 block truncate font-mono text-base font-black text-slate-100">{value}</span>
  </div>
);
