import React, { useMemo } from 'react';
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Clock,
  FileText,
  ShieldAlert,
  Target,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { TripData } from '../types';
import {
  DriverRankingRow,
  buildLocalAnalysis,
  buildRankingRows,
} from './DriverRankingView';

interface DriverRankingAnalysisPageProps {
  vehicles: TripData[];
  tripId: string | null;
}

const cardBase = 'rounded-lg border border-[#1E293B] bg-[#111827] shadow-lg shadow-black/20';

const statusClass = (severity: string) => {
  if (severity === 'critical') return 'bg-red-500/10 text-red-300 border-red-500/40';
  if (severity === 'high') return 'bg-orange-500/10 text-orange-300 border-orange-500/40';
  if (severity === 'medium') return 'bg-amber-500/10 text-amber-300 border-amber-500/40';
  return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/40';
};

const metricColor = (value: number) => {
  if (value >= 80) return '#22C55E';
  if (value >= 65) return '#EAB308';
  if (value >= 45) return '#F97316';
  return '#EF4444';
};

const penaltyColor = (value: number) => {
  if (value >= 20) return '#EF4444';
  if (value >= 8) return '#F97316';
  if (value >= 3) return '#EAB308';
  return '#38BDF8';
};

const buildAuditTrail = (row: DriverRankingRow) => {
  const frames = row.trip.frames ?? [];
  const totalFrames = Math.max(frames.length, 1);
  const firstBy = (predicate: (frame: typeof frames[number]) => boolean) => frames.find(predicate);
  const countBy = (predicate: (frame: typeof frames[number]) => boolean) => frames.filter(predicate).length;
  const frameEvidence = (frame: typeof frames[number] | undefined) => {
    if (!frame) return 'Không có frame đại diện trong dữ liệu hiện tại.';
    const ttc = Number.isFinite(frame.min_ttc) ? `${frame.min_ttc.toFixed(2)}s` : 'Infinity';
    const headway = Number.isFinite(frame.headway_sec) ? `${frame.headway_sec.toFixed(2)}s` : 'Infinity';
    return `frame_id=${frame.frame_id}, timestamp=${Number(frame.timestamp ?? 0).toFixed(1)}s, driver.state=${frame.driver?.state}, alertness_score=${Number(frame.driver?.alertness_score ?? 0).toFixed(2)}, min_ttc=${ttc}, headway_sec=${headway}, risk.final_risk_score=${Number(frame.risk?.final_risk_score ?? 0).toFixed(1)}`;
  };

  const distractedFrame = firstBy((frame) => frame.driver?.state === 'distracted');
  const fatigueFrame = firstBy((frame) => ['drowsy', 'yawning', 'microsleep'].includes(frame.driver?.state ?? ''));
  const ttcFrame = firstBy((frame) => Number.isFinite(frame.min_ttc) && frame.min_ttc <= 2.5);
  const highRiskFrame = firstBy((frame) => Number(frame.risk?.final_risk_score ?? 0) >= 80 || (Number.isFinite(frame.min_ttc) && (frame.min_ttc as number) > 0 && (frame.min_ttc as number) <= 2.5));
  const speedingFrame = firstBy((frame) => Boolean(frame.behavior_flags?.speeding));
  const tailgatingFrame = firstBy((frame) => Boolean(frame.behavior_flags?.tailgating));
  const harshFrame = firstBy((frame) => Boolean(frame.behavior_flags?.harsh_brake || frame.behavior_flags?.harsh_accel || frame.behavior_flags?.harsh_corner));

  // Deterministic audit milestones derived from local AI frame history.
  return [
    {
      id: `${row.trip_id}-baseline`,
      timestamp: '0.0s',
      event: 'Baseline scoring started',
      evidence: `Score bắt đầu từ 100. Trip có ${totalFrames} frames. AI contract giữ nguyên field risk.final_risk_score, driver.state, min_ttc, headway_sec, behavior_flags.`,
      severity: 'low',
    },
    distractedFrame && {
      id: `${row.trip_id}-distracted`,
      timestamp: `${Number(distractedFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `Attention penalty: -${(row.distractedPct * 0.10).toFixed(1)} pts`,
      evidence: `${countBy((frame) => frame.driver?.state === 'distracted')}/${totalFrames} frames distracted (${row.distractedPct.toFixed(1)}%). ${frameEvidence(distractedFrame)}. Mốc này làm giảm điểm vì driver.state=distracted trong trip làm tăng rủi ro phản ứng trước tình huống phía trước.`,
      severity: row.distractedPct >= 25 ? 'high' : 'medium',
    },
    fatigueFrame && {
      id: `${row.trip_id}-fatigue`,
      timestamp: `${Number(fatigueFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `Fatigue penalty: -${(((row.fatigueEvents / totalFrames) * 100) * 0.05).toFixed(1)} pts`,
      evidence: `${row.fatigueEvents} fatigue/microsleep events. ${frameEvidence(fatigueFrame)}. Mốc này làm giảm điểm vì drowsy/yawning/microsleep là trạng thái rủi ro trong trip và cần review vận hành.`,
      severity: fatigueFrame.driver?.state === 'microsleep' ? 'critical' : 'high',
    },
    highRiskFrame && {
      id: `${row.trip_id}-risk`,
      timestamp: `${Number(highRiskFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `Risk score penalty: -${((row.avgRisk * 0.45) + (row.maxRisk * 0.20)).toFixed(1)} pts`,
      evidence: `${frameEvidence(highRiskFrame)}. Mốc này làm giảm điểm vì risk.final_risk_score tăng, cho thấy AI đã tổng hợp driver factor và traffic factor thành nguy cơ vận hành cao.`,
      severity: Number(highRiskFrame.risk?.final_risk_score ?? 0) >= 80 ? 'critical' : 'high',
    },
    ttcFrame && {
      id: `${row.trip_id}-ttc`,
      timestamp: `${Number(ttcFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `TTC/Near-miss penalty: -${(((row.nearMissCount / totalFrames) * 100) * 0.05).toFixed(1)} pts`,
      evidence: `${row.nearMissCount} near misses. ${frameEvidence(ttcFrame)}. Mốc này làm giảm điểm vì min_ttc thấp nghĩa là thời gian còn lại trước nguy cơ va chạm phía trước bị thu hẹp.`,
      severity: 'critical',
    },
    tailgatingFrame && {
      id: `${row.trip_id}-tailgating`,
      timestamp: `${Number(tailgatingFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `Tailgating penalty: -${(row.tailgatingPct * 0.04).toFixed(1)} pts`,
      evidence: `${row.tailgatingPct.toFixed(1)}% frames tailgating. ${frameEvidence(tailgatingFrame)}. Mốc này làm giảm điểm vì khoảng cách bám đuôi thấp làm tăng nguy cơ phanh gấp và va chạm.`,
      severity: row.tailgatingPct >= 20 ? 'high' : 'medium',
    },
    speedingFrame && {
      id: `${row.trip_id}-speeding`,
      timestamp: `${Number(speedingFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `Speeding penalty: -${(row.speedingPct * 0.03).toFixed(1)} pts`,
      evidence: `${row.speedingPct.toFixed(1)}% frames speeding. ${frameEvidence(speedingFrame)}. Mốc này làm giảm điểm vì vượt tốc làm tăng quãng đường phanh và rủi ro bảo hiểm.`,
      severity: 'medium',
    },
    harshFrame && {
      id: `${row.trip_id}-harsh`,
      timestamp: `${Number(harshFrame.timestamp ?? 0).toFixed(1)}s`,
      event: `Harsh behavior penalty: -${(((row.harshEvents / totalFrames) * 100) * 0.03).toFixed(1)} pts`,
      evidence: `${row.harshEvents} harsh behavior events. ${frameEvidence(harshFrame)}. Mốc này làm giảm điểm vì hành vi lái gắt ảnh hưởng an toàn và kiểm soát trip.`,
      severity: row.harshEvents >= 3 ? 'high' : 'medium',
    },
    {
      id: `${row.trip_id}-final`,
      timestamp: 'END',
      event: `Final score: ${row.score.toFixed(1)}/100`,
      evidence: `Kết luận audit: trip xếp relative rank #${row.rank}, absolute safety=${row.riskLevel}, coachingPriority=${row.coachingPriority}. Các penalty chính: ${[
        row.avgRisk > 0 || row.maxRisk > 0 ? 'risk score' : null,
        row.criticalEvents > 0 ? 'critical frames' : null,
        row.distractedPct > 0 ? 'driver attention' : null,
        row.fatigueEvents > 0 ? 'fatigue' : null,
        row.nearMissCount > 0 || row.tailgatingPct > 0 ? 'TTC/following distance' : null,
        row.harshEvents > 0 || row.speedingPct > 0 ? 'behavior flags' : null,
      ].filter(Boolean).join(', ')}.`,
      severity: row.riskLevel === 'CRITICAL' ? 'critical' : row.riskLevel === 'AT_RISK' ? 'high' : row.riskLevel === 'WATCH' ? 'medium' : 'low',
    },
  ].filter(Boolean);
};

export const DriverRankingAnalysisPage: React.FC<DriverRankingAnalysisPageProps> = ({ vehicles, tripId }) => {
  const rows = useMemo(() => buildRankingRows(vehicles), [vehicles]);
  const row = rows.find((item) => item.trip_id === tripId) ?? rows[0];
  const fleetAverage = rows.length
    ? rows.reduce((sum, item) => sum + item.score, 0) / rows.length
    : 0;
  const analysis = row ? buildLocalAnalysis(row, fleetAverage) : null;
  const history = row ? buildAuditTrail(row) : [];
  const previousRow = row ? rows[row.rank - 2] : undefined;
  const nextRow = row ? rows[row.rank] : undefined;
  const totalFrames = Math.max(row?.trip.frames?.length ?? 0, 1);
  const harshEventPct = row ? (row.harshEvents / totalFrames) * 100 : 0;
  const fatigueEventPct = row ? (row.fatigueEvents / totalFrames) * 100 : 0;
  const nearMissPct = row ? (row.nearMissCount / totalFrames) * 100 : 0;
  const estimatedPenalties = row ? [
    { label: 'Average risk', value: row.avgRisk * 0.45, detail: `${row.avgRisk.toFixed(1)} × 0.45` },
    { label: 'Max risk', value: row.maxRisk * 0.20, detail: `${row.maxRisk.toFixed(1)} × 0.20` },
    { label: 'Critical frames', value: row.criticalEventPct * 0.15, detail: `${row.criticalEventPct.toFixed(1)}% × 0.15` },
    { label: 'Distracted', value: row.distractedPct * 0.10, detail: `${row.distractedPct.toFixed(1)}% × 0.10` },
    { label: 'Fatigue', value: fatigueEventPct * 0.05, detail: `${fatigueEventPct.toFixed(1)}% × 0.05` },
    { label: 'Speeding', value: row.speedingPct * 0.03, detail: `${row.speedingPct.toFixed(1)}% × 0.03` },
    { label: 'Tailgating', value: row.tailgatingPct * 0.04, detail: `${row.tailgatingPct.toFixed(1)}% × 0.04` },
    { label: 'Harsh behavior', value: harshEventPct * 0.03, detail: `${harshEventPct.toFixed(1)}% × 0.03` },
    { label: 'Near misses', value: nearMissPct * 0.05, detail: `${nearMissPct.toFixed(1)}% × 0.05` },
  ].filter((item) => item.value > 0.01) : [];
  const estimatedTotalPenalty = estimatedPenalties.reduce((sum, item) => sum + item.value, 0);
  const rawRankingScore = Math.max(0, 100 - estimatedTotalPenalty);
  const pieData = row ? [
    { name: 'Ranking Score', value: row.score, color: metricColor(row.score) },
    { name: 'Risk Gap', value: 100 - row.score, color: '#334155' },
  ] : [];
  const penaltyBreakdown = estimatedPenalties.map((item) => ({
    category: item.label,
    penalty: item.value,
  }));

  if (!row || !analysis) {
    return (
      <div className="min-h-screen bg-[#070A12] p-8 text-slate-300">
        Trip ranking analysis is not available.
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-y-auto bg-[#070A12] px-5 py-8 text-slate-100">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[#1E293B] pb-6">
          <div>
            <span className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-500">AI Trip Ranking Report</span>
            <h1 className="mt-2 text-3xl font-black tracking-tight">{row.trip_id}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
              Phân tích relative ranking và absolute safety dựa trên AI contract gốc: trip_id, metadata, frames, ego, driver, min_ttc, headway_sec, behavior_flags và risk.
            </p>
          </div>
          <div className={`rounded-lg border px-4 py-3 text-right ${statusClass(analysis.top_risk_factors[0]?.severity ?? 'low')}`}>
            <span className="block text-[10px] font-black uppercase tracking-widest">Coaching Priority</span>
            <span className="mt-1 block text-2xl font-black">{row.coachingPriority}</span>
          </div>
        </header>

        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat icon={Target} label="Fleet Rank" value={`#${row.rank}`} />
          <Stat icon={Brain} label="Ranking Score" value={row.score.toFixed(1)} />
          <Stat icon={AlertTriangle} label="High-Risk Frames" value={String(row.criticalEvents)} />
          <Stat icon={CheckCircle2} label="Fleet Avg Ranking Score" value={fleetAverage.toFixed(1)} />
        </section>

        <section className="grid gap-5 lg:grid-cols-[320px_1fr]">
          <div className={`${cardBase} p-5`}>
            <h2 className="mb-4 text-xs font-black uppercase tracking-widest text-slate-400">Overall Ranking Score</h2>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" innerRadius={62} outerRadius={88} startAngle={90} endAngle={450}>
                    {pieData.map((item) => <Cell key={item.name} fill={item.color} />)}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#F8FAFC' }}
                    itemStyle={{ color: '#F8FAFC' }}
                    labelStyle={{ color: '#F8FAFC', fontWeight: 800 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="-mt-36 grid h-24 place-items-center text-center">
              <span className="font-mono text-4xl font-black" style={{ color: metricColor(row.score) }}>{row.score.toFixed(1)}</span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Ranking Score</span>
            </div>
          </div>

          <div className={`${cardBase} p-5`}>
            <h2 className="mb-4 text-xs font-black uppercase tracking-widest text-slate-400">Ranking Penalty Breakdown</h2>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={penaltyBreakdown} layout="vertical" margin={{ left: 18, right: 34 }}>
                  <CartesianGrid stroke="#1E293B" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#94A3B8', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="category" tick={{ fill: '#CBD5E1', fontSize: 11 }} axisLine={false} tickLine={false} width={112} />
                  <Tooltip
                    contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#F8FAFC' }}
                    itemStyle={{ color: '#F8FAFC' }}
                    labelStyle={{ color: '#F8FAFC', fontWeight: 800 }}
                    cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }}
                  />
                  <Bar dataKey="penalty" name="Penalty" radius={[0, 6, 6, 0]}>
                    <LabelList dataKey="penalty" position="right" formatter={(value: number) => `-${value.toFixed(1)}`} fill="#F8FAFC" fontSize={12} fontWeight={800} />
                    {penaltyBreakdown.map((item) => <Cell key={item.category} fill={penaltyColor(item.penalty)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section className={`${cardBase} overflow-hidden`}>
          <div className="border-b border-[#1E293B] px-5 py-4">
            <h2 className="text-xs font-black uppercase tracking-widest text-slate-400">Ranking Method And Rank Reason</h2>
          </div>
          <div className="grid gap-0 text-sm lg:grid-cols-[1.05fr_0.95fr]">
            <div className="border-b border-[#1E293B] p-5 lg:border-b-0 lg:border-r">
              <p className="text-slate-300">
                Fleet ranking được sắp xếp giảm dần theo <b className="text-slate-100">Ranking Score riêng của bảng Ranking</b>.
                Điểm này tính từ JSON/local AI risk và behavior fields, không dùng BTC safe score cũ.
              </p>
              <div className="mt-4 grid gap-2">
                <InfoLine label="Base score" value="100.0" />
                <InfoLine label="Estimated penalty" value={`-${estimatedTotalPenalty.toFixed(1)}`} />
                <InfoLine label="Raw ranking score" value={rawRankingScore.toFixed(1)} />
                <InfoLine label="Final ranking score" value={row.score.toFixed(1)} />
                <InfoLine label="Final rank" value={`#${row.rank} / ${rows.length}`} />
              </div>
            </div>
            <div className="p-5">
              <p className="text-slate-300">
                {previousRow
                  ? `${row.trip_id} đứng sau ${previousRow.trip_id} vì Ranking Score thấp hơn ${Math.abs(previousRow.score - row.score).toFixed(1)} điểm.`
                  : `${row.trip_id} đang đứng đầu fleet vì có Ranking Score cao nhất trong danh sách hiện tại.`}
                {' '}
                {nextRow
                  ? `Trip ngay phía sau là ${nextRow.trip_id}, thấp hơn ${Math.abs(row.score - nextRow.score).toFixed(1)} điểm.`
                  : 'Đây là trip cuối bảng theo Ranking Score hiện tại.'}
              </p>
              <div className="mt-4 space-y-2">
                {estimatedPenalties.length === 0 ? (
                  <div className="rounded border border-[#1E293B] bg-slate-950/50 px-3 py-2 text-slate-400">Không có penalty đáng kể trong dữ liệu hiện tại.</div>
                ) : estimatedPenalties.map((item) => (
                  <div key={item.label} className="grid grid-cols-[1fr_90px_120px] gap-2 rounded border border-[#1E293B] bg-slate-950/50 px-3 py-2 text-xs">
                    <span className="font-bold text-slate-200">{item.label}</span>
                    <span className="font-mono font-black text-red-300">-{item.value.toFixed(1)}</span>
                    <span className="font-mono text-slate-500">{item.detail}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className={`${cardBase} overflow-hidden`}>
          <div className="border-b border-[#1E293B] px-5 py-4">
            <h2 className="text-xs font-black uppercase tracking-widest text-slate-400">Score Explanation</h2>
          </div>
          <div className="grid grid-cols-[180px_120px_1fr] gap-0 text-sm">
            {analysis.top_risk_factors.map((factor) => (
              <React.Fragment key={factor.factor}>
                <div className="border-b border-[#1E293B] px-5 py-4 font-bold text-slate-200">{factor.factor}</div>
                <div className="border-b border-[#1E293B] px-5 py-4">
                  <span className={`rounded border px-2 py-1 text-[10px] font-black uppercase ${statusClass(factor.severity)}`}>{factor.severity}</span>
                </div>
                <div className="border-b border-[#1E293B] px-5 py-4 text-slate-400">
                  <span className="block text-slate-200">{factor.evidence}</span>
                  {factor.business_impact}
                </div>
              </React.Fragment>
            ))}
          </div>
        </section>

        <section className={`${cardBase} overflow-hidden`}>
          <div className="flex items-center justify-between border-b border-[#1E293B] px-5 py-4">
            <h2 className="text-xs font-black uppercase tracking-widest text-slate-400">Score Audit Trail And Event Log</h2>
            <span className="text-[10px] font-bold uppercase text-slate-500">// derived from local AI frame history</span>
          </div>
          <div className="grid grid-cols-[90px_220px_1fr_110px] text-sm">
            {history.length === 0 ? (
              <div className="col-span-4 px-5 py-6 text-slate-500">No notable historical events detected in current frames.</div>
            ) : history.map((event) => (
              <React.Fragment key={event.id}>
                <div className="border-b border-[#1E293B] px-5 py-3 font-mono text-slate-400">{event.timestamp}</div>
                <div className="border-b border-[#1E293B] px-5 py-3 font-bold text-slate-200">{event.event}</div>
                <div className="border-b border-[#1E293B] px-5 py-3 text-slate-400">{event.evidence}</div>
                <div className="border-b border-[#1E293B] px-5 py-3">
                  <span className={`rounded border px-2 py-1 text-[10px] font-black uppercase ${statusClass(event.severity)}`}>{event.severity}</span>
                </div>
              </React.Fragment>
            ))}
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <ReportPanel icon={FileText} title="AI Audit Reasoning">
            {analysis.summary}
            {'\n\n'}
            {analysis.ranking_reason}
            {'\n\n'}
            {analysis.fleet_comparison.score_vs_average}
            {'\n'}
            {analysis.fleet_comparison.risk_vs_average}
            {'\n'}
            {analysis.fleet_comparison.behavior_vs_average}
          </ReportPanel>

          <ReportPanel icon={ShieldAlert} title="Action And Coaching Plan">
            {analysis.recommended_actions.map((item) => `${item.priority.toUpperCase()}: ${item.action} Lý do: ${item.reason}`).join('\n\n')}
            {'\n\n'}
            Coaching focus: {analysis.coaching_plan.focus}
            {'\n'}
            Next review: {analysis.coaching_plan.next_review}
            {'\n'}
            Success metric: {analysis.coaching_plan.success_metric}
          </ReportPanel>
        </section>
      </div>
    </div>
  );
};

const Stat = ({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) => (
  <div className={`${cardBase} p-5`}>
    <Icon className="mb-3 h-5 w-5 text-sky-400" />
    <span className="block text-[10px] font-black uppercase tracking-widest text-slate-500">{label}</span>
    <span className="mt-1 block font-mono text-3xl font-black text-slate-100">{value}</span>
  </div>
);

const InfoLine = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between rounded border border-[#1E293B] bg-slate-950/50 px-3 py-2">
    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">{label}</span>
    <span className="font-mono text-sm font-black text-slate-100">{value}</span>
  </div>
);

const ReportPanel = ({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) => (
  <div className={`${cardBase} p-5`}>
    <div className="mb-3 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400">
      <Icon className="h-4 w-4 text-sky-400" />
      {title}
    </div>
    <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">{children}</div>
  </div>
);
