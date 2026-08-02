import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Brain, Play, Sparkles, Wifi, WifiOff } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
import { DecisionAlert, LiveSnapshot, TripData } from '../types';
import { LiveCameraFrame } from './LiveCameraFrame';

interface TripDetailViewProps {
  vehicle: TripData;
  liveAlerts: DecisionAlert[];
  alertsConnected: boolean;
  onViewLiveFeed: () => void;
  onOpenCopilot: () => void;
}

interface LivePoint {
  frame: number;
  speed: number;
  risk: number;
  ttc: number | null;
}

const formatNumber = (value: number | null | undefined, digits = 1) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';

export const TripDetailView: React.FC<TripDetailViewProps> = ({
  vehicle,
  liveAlerts,
  alertsConnected,
  onViewLiveFeed,
  onOpenCopilot,
}) => {
  const [snapshot, setSnapshot] = useState<LiveSnapshot | null>(null);
  const [snapshotConnected, setSnapshotConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<LivePoint[]>([]);
  const snapshotEndpoint = import.meta.env.VITE_LIVE_SNAPSHOT_URL
    || 'http://127.0.0.1:8000/api/v1/alerts/snapshot';

  useEffect(() => {
    let stopped = false;
    let inFlight = false;
    setSnapshot(null);
    setTelemetry([]);

    const refresh = async () => {
      if (inFlight) return;
      inFlight = true;
      try {
        const separator = snapshotEndpoint.includes('?') ? '&' : '?';
        const response = await fetch(
          `${snapshotEndpoint}${separator}trip_id=${encodeURIComponent(vehicle.trip_id)}&v=${Date.now()}`,
          { cache: 'no-store' },
        );
        if (!response.ok) throw new Error(`snapshot ${response.status}`);
        const payload = await response.json() as LiveSnapshot;
        if (!stopped) {
          setSnapshot(payload);
          setSnapshotConnected(true);
          setTelemetry((points) => {
            if (points.at(-1)?.frame === payload.frame_id) return points;
            return [...points, {
              frame: payload.frame_id,
              speed: payload.speed_kmh,
              risk: payload.risk_score,
              ttc: payload.predicted_ttc_sec,
            }].slice(-120);
          });
        }
      } catch {
        if (!stopped) setSnapshotConnected(false);
      } finally {
        inFlight = false;
      }
    };

    void refresh();
    const timer = window.setInterval(refresh, 200);
    return () => {
      stopped = true;
      window.clearInterval(timer);
    };
  }, [snapshotEndpoint, vehicle.trip_id]);

  const tripAlerts = useMemo(
    () => liveAlerts.filter((alert) => alert.trip_id === vehicle.trip_id),
    [liveAlerts, vehicle.trip_id],
  );
  const latestAlert = tripAlerts[0];
  const eventCounts = useMemo(() => {
    const unique = new Map<string, DecisionAlert>();
    for (const alert of tripAlerts) if (!unique.has(alert.event_id)) unique.set(alert.event_id, alert);
    const counts = new Map<string, number>();
    for (const alert of unique.values()) counts.set(alert.alert_type, (counts.get(alert.alert_type) ?? 0) + 1);
    return [...counts.entries()];
  }, [tripAlerts]);

  const safetyScore = snapshot ? Math.max(0, Math.min(100, 100 - snapshot.risk_score)) : null;

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden bg-[#070A12] p-4 text-white md:p-6">
      <div className="flex shrink-0 items-center justify-between">
        <div>
          <div className="mb-0.5 flex items-center gap-1.5 font-mono text-[10px] text-slate-400"><span>FLEET</span><span>&gt;</span><span>SAFETY</span><span>&gt;</span><b className="text-slate-200">TRIP {vehicle.trip_id}</b></div>
          <h1 className="text-xl font-black tracking-tight">Trip Detail: {vehicle.trip_id}</h1>
        </div>
        <button onClick={onViewLiveFeed} className="flex items-center gap-1.5 rounded bg-sky-600 px-3 py-1.5 text-[11px] font-bold"><Play className="h-3.5 w-3.5 fill-current" />Live Feed</button>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="flex min-h-0 flex-col gap-4 lg:col-span-8">
          <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-[#1E293B] bg-[#0B0F19] p-3">
            <div className="mb-2 flex shrink-0 items-center justify-between">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-slate-300">Synchronized AI camera frames</span>
              <span className={`flex items-center gap-1 text-[9px] font-bold ${snapshotConnected ? 'text-emerald-400' : 'text-slate-500'}`}>{snapshotConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}{snapshotConnected ? `LIVE · FRAME ${snapshot?.frame_id}` : 'OFFLINE'}</span>
            </div>
            <div className="grid min-h-0 flex-1 grid-cols-2 gap-3">
              <div className="relative h-full overflow-hidden rounded-lg border border-slate-800 bg-slate-950"><LiveCameraFrame tripId={vehicle.trip_id} camera="cabin" className="absolute inset-0 h-full w-full object-cover" /></div>
              <div className="relative h-full overflow-hidden rounded-lg border border-slate-800 bg-slate-950"><LiveCameraFrame tripId={vehicle.trip_id} camera="road" className="absolute inset-0 h-full w-full object-cover" /></div>
            </div>
          </div>

          <div className="flex h-48 shrink-0 flex-col rounded-xl border border-[#1E293B] bg-[#0B0F19] p-3">
            <div className="mb-1 flex shrink-0 items-center justify-between"><span className="text-[10px] font-bold uppercase text-slate-300">Live telemetry · current session</span><div className="flex gap-3 font-mono text-[9px] text-slate-400"><span className="text-sky-400">— Speed</span><span className="text-indigo-400">— C3 Risk</span></div></div>
            <div className="min-h-0 flex-1">
              {telemetry.length < 2 ? <div className="grid h-full place-items-center text-xs text-slate-500">Waiting for realtime telemetry…</div> : (
                <ResponsiveContainer width="100%" height="100%"><LineChart data={telemetry} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}><XAxis dataKey="frame" stroke="#475569" fontSize={9} tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} stroke="#475569" fontSize={9} tickLine={false} axisLine={false} /><Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', fontSize: '10px' }} /><Line type="monotone" dataKey="speed" stroke="#38bdf8" strokeWidth={2} dot={false} isAnimationActive={false} /><Line type="monotone" dataKey="risk" stroke="#818cf8" strokeWidth={1.5} strokeDasharray="3 3" dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        <div className="flex min-h-0 flex-col gap-4 lg:col-span-4">
          <div className="shrink-0 rounded-xl border border-[#1E293B] bg-[#0B0F19] p-4">
            <div className="flex justify-between"><span className="text-[10px] font-bold uppercase text-slate-300">Challenge 3 scores</span><AlertTriangle className="h-3.5 w-3.5 text-amber-400" /></div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center"><Metric label="SAFE" value={formatNumber(safetyScore)} /><Metric label="RISK" value={formatNumber(snapshot?.risk_score)} /><Metric label="TTC" value={snapshot?.predicted_ttc_sec === null ? '∞' : formatNumber(snapshot?.predicted_ttc_sec, 2)} /></div>
            <p className="mt-3 text-[9px] text-slate-500">Safe Score = 100 − C3 Risk Score. TTC originates from Challenge 1 and is consumed by Challenge 3.</p>
          </div>

          <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-sky-900/50 bg-[#0B0F19] p-4">
            <div className="mb-2 flex shrink-0 items-center justify-between text-[10px] font-bold uppercase text-sky-400"><span className="flex items-center gap-1.5"><Brain className="h-3.5 w-3.5" />Realtime evidence</span><span className={alertsConnected ? 'text-emerald-400' : 'text-slate-500'}>{alertsConnected ? 'EVENTS LIVE' : 'EVENTS OFFLINE'}</span></div>
            {!snapshot ? <div className="grid flex-1 place-items-center text-xs text-slate-500">No live snapshot received.</div> : <div className="space-y-2 overflow-y-auto rounded-lg border border-sky-900/30 bg-[#0F172A] p-3 text-[10px] text-slate-200"><p className="font-mono text-sky-300">frame={snapshot.frame_id} · t={(snapshot.trip_timestamp_ms / 1000).toFixed(2)}s</p><p>Speed: <b>{snapshot.speed_kmh.toFixed(1)} km/h</b> · TTC: <b>{snapshot.predicted_ttc_sec === null ? '∞' : `${snapshot.predicted_ttc_sec.toFixed(2)}s`}</b></p><p>Driver: <b>{snapshot.driver_state}</b> · confidence <b>{Math.round(snapshot.driver_confidence * 100)}%</b> · alertness <b>{Math.round(snapshot.alertness_score * 100)}%</b></p><p>C3 Risk: <b className="text-amber-400">{snapshot.risk_score.toFixed(1)}/100</b></p>{latestAlert && <div className="border-t border-slate-700 pt-2"><b className="uppercase text-amber-300">{latestAlert.status} · {latestAlert.alert_type.replaceAll('_', ' ')}</b><p className="mt-1 text-slate-400">{latestAlert.recommended_action}</p></div>}</div>}
          </div>

          <div className="shrink-0 rounded-xl border border-[#1E293B] bg-[#0B0F19] p-4"><span className="mb-2 block text-[10px] font-bold uppercase text-slate-300">Decision events · current session</span>{eventCounts.length === 0 ? <p className="text-[10px] text-slate-500">No DecisionEvent received.</p> : <div className="flex max-h-24 flex-col gap-1.5 overflow-y-auto text-[10px]">{eventCounts.map(([type, count]) => <div key={type} className="flex justify-between rounded border border-slate-700 bg-slate-900 p-1.5"><span>{type.replaceAll('_', ' ')}</span><b className="font-mono">×{count}</b></div>)}</div>}</div>
        </div>
      </div>

      <button onClick={onOpenCopilot} className="fixed bottom-6 right-6 z-30 flex items-center justify-center rounded-full bg-sky-600 p-3 text-white shadow-xl"><Sparkles className="h-4 w-4 text-amber-200" /></button>
    </div>
  );
};

const Metric = ({ label, value }: { label: string; value: string }) => <div className="rounded-lg border border-slate-800 bg-slate-950 p-2"><span className="block text-[8px] text-slate-500">{label}</span><b className="font-mono text-lg">{value}</b></div>;
