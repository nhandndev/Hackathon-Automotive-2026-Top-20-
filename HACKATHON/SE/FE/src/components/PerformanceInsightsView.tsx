import React from 'react';
import { AlertTriangle, Brain, Gauge, ListChecks, Sparkles, TrendingUp, Trophy } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { DecisionAlert, TripData } from '../types';
import { buildRankingRows } from './DriverRankingView';

interface PerformanceInsightsViewProps {
  vehicle: TripData;
  vehicles?: TripData[];
  liveAlerts?: DecisionAlert[];
  onOpenCopilot: () => void;
}

const finiteNumber = (value: unknown, fallback = 0) =>
  typeof value === 'number' && Number.isFinite(value) ? value : fallback;

const format = (value: unknown, digits = 1) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';

const severityClass = (severity: 'HIGH' | 'MEDIUM' | 'LOW') =>
  severity === 'HIGH' ? 'text-red-300' : severity === 'MEDIUM' ? 'text-amber-300' : 'text-slate-500';

export const PerformanceInsightsView: React.FC<PerformanceInsightsViewProps> = ({ vehicle, vehicles = [vehicle], liveAlerts = [], onOpenCopilot }) => {
  const fleetTrips = vehicles.length > 0 ? vehicles : [vehicle];
  const rows = buildRankingRows(fleetTrips);
  const allFrames = fleetTrips.flatMap((trip) => trip.frames ?? []);
  const totalFrames = Math.max(allFrames.length, 1);
  const totalTrips = fleetTrips.length;
  const avgRankingScore = rows.length
    ? rows.reduce((sum, row) => sum + row.score, 0) / rows.length
    : 0;
  const fleetAvgRisk = rows.length
    ? rows.reduce((sum, row) => sum + row.avgRisk, 0) / rows.length
    : 0;
  const fleetMaxRisk = rows.length
    ? Math.max(...rows.map((row) => row.maxRisk))
    : 0;
  const highRiskFrames = allFrames.filter((frame) => finiteNumber(frame.risk?.final_risk_score) >= 80).length;
  const highRiskPct = (highRiskFrames / totalFrames) * 100;
  const distractedFrames = allFrames.filter((frame) => frame.driver?.state === 'distracted').length;
  const distractedPct = (distractedFrames / totalFrames) * 100;
  const fatigueFrames = allFrames.filter((frame) => ['drowsy', 'yawning', 'microsleep'].includes(frame.driver?.state ?? '')).length;
  const nearMissFrames = allFrames.filter((frame) => Number.isFinite(frame.min_ttc) && Number(frame.min_ttc) > 0 && Number(frame.min_ttc) <= 2.5).length;
  const harshEvents = rows.reduce((sum, row) => sum + row.harshEvents, 0);
  const criticalTrips = rows.filter((row) => row.riskLevel === 'CRITICAL').length;
  const coachingTrips = rows.filter((row) => row.score < 60 || row.riskLevel === 'CRITICAL').length;
  const bestTrip = [...rows].sort((a, b) => b.score - a.score)[0];
  const riskiestTrip = [...rows].sort((a, b) => a.score - b.score)[0];
  const liveAlertCount = new Set(liveAlerts.map((alert) => alert.event_id)).size;

  const chartData = rows.map((row) => ({
    trip: row.trip_id.replace('-Sample', ''),
    score: Number(row.score.toFixed(1)),
    avgRisk: Number(row.avgRisk.toFixed(1)),
    maxRisk: Number(row.maxRisk.toFixed(1)),
  }));

  const factors = [
    {
      label: 'Fleet average risk',
      value: fleetAvgRisk,
      display: `${format(fleetAvgRisk)}/100`,
      severity: fleetAvgRisk >= 70 ? 'HIGH' : fleetAvgRisk >= 50 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'High-risk frames',
      value: highRiskPct,
      display: `${highRiskFrames}/${allFrames.length}`,
      severity: highRiskFrames > 0 ? 'HIGH' : 'LOW',
    },
    {
      label: 'Distracted driving',
      value: distractedPct,
      display: `${format(distractedPct)}%`,
      severity: distractedPct >= 25 ? 'HIGH' : distractedPct > 0 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'Harsh behavior',
      value: harshEvents,
      display: `${harshEvents} events`,
      severity: harshEvents > 0 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'Fatigue frames',
      value: fatigueFrames,
      display: `${fatigueFrames} frames`,
      severity: fatigueFrames > 0 ? 'HIGH' : 'LOW',
    },
    {
      label: 'Near miss / TTC',
      value: nearMissFrames,
      display: `${nearMissFrames} frames`,
      severity: nearMissFrames > 0 ? 'HIGH' : 'LOW',
    },
  ] satisfies Array<{ label: string; value: number; display: string; severity: 'HIGH' | 'MEDIUM' | 'LOW' }>;

  const fleetInsights = [
    `Fleet hiện có ${totalTrips} trip với ${allFrames.length} frame telemetry. Fleet Ranking Score trung bình là ${format(avgRankingScore)}/100, nên đây là overview toàn bộ trip, không phải insight riêng của ${vehicle.trip_id}.`,
    `Có ${criticalTrips}/${totalTrips} trip ở mức CRITICAL và ${coachingTrips}/${totalTrips} trip cần coaching/đánh giá vận hành. Max risk toàn fleet đạt ${format(fleetMaxRisk)}/100.`,
    bestTrip
      ? `Trip tốt nhất theo ranking hiện tại là ${bestTrip.trip_id} (${format(bestTrip.score)}/100); trip rủi ro nhất là ${riskiestTrip?.trip_id ?? 'N/A'} (${format(riskiestTrip?.score)}/100).`
      : 'Chưa đủ dữ liệu ranking để xác định trip tốt nhất hoặc rủi ro nhất.',
    `Risk contributors toàn fleet: ${highRiskFrames} high-risk frames, ${distractedFrames} distracted frames, ${harshEvents} harsh events, ${nearMissFrames} near-miss/TTC frames và ${liveAlertCount} live alerts trong session hiện tại.`,
  ];

  const actionItems = [
    coachingTrips > 0
      ? `Ưu tiên coaching 24h cho ${coachingTrips} trip đang dưới ngưỡng an toàn hoặc CRITICAL.`
      : 'Không có trip nào cần coaching khẩn theo ranking hiện tại.',
    highRiskFrames > 0
      ? 'Audit các đoạn high-risk frame trước, vì đây là tín hiệu trực tiếp từ JSON/local AI risk model.'
      : 'Không có high-risk frame trong dataset đang load.',
    distractedPct >= 25
      ? 'Mất tập trung là contributor lớn ở cấp fleet; cần review cabin evidence theo từng trip.'
      : 'Mất tập trung chưa vượt ngưỡng contributor chính ở cấp fleet.',
  ];

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-[#070A12] p-6 text-white">
      <div className="mb-5 shrink-0">
        <h1 className="text-3xl font-extrabold">Performance Insights</h1>
        <p className="mt-1 text-sm text-slate-400">Fleet-wide situation, risk contributors and operating actions across all loaded trips.</p>
      </div>

      <section className="grid gap-3 lg:grid-cols-4">
        <InsightMetric icon={Gauge} label="Fleet ranking score" value={`${format(avgRankingScore)}/100`} sub={`${totalTrips} trips analyzed`} />
        <InsightMetric icon={AlertTriangle} label="Fleet risk" value={`${format(fleetAvgRisk)} avg`} sub={`Max ${format(fleetMaxRisk)}`} />
        <InsightMetric icon={TrendingUp} label="High-risk frames" value={String(highRiskFrames)} sub={`${format(highRiskPct)}% of all frames`} />
        <InsightMetric icon={Trophy} label="Lowest-risk trip" value={bestTrip?.trip_id ?? 'N/A'} sub={bestTrip ? `${format(bestTrip.score)}/100 ranking score` : 'No ranking data'} />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5">
          <h2 className="mb-4 text-xs font-black uppercase tracking-widest text-slate-400">Fleet Score vs Risk By Trip</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 18, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="#1E293B" />
                <XAxis dataKey="trip" tick={{ fill: '#94A3B8', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#E2E8F0' }} cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }} />
                <Bar dataKey="score" fill="#38BDF8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="avgRisk" fill="#F43F5E" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5">
          <h2 className="mb-4 text-xs font-black uppercase tracking-widest text-slate-400">Fleet Contributing Factors</h2>
          <div className="space-y-3">
            {factors.map((factor) => (
              <div key={factor.label} className="grid grid-cols-[1fr_96px_72px] items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm">
                <span className="font-bold text-slate-200">{factor.label}</span>
                <span className="font-mono text-sky-300">{factor.display}</span>
                <span className={`text-right text-[10px] font-black ${severityClass(factor.severity)}`}>{factor.severity}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-4 rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5">
        <div className="mb-4 flex items-center gap-2">
          <Brain className="h-5 w-5 text-sky-400" />
          <h2 className="text-xs font-black uppercase tracking-widest text-slate-400">Fleet Insight</h2>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {fleetInsights.map((insight) => (
            <div key={insight} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-sm leading-relaxed text-slate-300">
              {insight}
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-lg border border-sky-900/70 bg-sky-950/20 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-black text-sky-200">
            <ListChecks className="h-4 w-4" />
            Operating decision
          </div>
          <div className="space-y-2 text-sm leading-relaxed text-slate-300">
            {actionItems.map((item) => <p key={item}>{item}</p>)}
          </div>
        </div>
      </section>
      <button onClick={onOpenCopilot} className="fixed bottom-6 right-6 flex items-center justify-center rounded-full bg-sky-600 p-3.5 text-white shadow-xl" title="Open AI Copilot"><Sparkles className="h-5 w-5 text-amber-200" /></button>
    </div>
  );
};

const InsightMetric = ({ icon: Icon, label, value, sub }: { icon: React.ElementType; label: string; value: string; sub: string }) => (
  <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-4">
    <Icon className="mb-3 h-5 w-5 text-sky-400" />
    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</span>
    <div className="mt-1 text-2xl font-black text-slate-100">{value}</div>
    <div className="mt-1 text-xs text-slate-500">{sub}</div>
  </div>
);
