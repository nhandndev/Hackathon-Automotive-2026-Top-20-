import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Gauge, ShieldAlert, Video, Wifi, WifiOff } from 'lucide-react';
import { DecisionAlert, InterventionNotif, LiveSnapshot, TripData } from '../types';
import { LiveCameraFrame } from './LiveCameraFrame';

interface VehicleLiveViewProps {
  vehicle: TripData;
  liveAlerts: DecisionAlert[];
  alertsConnected: boolean;
  onIntervene?: () => void;
  interventionNotif?: InterventionNotif | null;
}

const formatTtc = (value: number | null | undefined) => {
  if (value === null) return '∞';
  if (value === undefined) return '--';
  return value.toFixed(2);
};

const formatEventTime = (timestampMs: number) => `${(timestampMs / 1000).toFixed(1)}s`;

// ─── Web Audio alert — plays ONLY inside this AI window ────────────────────
function playAlertSound(type: InterventionNotif['type']) {
  try {
    const ctx = new AudioContext();
    const master = ctx.createGain();
    master.gain.value = 0.6;
    master.connect(ctx.destination);

    const schedule = (freq: number, startSec: number, durationSec: number) => {
      const osc = ctx.createOscillator();
      const env = ctx.createGain();
      osc.frequency.value = freq;
      osc.type = 'sine';
      env.gain.setValueAtTime(0, startSec);
      env.gain.linearRampToValueAtTime(1, startSec + 0.02);
      env.gain.linearRampToValueAtTime(0, startSec + durationSec);
      osc.connect(env);
      env.connect(master);
      osc.start(ctx.currentTime + startSec);
      osc.stop(ctx.currentTime + startSec + durationSec + 0.05);
    };

    if (type === 'alarm') {
      // 3 sharp beeps — high frequency (emergency)
      schedule(880, 0.0, 0.15);
      schedule(880, 0.2, 0.15);
      schedule(880, 0.4, 0.15);
      schedule(1100, 0.6, 0.25);
    } else if (type === 'stop') {
      // 2 medium tone beeps
      schedule(440, 0.0, 0.3);
      schedule(550, 0.4, 0.3);
    } else {
      // call — ringtone-style rising pair
      schedule(660, 0.0, 0.2);
      schedule(880, 0.25, 0.2);
      schedule(660, 0.55, 0.2);
      schedule(880, 0.80, 0.2);
    }
  } catch {
    // AudioContext blocked — silently skip
  }
}

