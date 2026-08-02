import React from 'react';
import { AlertTriangle, Gauge, Sparkles, TrendingUp } from 'lucide-react';
import { DecisionAlert, TripData } from '../types';

interface PerformanceInsightsViewProps {
  vehicle: TripData;
  liveAlerts?: DecisionAlert[];
  onOpenCopilot: () => void;
}

export const PerformanceInsightsView: React.FC<PerformanceInsightsViewProps> = ({ vehicle, liveAlerts = [], onOpenCopilot }) => {
  const aggregate = vehicle.trip_aggregate;
  const summary = vehicle.driver_summary;
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
    : summary.microsleep_count;
  const metrics = [
    ['Safe driving score', aggregate.safe_driving_score.toFixed(1)],
    ['Near misses', aggregate.near_miss_count.toString()],
    ['Maximum risk', aggregate.max_risk_score.toFixed(1)],
    ['Average headway', `${aggregate.avg_headway_sec.toFixed(2)}s`],
    ['Microsleep count', microsleepCount.toString()],
    ['Average alertness', `${Math.round(summary.average_alertness_score * 100)}%`],
  ];

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#070A12] p-6 text-white">
      <div className="mb-4 shrink-0"><h1 className="text-3xl font-extrabold">Performance Insights</h1><p className="mt-1 text-sm text-slate-400">Organizer BTC data for {vehicle.trip_id}; no synthetic fleet ranking.</p></div>
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
