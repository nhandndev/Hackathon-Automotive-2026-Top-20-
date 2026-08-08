import React from 'react';
import { AlertTriangle, Gauge, Sparkles, TrendingUp } from 'lucide-react';
import { DecisionAlert, TripData } from '../types';
import { buildRankingRows } from './DriverRankingView';

interface PerformanceInsightsViewProps {
  vehicle: TripData;
  liveAlerts?: DecisionAlert[];
  onOpenCopilot: () => void;
}

export const PerformanceInsightsView: React.FC<PerformanceInsightsViewProps> = ({ vehicle, liveAlerts = [], onOpenCopilot }) => {
  const summary = vehicle.driver_summary;
  const canonicalRow = buildRankingRows([vehicle])[0];
  const finite = (value: unknown, digits = 1) =>
    typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';
  const validHeadways = (vehicle.frames ?? [])
    .map((frame) => frame.headway_sec)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value) && value > 0);
  const avgHeadway = validHeadways.length
    ? validHeadways.reduce((sum, value) => sum + value, 0) / validHeadways.length
    : vehicle.trip_aggregate?.avg_headway_sec;
  const tripSessionAlerts = liveAlerts.filter(
    (alert) => alert.trip_id === vehicle.trip_id,
  );
  const liveMicrosleepCount = new Set(
    tripSessionAlerts
      .filter((alert) => alert.alert_type === 'microsleep')
      .map((alert) => alert.event_id),
  ).size;
  const microsleepCount = tripSessionAlerts.length > 0
    ? liveMicrosleepCount
    : summary?.microsleep_count ?? 0;
  const metrics = [
    ['Ranking score', finite(canonicalRow?.score)],
    ['Near misses', String(canonicalRow?.nearMissCount ?? 'N/A')],
    ['Maximum risk', finite(canonicalRow?.maxRisk)],
    ['Average headway', typeof avgHeadway === 'number' && Number.isFinite(avgHeadway) && avgHeadway > 0 ? `${avgHeadway.toFixed(2)}s` : 'No TTC data'],
    ['Microsleep count', microsleepCount.toString()],
    ['Average alertness', typeof summary?.average_alertness_score === 'number' ? `${Math.round(summary.average_alertness_score * 100)}%` : 'N/A'],
  ];

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#070A12] p-6 text-white">
      <div className="mb-4 shrink-0"><h1 className="text-3xl font-extrabold">Performance Insights</h1><p className="mt-1 text-sm text-slate-400">JSON/local AI telemetry for {vehicle.trip_id}; no synthetic fleet ranking.</p></div>
      <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-3">
        {metrics.map(([label, value], index) => (
          <div key={label} className="flex flex-col justify-center rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5">
            {index % 3 === 0 ? <Gauge className="mb-3 h-5 w-5 text-sky-400" /> : index % 3 === 1 ? <AlertTriangle className="mb-3 h-5 w-5 text-amber-400" /> : <TrendingUp className="mb-3 h-5 w-5 text-indigo-400" />}
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</span><span className="mt-2 text-3xl font-black">{value}</span>
          </div>
        ))}
      </div>
      <button onClick={onOpenCopilot} className="fixed bottom-6 right-6 flex items-center justify-center rounded-full bg-sky-600 p-3.5 text-white shadow-xl" title="Open AI Copilot"><Sparkles className="h-5 w-5 text-amber-200" /></button>
    </div>
  );
};
