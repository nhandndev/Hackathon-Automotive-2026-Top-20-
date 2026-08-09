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

const tooltipFormatter = (value: number | string, name: string) => {
  const numeric = Number(value);
  const formatted = Number.isFinite(numeric) ? `${numeric.toFixed(1)}/100` : String(value);
  return [formatted, name];
};

export const PerformanceInsightsView: React.FC<PerformanceInsightsViewProps> = ({
  vehicle,
  vehicles = [vehicle],
  liveAlerts = [],
  onOpenCopilot,
}) => {
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
    ? rows.reduce((max, row) => Math.max(max, row.maxRisk), 0)
    : 0;

  const highRiskFrames = allFrames.filter((frame) => finiteNumber(frame.risk?.final_risk_score) >= 80).length;
  const highRiskPct = (highRiskFrames / totalFrames) * 100;
  const distractedFrames = allFrames.filter((frame) => frame.driver?.state === 'distracted').length;
  const distractedPct = (distractedFrames / totalFrames) * 100;
  const fatigueFrames = allFrames.filter((frame) => ['drowsy', 'yawning', 'microsleep'].includes(frame.driver?.state ?? '')).length;
  const microsleepCount = fleetTrips.reduce((sum, trip) => sum + finiteNumber(trip.driver_summary?.microsleep_count), 0);
  const nearMissFrames = allFrames.filter((frame) => Number.isFinite(frame.min_ttc) && Number(frame.min_ttc) > 0 && Number(frame.min_ttc) <= 2.5).length;
  const validHeadways = allFrames
    .map((frame) => frame.headway_sec)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value) && value > 0);
  const avgHeadway = validHeadways.length
    ? validHeadways.reduce((sum, value) => sum + value, 0) / validHeadways.length
    : fleetTrips.length
      ? fleetTrips.reduce((sum, trip) => sum + finiteNumber(trip.trip_aggregate?.avg_headway_sec), 0) / fleetTrips.length
      : 0;
  const avgAlertness = fleetTrips.length
    ? fleetTrips.reduce((sum, trip) => sum + finiteNumber(trip.driver_summary?.average_alertness_score, 1), 0) / fleetTrips.length
    : 1;
  const harshEvents = rows.reduce((sum, row) => sum + row.harshEvents, 0);
  const criticalTrips = rows.filter((row) => row.riskLevel === 'CRITICAL').length;
  const coachingTrips = rows.filter((row) => row.score < 60 || row.riskLevel === 'CRITICAL').length;
  const bestTrip = [...rows].sort((a, b) => b.score - a.score)[0];
  const riskiestTrip = [...rows].sort((a, b) => a.score - b.score)[0];
  const liveAlertCount = new Set(liveAlerts.map((alert) => alert.event_id)).size;

  const chartData = rows.map((row) => ({
    trip: row.trip_id.replace('-Sample', ''),
    rankingScore: Number(row.score.toFixed(1)),
    averageRiskScore: Number(row.avgRisk.toFixed(1)),
    maximumRiskScore: Number(row.maxRisk.toFixed(1)),
  }));

  const factors = [
    {
      label: 'Average Risk Score',
      value: fleetAvgRisk,
      display: `${format(fleetAvgRisk)}/100`,
      severity: fleetAvgRisk >= 70 ? 'HIGH' : fleetAvgRisk >= 50 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'High-Risk Frames',
      value: highRiskPct,
      display: `${highRiskFrames}/${allFrames.length}`,
      severity: highRiskFrames > 0 ? 'HIGH' : 'LOW',
    },
    {
      label: 'Distracted Driving',
      value: distractedPct,
      display: `${format(distractedPct)}%`,
      severity: distractedPct >= 25 ? 'HIGH' : distractedPct > 0 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'Harsh Behavior',
      value: harshEvents,
      display: `${harshEvents} events`,
      severity: harshEvents > 0 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'Fatigue Frames',
      value: fatigueFrames,
      display: `${fatigueFrames} frames`,
      severity: fatigueFrames > 0 ? 'HIGH' : 'LOW',
    },
    {
      label: 'Microsleep Count',
      value: microsleepCount,
      display: `${microsleepCount} events`,
      severity: microsleepCount > 0 ? 'HIGH' : 'LOW',
    },
    {
      label: 'Average Headway',
      value: avgHeadway,
      display: avgHeadway > 0 ? `${format(avgHeadway, 2)}s` : 'No TTC data',
      severity: avgHeadway > 0 && avgHeadway < 1.5 ? 'HIGH' : avgHeadway > 0 && avgHeadway < 3.0 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'Average Alertness',
      value: avgAlertness,
      display: `${Math.round(avgAlertness * 100)}%`,
      severity: avgAlertness < 0.5 ? 'HIGH' : avgAlertness < 0.75 ? 'MEDIUM' : 'LOW',
    },
    {
      label: 'Near Miss / TTC',
      value: nearMissFrames,
      display: `${nearMissFrames} frames`,
      severity: nearMissFrames > 0 ? 'HIGH' : 'LOW',
    },
  ] satisfies Array<{ label: string; value: number; display: string; severity: 'HIGH' | 'MEDIUM' | 'LOW' }>;

  const fleetInsights = [
    `Fleet currently has ${totalTrips} trip(s) with ${allFrames.length} telemetry frames. Average Fleet Ranking Score is ${format(avgRankingScore)}/100, so this page is a fleet-wide overview, not only ${vehicle.trip_id}.`,
    `There are ${criticalTrips}/${totalTrips} critical trip(s) and ${coachingTrips}/${totalTrips} trip(s) that need coaching or operational review. Fleet maximum risk reached ${format(fleetMaxRisk)}/100.`,
    bestTrip
      ? `Best current trip by ranking is ${bestTrip.trip_id} (${format(bestTrip.score)}/100); riskiest trip is ${riskiestTrip?.trip_id ?? 'N/A'} (${format(riskiestTrip?.score)}/100).`
      : 'Not enough ranking data to identify best or riskiest trip.',
    `Fleet risk contributors: ${highRiskFrames} high-risk frames, ${distractedFrames} distracted frames, ${fatigueFrames} fatigue frames, ${microsleepCount} microsleep event(s), ${harshEvents} harsh events, ${nearMissFrames} near-miss/TTC frames and ${liveAlertCount} live alerts in the current session.`,
  ];

  const actionItems = [
    coachingTrips > 0
      ? `Prioritize coaching within 24h for ${coachingTrips} trip(s) under the safety threshold or in CRITICAL status.`
      : 'No trip currently requires urgent coaching from the ranking view.',
    highRiskFrames > 0
      ? 'Audit high-risk frame segments first because these are direct evidence from local AI risk telemetry.'
      : 'No high-risk frame is present in the currently loaded dataset.',
    distractedPct >= 25
      ? 'Distraction is a major fleet contributor; review cabin evidence per affected trip.'
      : 'Distraction has not crossed the main fleet-contributor threshold.',
    microsleepCount > 0
      ? `Microsleep was detected ${microsleepCount} time(s); trigger rest policy and verify the corresponding cabin frames.`
      : 'No microsleep event is currently stored in the loaded fleet session.',
  ];

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-[#070A12] p-6 text-white">
      <div className="mb-5 shrink-0">
        <h1 className="text-3xl font-extrabold">Performance Insights</h1>
        <p className="mt-1 text-sm text-slate-400">Fleet-wide situation, risk contributors and operating actions across all loaded trips.</p>
      </div>

      <section className="grid gap-3 lg:grid-cols-4">
        <InsightMetric icon={Gauge} label="Average Fleet Ranking Score" value={`${format(avgRankingScore)}/100`} sub={`${totalTrips} trips analyzed`} />
        <InsightMetric icon={AlertTriangle} label="Average Risk Score" value={`${format(fleetAvgRisk)}/100`} sub={`Maximum Risk Score ${format(fleetMaxRisk)}/100`} />
        <InsightMetric icon={TrendingUp} label="High-Risk Frames" value={String(highRiskFrames)} sub={`${format(highRiskPct)}% of all frames`} />
        <InsightMetric icon={Trophy} label="Lowest-Risk Trip" value={bestTrip?.trip_id ?? 'N/A'} sub={bestTrip ? `${format(bestTrip.score)}/100 Fleet Ranking Score` : 'No ranking data'} />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5">
          <h2 className="mb-4 text-xs font-black uppercase tracking-widest text-slate-400">Fleet Ranking Score vs Average Risk Score by Trip</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 18, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="#1E293B" />
                <XAxis dataKey="trip" tick={{ fill: '#94A3B8', fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={tooltipFormatter}
                  contentStyle={{ background: '#0F172A', border: '1px solid #334155', borderRadius: 8, color: '#E2E8F0' }}
                  cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }}
                />
                <Bar dataKey="rankingScore" name="Fleet Ranking Score" fill="#38BDF8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="averageRiskScore" name="Average Risk Score" fill="#F43F5E" radius={[4, 4, 0, 0]} />
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