export const VehicleLiveView: React.FC<VehicleLiveViewProps> = ({
  vehicle,
  liveAlerts,
  alertsConnected,
  onIntervene,
  interventionNotif,
}) => {
  const [snapshot, setSnapshot] = useState<LiveSnapshot | null>(null);
  const [snapshotConnected, setSnapshotConnected] = useState(false);
  const snapshotEndpoint = import.meta.env.VITE_LIVE_SNAPSHOT_URL
    || 'http://127.0.0.1:8000/api/v1/alerts/snapshot';

  // Play audio in a loop when a new notification arrives for this vehicle's trip, until completed
  useEffect(() => {
    if (!interventionNotif || interventionNotif.tripId !== vehicle.trip_id) {
      return;
    }
    
    // If the trip is already completed, do not play sound
    if (vehicle.runtime_status === 'completed') {
      return;
    }

    // Play immediately
    playAlertSound(interventionNotif.type);

    // Loop playing every 1.5 seconds
    const intervalId = setInterval(() => {
      // Check if it transitioned to completed during the interval
      if (vehicle.runtime_status === 'completed') {
        clearInterval(intervalId);
        return;
      }
      playAlertSound(interventionNotif.type);
    }, 1500);

    return () => clearInterval(intervalId);
  }, [interventionNotif, vehicle.trip_id, vehicle.runtime_status]);

  useEffect(() => {
    let stopped = false;
    let inFlight = false;
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
  const activeAlert = useMemo(() => {
    const latestStatus = new Set<string>();
    for (const alert of tripAlerts) {
      if (latestStatus.has(alert.event_id)) continue;
      latestStatus.add(alert.event_id);
      if (alert.status !== 'resolved') return alert;
    }
    return undefined;
  }, [tripAlerts]);

  const riskScore = snapshot?.risk_score;
  const riskPercent = Math.max(0, Math.min(100, riskScore ?? 0));
  const severityClass = activeAlert?.severity === 'critical'
    ? 'from-red-700 to-red-600 border-red-400/30'
    : activeAlert?.severity === 'warning'
      ? 'from-amber-700 to-orange-600 border-amber-400/30'
      : 'from-emerald-800 to-emerald-700 border-emerald-400/30';

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden bg-[#070A12] p-4 text-white md:p-6">
      <div className="grid h-28 shrink-0 grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="relative flex flex-col items-center justify-center overflow-hidden rounded-xl border border-[#1E293B] bg-[#0B0F19] p-2 lg:col-span-2">
          <span className="mb-1 text-[9px] font-bold uppercase tracking-widest text-slate-400">RISK SCORE</span>
          <div className="relative flex h-16 w-16 items-center justify-center">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="#1E293B" strokeWidth="12" fill="transparent" />
              <circle cx="50" cy="50" r="40" stroke="#ef4444" strokeWidth="12" fill="transparent" strokeDasharray={251.2} strokeDashoffset={251.2 * (1 - riskPercent / 100)} strokeLinecap="round" />
            </svg>
            <span className="absolute text-xl font-extrabold">{riskScore === undefined ? '--' : riskScore.toFixed(1)}</span>
          </div>
        </div>

        <div className="flex flex-col justify-between rounded-xl border border-[#1E293B] bg-[#0B0F19] p-3 lg:col-span-8">
          <div className={`flex items-center justify-between rounded-lg border bg-gradient-to-r p-3 ${severityClass}`}>
            <div className="flex items-center gap-2">
              {activeAlert ? <AlertTriangle className="h-5 w-5 text-amber-200" /> : <ShieldAlert className="h-5 w-5 text-emerald-200" />}
              <div>
                <h3 className="text-sm font-black uppercase tracking-wide leading-none">
                  {activeAlert ? `${activeAlert.severity}: ${activeAlert.alert_type.replaceAll('_', ' ')}` : snapshotConnected ? 'NO ACTIVE SAFETY ALERT' : 'WAITING FOR LIVE AI DATA'}
                </h3>
                <p className="mt-1 text-[10px] text-slate-100">
                  {activeAlert?.recommended_action || (snapshotConnected ? `Driver state: ${snapshot?.driver_state}` : 'Start the AI end-to-end pipeline')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs font-bold">
              {snapshotConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
              {snapshotConnected ? 'LIVE' : 'OFFLINE'}
            </div>
          </div>
          <div className="mt-2 flex items-center justify-end gap-2 pr-2">
            <Gauge className="h-4 w-4 text-slate-400" />
            <span className="text-xl font-black">{snapshot ? snapshot.speed_kmh.toFixed(1) : '--'} <span className="text-xs font-normal text-slate-400">km/h</span></span>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between rounded-xl border border-red-900/50 bg-[#0B0F19] p-3 text-center lg:col-span-2">
          <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">TTC</span>
          <div className="my-1 flex items-baseline gap-1 text-3xl font-extrabold text-red-500">
            {formatTtc(snapshot?.predicted_ttc_sec)}<span className="text-sm text-red-400">s</span>
          </div>
          {onIntervene && activeAlert && (
            <button onClick={onIntervene} className="w-full rounded bg-red-600 py-1 text-[10px] font-bold uppercase tracking-wider">Can thiệp</button>
          )}
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Camera grid — 2 panels side by side */}
        <div className="grid min-h-0 grid-cols-2 gap-4 lg:col-span-8">
          {/* ROAD CAM */}
          <div className="flex flex-col rounded-xl border border-[#1E293B] bg-[#0B0F19] p-2">
            <div className="mb-1 flex shrink-0 items-center justify-between px-1">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-300"><Video className="h-3 w-3 text-sky-400" /> ROAD CAM</span>
              <span className="font-mono text-[9px] text-slate-500">FRAME {snapshot?.frame_id ?? '--'}</span>
            </div>
            <div className="relative flex-1 overflow-hidden rounded-lg border border-slate-800 bg-slate-950">
              <LiveCameraFrame tripId={vehicle.trip_id} camera="road" className="h-full w-full object-cover" />
            </div>
          </div>

          {/* CABIN CAM */}
          <div className="flex flex-col rounded-xl border border-[#1E293B] bg-[#0B0F19] p-2">
            <div className="mb-1 flex shrink-0 items-center justify-between px-1">
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-300"><Video className="h-3 w-3 text-indigo-400" /> CABIN CAM</span>
              <div className="flex items-center gap-1 rounded-full border border-amber-500/50 bg-amber-950/80 px-1.5 py-0.5 text-[9px] font-bold text-amber-300">
                <ShieldAlert className="h-3 w-3" /> {snapshot ? `${Math.round(snapshot.alertness_score * 100)}%` : '--'}
              </div>
            </div>
            <div className="relative flex-1 overflow-hidden rounded-lg border border-slate-800 bg-slate-950">
              <LiveCameraFrame tripId={vehicle.trip_id} camera="cabin" className="h-full w-full object-cover" />
            </div>
          </div>
        </div>

        {/* Decision Event Log */}
        <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-[#1E293B] bg-[#0B0F19] lg:col-span-4">
          <div className="flex shrink-0 items-center justify-between border-b border-[#1E293B] px-4 py-2.5">
            <h2 className="text-[10px] font-bold uppercase tracking-wider text-slate-300">DECISION EVENT LOG</h2>
            <span className={`text-[9px] font-bold ${alertsConnected ? 'text-emerald-400' : 'text-slate-500'}`}>{alertsConnected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            {tripAlerts.length === 0 ? (
              <div className="flex h-full items-center justify-center p-5 text-center text-xs text-slate-500">No DecisionEvent received for this trip.</div>
            ) : (
              <table className="w-full text-left text-[10px]">
                <thead className="sticky top-0 border-b border-[#1E293B] bg-[#0F172A] font-bold uppercase text-slate-400">
                  <tr><th className="px-3 py-2">Time</th><th className="px-3 py-2">Event / action</th><th className="px-3 py-2 text-right">State</th></tr>
                </thead>
                <tbody className="divide-y divide-[#1E293B]">
                  {tripAlerts.slice(0, 30).map((alert) => (
                    <tr key={`${alert.event_id}-${alert.status}-${alert.trip_timestamp_ms}`} className={alert.severity === 'critical' ? 'bg-red-950/35' : ''}>
                      <td className="px-3 py-2 font-mono text-slate-400">{formatEventTime(alert.trip_timestamp_ms)}</td>
                      <td className="px-3 py-2"><div className="font-bold uppercase text-slate-100">{alert.alert_type.replaceAll('_', ' ')}</div><div className="max-w-[180px] truncate text-slate-400">{alert.recommended_action}</div></td>
                      <td className="px-3 py-2 text-right font-bold uppercase"><div className={alert.severity === 'critical' ? 'text-red-400' : 'text-amber-400'}>{alert.severity}</div><div className="text-slate-500">{alert.status}</div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
