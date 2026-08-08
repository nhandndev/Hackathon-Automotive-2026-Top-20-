import React, { useMemo, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  Brain,
  Gauge,
  Loader2,
  Sparkles,
  Target,
  Trophy,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { DecisionAlert, Frame, TripData } from '../types';

interface DriverRankingViewProps {
  vehicles: TripData[];
  selectedVehicle: TripData | null;
  liveAlerts?: DecisionAlert[];
  onSelectVehicle: (vehicle: TripData) => void;
  onViewTripDetail: (vehicle: TripData) => void;
  onOpenCopilot: () => void;
}

type RiskLevel = 'SAFE' | 'WATCH' | 'AT_RISK' | 'CRITICAL';
type ActionPriority = 'monitoring' | 'short_term' | 'immediate';

export interface DriverRankingRow {
  trip: TripData;
  rank: number;
  trip_id: string;
  score: number;
  riskLevel: RiskLevel;
  avgRisk: number;
  maxRisk: number;
  criticalEvents: number;
  criticalEventPct: number;
  distractedPct: number;
  fatigueEvents: number;
  speedingPct: number;
  tailgatingPct: number;
  harshEvents: number;
  nearMissCount: number;
  coachingPriority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  chartData: { label: string; value: number; color: string }[];
}

export interface RankingAnalysis {
  summary: string;
  ranking_reason: string;
  top_risk_factors: {
    factor: string;
    evidence: string;
    business_impact: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }[];
  fleet_comparison: {
    score_vs_average: string;
    risk_vs_average: string;
    behavior_vs_average: string;
  };
  recommended_actions: {
    priority: ActionPriority;
    action: string;
    reason: string;
  }[];
  coaching_plan: {
    focus: string;
    next_review: string;
    success_metric: string;
  };
}

export const AI_RANKING_EXPLAIN_PROMPT = `
You are Fleet AI Copilot for a driver safety monitoring dashboard.

Analyze the selected driver's ranking using only the provided AI contract fields:
trip_id, metadata, frames, ego, driver, min_ttc, headway_sec, behavior_flags, and risk.

Your job:
1. Explain why this driver received the current safety ranking.
2. Identify the top risk contributors.
3. Compare this driver against the fleet average.
4. Provide clear business reasoning for fleet managers.
5. Recommend concrete actions: immediate intervention, coaching, monitoring, or no action.
6. Keep the output concise, professional, and evidence-based.
7. Do not invent missing data. If a metric is unavailable, mark it as unavailable.

Return a business-readable Vietnamese analysis with these sections:
- Executive summary
- Score audit trail: explain exactly which time ranges, frame_id values, and AI fields caused score deduction.
- Ranking reasoning: say "at this milestone/frame/time, this happened, therefore score decreased by X estimated points" for every important risk contributor.
- Top risk factors with evidence from frame_id, timestamp, driver.state, driver.alertness_score, min_ttc, headway_sec, behavior_flags, risk.final_risk_score.
- Fleet comparison
- Recommended action plan
- Coaching plan

Rules:
- Be explicit. Do not only summarize "Risk score is high"; show the audit reason.
- Mention the exact AI fields used.
- If a value is Infinity, write "Infinity means no immediate TTC/headway threat at that frame".
- Distinguish driver-state risk from traffic-proximity risk.
- Use Vietnamese, professional fleet-safety language.
- Do not expose chain-of-thought. Provide concise evidence-based reasoning and audit conclusions.
`;

const clamp = (value: number, min = 0, max = 100) => Math.min(Math.max(value, min), max);

const finite = (value: unknown, fallback = 0) =>
  typeof value === 'number' && Number.isFinite(value) ? value : fallback;

const pct = (count: number, total: number) => (total > 0 ? (count / total) * 100 : 0);

const scoreLabel = (score: number): RiskLevel => {
  if (score < 45) return 'CRITICAL';
  if (score < 65) return 'AT_RISK';
  if (score < 82) return 'WATCH';
  return 'SAFE';
};

const priorityFor = (riskLevel: RiskLevel): DriverRankingRow['coachingPriority'] => {
  if (riskLevel === 'CRITICAL') return 'CRITICAL';
  if (riskLevel === 'AT_RISK') return 'HIGH';
  if (riskLevel === 'WATCH') return 'MEDIUM';
  return 'LOW';
};

const riskClass = (level: RiskLevel) => {
  if (level === 'CRITICAL') return 'border-red-500/60 bg-red-950/30 text-red-200';
  if (level === 'AT_RISK') return 'border-orange-500/60 bg-orange-950/30 text-orange-200';
  if (level === 'WATCH') return 'border-amber-500/60 bg-amber-950/30 text-amber-200';
  return 'border-emerald-500/60 bg-emerald-950/30 text-emerald-200';
};

const scoreColor = (score: number) => {
  if (score < 45) return 'text-red-300';
  if (score < 65) return 'text-orange-300';
  if (score < 82) return 'text-amber-300';
  return 'text-emerald-300';
};

const isFatigueState = (state?: string) => (
  state === 'drowsy'
  || state === 'yawning'
  || state === 'microsleep'
);

const isDistractedState = (state?: string) => state === 'distracted';

const lowTtc = (frame: Frame) => {
  const value = finite(frame.min_ttc, Number.POSITIVE_INFINITY);
  return value > 0 && value <= 2.5;
};

const countBehavior = (frames: Frame[], key: 'harsh_brake' | 'harsh_accel' | 'harsh_corner' | 'speeding' | 'tailgating') =>
  frames.filter((frame) => Boolean(frame.behavior_flags?.[key])).length;

export const buildRankingRows = (vehicles: TripData[]): DriverRankingRow[] => (
  vehicles.map((trip) => {
    const frames = trip.frames ?? [];
    const total = frames.length;
    const aggregate = trip.trip_aggregate;
    const driverSummary = trip.driver_summary;

    const avgRisk = total > 0
      ? frames.reduce((sum, frame) => sum + finite(frame.risk?.final_risk_score), 0) / total
      : finite(aggregate?.avg_risk_score);
    const maxRisk = total > 0
      ? frames.reduce((max, frame) => Math.max(max, finite(frame.risk?.final_risk_score)), 0)
      : finite(aggregate?.max_risk_score);
    const distractedPct = total > 0
      ? pct(frames.filter((frame) => isDistractedState(frame.driver?.state)).length, total)
      : finite(driverSummary?.state_distribution_pct?.distracted);
    const speedingPct = total > 0
      ? pct(countBehavior(frames, 'speeding'), total)
      : finite(aggregate?.speeding_pct_time);
    const tailgatingPct = total > 0
      ? pct(countBehavior(frames, 'tailgating'), total)
      : finite(aggregate?.tailgating_pct_time);
    const harshEvents = total > 0
      ? countBehavior(frames, 'harsh_brake') + countBehavior(frames, 'harsh_accel') + countBehavior(frames, 'harsh_corner')
      : finite(aggregate?.harsh_brake_count) + finite(aggregate?.harsh_accel_count) + finite(aggregate?.harsh_corner_count);
    const fatigueEvents = total > 0
      ? frames.filter((frame) => isFatigueState(frame.driver?.state)).length
      : finite(driverSummary?.microsleep_count);
    const nearMissCount = total > 0
      ? frames.filter(lowTtc).length
      : finite(aggregate?.near_miss_count);
    const criticalEvents = frames.filter((frame) => finite(frame.risk?.final_risk_score) >= 80 || lowTtc(frame)).length;
    const criticalEventPct = pct(criticalEvents, total);
    const harshEventPct = pct(harshEvents, total);
    const fatigueEventPct = pct(fatigueEvents, total);
    const nearMissPct = pct(nearMissCount, total);

    const penalty = (avgRisk * 0.45)
      + (maxRisk * 0.20)
      + (criticalEventPct * 0.15)
      + (distractedPct * 0.10)
      + (fatigueEventPct * 0.05)
      + (speedingPct * 0.03)
      + (tailgatingPct * 0.04)
      + (harshEventPct * 0.03)
      + (nearMissPct * 0.05);

    let calculatedScore = clamp(100 - penalty);
    if (distractedPct > 50) calculatedScore = Math.min(calculatedScore, 58);

    const score = clamp(calculatedScore);
    const riskLevel = scoreLabel(score);

    return {
      trip,
      rank: 0,
      trip_id: trip.trip_id,
      score,
      riskLevel,
      avgRisk,
      maxRisk,
      criticalEvents,
      criticalEventPct,
      distractedPct,
      fatigueEvents,
      speedingPct,
      tailgatingPct,
      harshEvents,
      nearMissCount,
      coachingPriority: priorityFor(riskLevel),
      chartData: [
        { label: 'Risk', value: clamp(avgRisk), color: '#38BDF8' },
        { label: 'Speeding', value: clamp(speedingPct), color: '#F59E0B' },
        { label: 'Tailgating', value: clamp(tailgatingPct), color: '#FB923C' },
        { label: 'Distraction', value: clamp(distractedPct), color: '#A78BFA' },
        { label: 'Fatigue', value: clamp(fatigueEvents * 10), color: '#F43F5E' },
        { label: 'Harsh', value: clamp(harshEvents * 10), color: '#EF4444' },
      ],
    };
  })
    .sort((a, b) => (b.score - a.score) || (a.avgRisk - b.avgRisk) || (a.maxRisk - b.maxRisk) || (a.criticalEventPct - b.criticalEventPct))
    .map((row, index) => ({ ...row, rank: index + 1 }))
);

export const buildLocalAnalysis = (row: DriverRankingRow, fleetAverage: number): RankingAnalysis => {
  const frames = row.trip.frames ?? [];
  const totalFrames = Math.max(frames.length, 1);
  const distractedFrames = frames.filter((frame) => frame.driver?.state === 'distracted');
  const fatigueFrames = frames.filter((frame) => isFatigueState(frame.driver?.state));
  const ttcFrames = frames.filter(lowTtc);
  const highRiskFrames = frames.filter((frame) => finite(frame.risk?.final_risk_score) >= 60);
  const firstDistracted = distractedFrames[0];
  const firstFatigue = fatigueFrames[0];
  const firstTtc = ttcFrames[0];
  const firstHighRisk = highRiskFrames[0];
  const harshEventPct = pct(row.harshEvents, totalFrames);
  const fatigueEventPct = pct(row.fatigueEvents, totalFrames);
  const nearMissPct = pct(row.nearMissCount, totalFrames);
  const estimatedPenalties = {
    avgRisk: row.avgRisk * 0.45,
    maxRisk: row.maxRisk * 0.20,
    criticalEvents: row.criticalEventPct * 0.15,
    distracted: row.distractedPct * 0.10,
    fatigue: fatigueEventPct * 0.05,
    speeding: row.speedingPct * 0.03,
    tailgating: row.tailgatingPct * 0.04,
    harsh: harshEventPct * 0.03,
    nearMiss: nearMissPct * 0.05,
  };
  const totalPenalty = Object.values(estimatedPenalties).reduce((sum, value) => sum + value, 0);
  const frameText = (frame: typeof frames[number] | undefined) => {
    if (!frame) return 'không có frame đại diện';
    const ttc = Number.isFinite(frame.min_ttc) ? `${frame.min_ttc.toFixed(2)}s` : 'Infinity';
    const headway = Number.isFinite(frame.headway_sec) ? `${frame.headway_sec.toFixed(2)}s` : 'Infinity';
    return `frame_id=${frame.frame_id}, timestamp=${Number(frame.timestamp ?? 0).toFixed(1)}s, driver.state=${frame.driver?.state}, alertness_score=${Number(frame.driver?.alertness_score ?? 0).toFixed(2)}, min_ttc=${ttc}, headway_sec=${headway}, risk.final_risk_score=${Number(frame.risk?.final_risk_score ?? 0).toFixed(1)}`;
  };
  const factors = [
    {
      factor: 'Risk score',
      value: row.maxRisk,
      evidence: `Max risk ${row.maxRisk.toFixed(1)}, average risk ${row.avgRisk.toFixed(1)}`,
      business_impact: 'Rủi ro cao làm tăng khả năng cần can thiệp vận hành trong chuyến.',
      severity: row.maxRisk >= 80 ? 'critical' : row.maxRisk >= 60 ? 'high' : row.maxRisk >= 35 ? 'medium' : 'low',
    },
    {
      factor: 'Driver attention',
      value: row.distractedPct,
      evidence: `Distracted ${row.distractedPct.toFixed(1)}% thời lượng ghi nhận`,
      business_impact: 'Mất tập trung làm giảm khả năng phản ứng với tình huống TTC thấp.',
      severity: row.distractedPct >= 25 ? 'high' : row.distractedPct >= 10 ? 'medium' : 'low',
    },
    {
      factor: 'Fatigue',
      value: row.fatigueEvents,
      evidence: `${row.fatigueEvents} fatigue/microsleep events`,
      business_impact: 'Buồn ngủ hoặc microsleep là nhóm rủi ro cần coaching và nghỉ bắt buộc.',
      severity: row.fatigueEvents >= 3 ? 'critical' : row.fatigueEvents >= 1 ? 'high' : 'low',
    },
    {
      factor: 'Following distance',
      value: row.nearMissCount + row.tailgatingPct,
      evidence: `${row.nearMissCount} near misses, tailgating ${row.tailgatingPct.toFixed(1)}%`,
      business_impact: 'Khoảng cách an toàn thấp làm tăng xác suất va chạm phía trước.',
      severity: row.nearMissCount >= 3 || row.tailgatingPct >= 20 ? 'high' : row.nearMissCount > 0 ? 'medium' : 'low',
    },
  ]
    .sort((a, b) => b.value - a.value)
    .slice(0, 3);

  const delta = row.score - fleetAverage;
  const priority: ActionPriority = row.riskLevel === 'CRITICAL'
    ? 'immediate'
    : row.riskLevel === 'AT_RISK'
      ? 'short_term'
      : 'monitoring';

  return {
    summary: `${row.trip_id} đạt Ranking Score ${row.score.toFixed(1)}/100, xếp hạng #${row.rank}. Mức ưu tiên coaching: ${row.coachingPriority}.`,
    ranking_reason: [
      `Ranking formula bắt đầu từ 100 điểm và trừ ${totalPenalty.toFixed(1)} điểm đã normalize theo tỷ lệ frame/phần trăm. Ranking Score cuối là ${row.score.toFixed(1)}/100.`,
      `1. Risk score penalty: -${(estimatedPenalties.avgRisk + estimatedPenalties.maxRisk).toFixed(1)} điểm. Mốc đại diện: ${frameText(firstHighRisk)}. Lý do: risk.final_risk_score cao cho thấy tình huống đã được AI đánh giá nguy hiểm hơn baseline.`,
      `2. Driver attention penalty: -${estimatedPenalties.distracted.toFixed(1)} điểm. Có ${distractedFrames.length}/${totalFrames} frames distracted (${row.distractedPct.toFixed(1)}%). Mốc đầu tiên: ${frameText(firstDistracted)}. Lý do: driver.state=distracted làm giảm khả năng phản ứng, dù min_ttc có thể là Infinity ở các frame đầu.`,
      `3. Critical frame penalty: -${estimatedPenalties.criticalEvents.toFixed(1)} điểm. Critical frames=${row.criticalEvents}/${totalFrames} (${row.criticalEventPct.toFixed(1)}%). Mốc đại diện: ${frameText(firstHighRisk)}.`,
      `4. Fatigue/microsleep penalty: -${estimatedPenalties.fatigue.toFixed(1)} điểm. Fatigue events=${row.fatigueEvents}. Mốc đại diện: ${frameText(firstFatigue)}. Lý do: drowsy/yawning/microsleep là rủi ro trực tiếp với tài xế, cần coaching hoặc nghỉ bắt buộc.`,
      `5. TTC/following-distance penalty: -${(estimatedPenalties.nearMiss + estimatedPenalties.tailgating).toFixed(1)} điểm. Near miss=${row.nearMissCount}, tailgating=${row.tailgatingPct.toFixed(1)}%. Mốc đại diện: ${frameText(firstTtc)}. Lý do: min_ttc thấp hoặc tailgating làm tăng nguy cơ va chạm phía trước.`,
      `6. Behavior penalty: -${(estimatedPenalties.speeding + estimatedPenalties.harsh).toFixed(1)} điểm từ speeding=${row.speedingPct.toFixed(1)}% và harsh_events=${row.harshEvents}. Đây là nhóm hành vi vận hành ảnh hưởng chi phí bảo hiểm, hao mòn xe và coaching priority.`,
    ].join('\n\n'),
    top_risk_factors: factors.map((factor) => ({
      factor: factor.factor,
      evidence: factor.evidence,
      business_impact: factor.business_impact,
      severity: factor.severity as RankingAnalysis['top_risk_factors'][number]['severity'],
    })),
    fleet_comparison: {
      score_vs_average: `${delta >= 0 ? '+' : ''}${delta.toFixed(1)} điểm so với fleet average ranking score ${fleetAverage.toFixed(1)}`,
      risk_vs_average: `Average risk ${row.avgRisk.toFixed(1)}, max risk ${row.maxRisk.toFixed(1)}`,
      behavior_vs_average: `Distracted ${row.distractedPct.toFixed(1)}%, speeding ${row.speedingPct.toFixed(1)}%, tailgating ${row.tailgatingPct.toFixed(1)}%`,
    },
    recommended_actions: [
      {
        priority,
        action: priority === 'immediate' ? 'Can thiệp ngay và yêu cầu giảm tốc/nghỉ an toàn.' : priority === 'short_term' ? 'Lên lịch coaching trong ca gần nhất.' : 'Tiếp tục theo dõi trong các trip tiếp theo.',
        reason: `Risk level hiện tại là ${row.riskLevel}, coaching priority ${row.coachingPriority}.`,
      },
      {
        priority: 'monitoring',
        action: 'Theo dõi lại TTC, distracted state và final risk score trong trip kế tiếp.',
        reason: 'Đây là các chỉ báo liên quan trực tiếp tới ranking hiện tại.',
      },
    ],
    coaching_plan: {
      focus: row.fatigueEvents > 0 ? 'Fatigue management, nghỉ bắt buộc và nhận diện microsleep.' : row.distractedPct > 10 ? 'Giảm distracted driving và tăng tập trung phía trước.' : 'Duy trì hành vi lái ổn định.',
      next_review: 'Sau 1-2 trip hoặc sau ca chạy kế tiếp.',
      success_metric: 'Ranking Score tăng, Max Risk giảm, distracted/tailgating/near miss giảm.',
    },
  };
};

export const DriverRankingView: React.FC<DriverRankingViewProps> = ({
  vehicles,
  selectedVehicle,
  liveAlerts = [],
  onSelectVehicle,
  onViewTripDetail,
  onOpenCopilot,
}) => {
  const rows = useMemo(() => buildRankingRows(vehicles), [vehicles]);
  const [selectedTripId, setSelectedTripId] = useState(selectedVehicle?.trip_id ?? rows[0]?.trip_id ?? '');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const selectedRow = rows.find((row) => row.trip_id === selectedTripId) ?? rows[0];
  const fleetAverage = rows.length
    ? rows.reduce((sum, row) => sum + row.score, 0) / rows.length
    : 0;
  const criticalDrivers = rows.filter((row) => row.riskLevel === 'CRITICAL' || row.riskLevel === 'AT_RISK').length;
  const criticalAlerts = liveAlerts.filter((alert) => alert.severity === 'critical').length
    + rows.reduce((sum, row) => sum + row.criticalEvents, 0);

  if (!selectedRow) {
    return (
      <div className="flex-1 grid place-items-center bg-[#070A12] text-slate-400">
        No driver ranking data loaded.
      </div>
    );
  }

  const handleSelect = (row: DriverRankingRow) => {
    setSelectedTripId(row.trip_id);
    onSelectVehicle(row.trip);
  };

  const handleExplainRanking = async () => {
    setIsAnalyzing(true);
    window.setTimeout(() => {
      const params = new URLSearchParams({
        view: 'ranking-analysis',
        trip_id: selectedRow.trip_id,
      });
      window.open(`${window.location.origin}${window.location.pathname}?${params.toString()}`, '_blank', 'noopener,noreferrer');
      setIsAnalyzing(false);
    }, 900);
  };

  return (
    <div className="flex h-full overflow-hidden bg-[#070A12] text-white">
      <section className="flex-1 overflow-y-auto p-5 lg:p-6">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div>
            <span className="text-xs font-mono text-sky-400">DRIVER SCORECARD</span>
            <h1 className="mt-1 text-2xl font-extrabold">Driver Ranking</h1>
            <p className="mt-1 max-w-3xl text-sm text-slate-400">
              Ranking xếp theo Ranking Score riêng của bảng này. Điểm được tính từ JSON/local AI risk, critical frames, distracted, fatigue, TTC/headway và behavior flags; không dùng BTC safe score cũ.
            </p>
          </div>
          <button
            onClick={onOpenCopilot}
            className="flex items-center gap-2 rounded-lg border border-indigo-500 px-4 py-2 text-sm font-bold text-indigo-300 hover:bg-indigo-950"
          >
            <Sparkles className="h-4 w-4" />
            Fleet AI Copilot
          </button>
        </div>

        <div className="mb-5 grid grid-cols-2 gap-3 xl:grid-cols-4">
          <MetricCard icon={Trophy} label="Drivers ranked" value={String(rows.length)} tone="sky" />
          <MetricCard icon={Gauge} label="Fleet avg ranking score" value={fleetAverage.toFixed(1)} tone="emerald" />
          <MetricCard icon={Target} label="Need coaching" value={String(criticalDrivers)} tone="amber" />
          <MetricCard icon={AlertTriangle} label="High-risk frames/signals" value={String(criticalAlerts)} tone="red" />
        </div>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
          <div className="overflow-hidden rounded-xl border border-[#1E293B] bg-[#0B0F19]">
            <div className="grid grid-cols-[70px_1fr_110px_120px_120px_120px_140px] border-b border-[#1E293B] px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <span>Rank</span>
              <span>Driver</span>
              <span>Ranking Score</span>
              <span>Risk</span>
              <span>Avg Risk</span>
              <span>High-Risk Frames</span>
              <span>Coaching</span>
            </div>
            <div className="divide-y divide-[#1E293B]">
              {rows.map((row) => (
                <button
                  key={row.trip_id}
                  onClick={() => handleSelect(row)}
                  className={`grid w-full grid-cols-[70px_1fr_110px_120px_120px_120px_140px] items-center px-4 py-3 text-left transition-colors ${
                    row.trip_id === selectedRow.trip_id ? 'bg-slate-900/90' : 'hover:bg-slate-900/50'
                  }`}
                >
                  <span className="font-mono text-lg font-black text-slate-200">#{row.rank}</span>
                  <span>
                    <span className="block font-bold text-slate-100">{row.trip_id}</span>
                    <span className="text-[11px] text-slate-500">{row.trip.metadata?.description ?? 'No description'}</span>
                  </span>
                  <span className={`font-mono text-xl font-black ${scoreColor(row.score)}`}>{row.score.toFixed(1)}</span>
                  <span className={`w-fit rounded-full border px-2 py-1 text-[10px] font-bold ${riskClass(row.riskLevel)}`}>
                    {row.riskLevel}
                  </span>
                  <span className="font-mono text-sm font-bold text-sky-300">{row.avgRisk.toFixed(1)}</span>
                  <span className="text-sm text-slate-300">{row.criticalEvents}</span>
                  <span className="text-xs font-bold text-slate-300">{row.coachingPriority}</span>
                </button>
              ))}
            </div>
          </div>

          <aside className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="text-xs font-mono text-sky-400">SELECTED DRIVER</span>
                <h2 className="mt-1 text-xl font-extrabold">{selectedRow.trip_id}</h2>
              </div>
              <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskClass(selectedRow.riskLevel)}`}>
                {selectedRow.riskLevel}
              </span>
            </div>

            <div className="mt-5 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={selectedRow.chartData}>
                  <CartesianGrid stroke="#1E293B" vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: '#94A3B8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#94A3B8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#E2E8F0' }}
                    cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }}
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {selectedRow.chartData.map((item) => <Cell key={item.label} fill={item.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <Info label="Avg risk" value={selectedRow.avgRisk.toFixed(1)} />
              <Info label="Max risk" value={selectedRow.maxRisk.toFixed(1)} />
              <Info label="Distracted" value={`${selectedRow.distractedPct.toFixed(1)}%`} />
              <Info label="Tailgating" value={`${selectedRow.tailgatingPct.toFixed(1)}%`} />
              <Info label="Fatigue events" value={String(selectedRow.fatigueEvents)} />
              <Info label="Near misses" value={String(selectedRow.nearMissCount)} />
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <button
                onClick={handleExplainRanking}
                disabled={isAnalyzing}
                className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-bold hover:bg-sky-500 disabled:cursor-wait disabled:bg-sky-900"
              >
                {isAnalyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
                {isAnalyzing ? 'Loading analysis...' : 'Explain Ranking'}
              </button>
              <button
                onClick={() => onViewTripDetail(selectedRow.trip)}
                className="flex items-center gap-2 rounded-lg border border-slate-600 px-4 py-2 text-sm font-bold text-slate-200 hover:bg-slate-800"
              >
                Trip detail
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
};

const MetricCard = ({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  tone: 'sky' | 'emerald' | 'amber' | 'red';
}) => {
  const toneClass = {
    sky: 'text-sky-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    red: 'text-red-400',
  }[tone];

  return (
    <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-4">
      <Icon className={`mb-3 h-5 w-5 ${toneClass}`} />
      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">{label}</span>
      <div className="mt-1 font-mono text-2xl font-black text-slate-100">{value}</div>
    </div>
  );
};

const Info = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg border border-[#1E293B] bg-slate-950/40 p-3">
    <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</span>
    <span className="mt-1 block font-mono text-sm font-bold text-slate-100">{value}</span>
  </div>
);
