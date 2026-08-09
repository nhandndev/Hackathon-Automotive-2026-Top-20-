import React from 'react';
import { AlertTriangle, Database, Gauge, MapPin, Sparkles, Trash2, Truck, Video } from 'lucide-react';
import { Frame, TripData } from '../types';
import { buildRankingRows } from './DriverRankingView';

interface FleetMapViewProps {
  vehicles: TripData[];
  selectedVehicle: TripData | null;
  onSelectVehicle: (v: TripData) => void;
  onViewLiveFeed: (v: TripData) => void;
  onViewTripDetail: (v: TripData) => void;
  onIntervene: (v: TripData) => void;
  onOpenCopilot: () => void;
  onClearSavedTrips: () => void;
}

const finite = (value: unknown, digits = 1) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';

const finiteNumber = (value: unknown) =>
  typeof value === 'number' && Number.isFinite(value) ? value : null;

const formatSeconds = (value: unknown, digits = 2) => {
  const numeric = finiteNumber(value);
  return numeric === null ? 'No TTC data' : `${numeric.toFixed(digits)} s`;
};

const lastFiniteBy = <T,>(items: T[] | undefined, getValue: (item: T) => unknown) => {
  for (let index = (items?.length ?? 0) - 1; index >= 0; index -= 1) {
    const numeric = finiteNumber(getValue(items![index]));
    if (numeric !== null) return numeric;
  }
  return null;
};

const averageFiniteBy = <T,>(items: T[] | undefined, getValue: (item: T) => unknown) => {
  const values = (items ?? [])
    .map(getValue)
    .map(finiteNumber)
    .filter((value): value is number => value !== null);
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
};

const hasRealCoordinates = (coordinates?: { lat?: number; lon?: number }) => {
  const lat = finiteNumber(coordinates?.lat);
  const lon = finiteNumber(coordinates?.lon);
  return lat !== null && lon !== null && !(lat === 0 && lon === 0);
};

const statusFor = (trip: TripData) => {
  if (trip.runtime_status === 'running') return 'LIVE';
  if (trip.runtime_status === 'pending') return 'PENDING';
  const risk = trip.trip_aggregate?.risk_classification?.toLowerCase();
  if (risk === 'high' || risk === 'critical') return 'CRITICAL';
  if (risk === 'medium' || risk === 'at_risk') return 'WARNING';
  return 'SAFE';
};

const riskExplanationFor = (row: ReturnType<typeof buildRankingRows>[number] | undefined) => {
  if (!row) return 'No ranking evidence available.';
  const reasons = [
    row.avgRisk >= 60 ? `Average Risk Score ${row.avgRisk.toFixed(1)}` : null,
    row.maxRisk >= 80 ? `Maximum Risk Score ${row.maxRisk.toFixed(1)}` : null,
    row.criticalEvents > 0 ? `${row.criticalEvents} high-risk frames` : null,
    row.distractedPct > 0 ? `${row.distractedPct.toFixed(1)}% distracted` : null,
    row.harshEvents > 0 ? `${row.harshEvents} harsh behavior events` : null,
    row.nearMissCount > 0 ? `${row.nearMissCount} near miss events` : null,
  ].filter(Boolean);
  return reasons.length ? `Primary cause: ${reasons.slice(0, 3).join(' · ')}` : 'Primary cause: lowest relative risk in current fleet.';
};

export const FleetMapView: React.FC<FleetMapViewProps> = ({
  vehicles,
  selectedVehicle,
  onSelectVehicle,
  onViewLiveFeed,
  onViewTripDetail,
  onIntervene,
  onOpenCopilot,
  onClearSavedTrips,
}) => {
  const selected = selectedVehicle ?? vehicles[0] ?? null;

  if (!selected) {
    return (
      <div className="flex-1 grid place-items-center bg-[#070A12] text-slate-400">
        No trip data loaded.
      </div>
    );
  }

  const lastFrame = selected.frames?.[selected.frames.length - 1];
  const selectedRanking = buildRankingRows([selected])[0];
  const status = statusFor(selected);
  const coordinates = lastFrame?.ego?.geolocation;
  const lastTtc = finiteNumber(lastFrame?.min_ttc) ?? lastFiniteBy<Frame>(selected.frames, (frame) => frame.min_ttc);
  const avgHeadway = averageFiniteBy<Frame>(selected.frames, (frame) => frame.headway_sec) ?? finiteNumber(selected.trip_aggregate?.avg_headway_sec);
  const nearMissCount = selected.frames?.length
    ? selected.frames.filter((frame) => {
      const ttc = finiteNumber(frame.min_ttc);
      return ttc !== undefined && ttc > 0 && ttc <= 2.5;
    }).length
    : selected.trip_aggregate?.near_miss_count;
  const coordinateLabel = hasRealCoordinates(coordinates) ? null : 'No GPS coordinates in organizer dataset';

  return (
    <div className="flex-1 flex flex-col md:flex-row bg-[#070A12] overflow-hidden text-white">
      <aside className="w-full md:w-80 bg-[#0B0F19] border-r border-[#1E293B] flex flex-col shrink-0">
        <div className="p-4 border-b border-[#1E293B]">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold tracking-widest text-slate-300 uppercase">Fleet Overview</h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClearSavedTrips}
                title="Clear saved demo trips"
                className="flex items-center gap-1 rounded-md border border-red-500/40 px-2 py-1 text-[10px] font-bold uppercase text-red-300 hover:bg-red-950/60"
              >
                <Trash2 className="w-3 h-3" /> Clear
              </button>
              <span className="flex items-center gap-1.5 text-[10px] text-sky-300 font-mono">
                <Database className="w-3 h-3" /> ORGANIZER DATA
              </span>
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-500">Demo trips replay from JSON/local AI telemetry.</p>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {vehicles.map((trip) => {
            const frame = trip.frames?.[trip.frames.length - 1];
            const tripStatus = statusFor(trip);
            const active = trip.trip_id === selected.trip_id;
            return (
              <button
                key={trip.trip_id}
                onClick={() => onSelectVehicle(trip)}
                className={`w-full text-left rounded-xl border p-3.5 transition-colors ${
                  active ? 'border-sky-500 bg-slate-900' : 'border-[#1E293B] bg-[#0F172A] hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2 font-bold"><Truck className="w-4 h-4" />{trip.trip_id}</span>
                  <span className={`text-[10px] font-bold ${tripStatus === 'CRITICAL' ? 'text-red-400' : tripStatus === 'WARNING' || tripStatus === 'PENDING' ? 'text-amber-400' : tripStatus === 'LIVE' ? 'text-sky-400' : 'text-emerald-400'}`}>
                    {tripStatus}
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-[11px] text-slate-400">
                  <span>Speed<br /><b className="text-slate-200">{finite(frame?.ego?.speed_kmh)} km/h</b></span>
                  <span>TTC<br /><b className="text-slate-200">{formatSeconds(finiteNumber(frame?.min_ttc) ?? lastFiniteBy<Frame>(trip.frames, (item) => item.min_ttc))}</b></span>
                  <span>State<br /><b className="text-slate-200">{frame?.driver?.state ?? 'N/A'}</b></span>
                </div>
              </button>
            );
          })}
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-5 md:p-8">
        <div className="max-w-5xl mx-auto space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <span className="text-xs font-mono text-sky-400">FLEET OVERVIEW</span>
              <h1 className="mt-1 text-2xl font-extrabold">{selected.trip_id}</h1>
              <p className="mt-2 text-sm text-slate-400">{selected.metadata?.description ?? 'No trip description provided.'}</p>
            </div>
            <div className="max-w-md text-right">
              <span className={`rounded-full border px-3 py-1 text-xs font-bold ${status === 'CRITICAL' ? 'border-red-500 text-red-300' : status === 'WARNING' ? 'border-amber-500 text-amber-300' : 'border-emerald-500 text-emerald-300'}`}>
                {status}
              </span>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">{riskExplanationFor(selectedRanking)}</p>
            </div>
          </div>

          <section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Metric label="Last speed" value={`${finite(lastFrame?.ego?.speed_kmh)} km/h`} />
            <Metric label="Last valid TTC" value={formatSeconds(lastTtc)} />
            <Metric label="Fleet Ranking Score" value={finite(selectedRanking?.score)} />
            <Metric label="Maximum Risk Score" value={finite(selected.trip_aggregate?.max_risk_score)} />
          </section>

          <section className="grid md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5 space-y-4">
              <h2 className="font-bold flex items-center gap-2"><MapPin className="w-4 h-4 text-sky-400" />Location</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Info label="Latitude" value={coordinateLabel ?? finite(coordinates?.lat, 6)} />
                <Info label="Longitude" value={coordinateLabel ?? finite(coordinates?.lon, 6)} />
                <Info label="Map source" value={selected.metadata?.map ?? 'N/A'} />
                <Info label="Weather" value={selected.metadata?.weather ? `cloud ${finite(selected.metadata.weather.cloudiness, 0)}%` : 'N/A'} />
              </div>
              <p className="text-xs text-slate-500">{coordinateLabel ? 'Location unavailable. GPS information was not provided for this trip.' : 'GPS coordinates are available for this trip.'}</p>
            </div>

            <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5 space-y-4">
              <h2 className="font-bold flex items-center gap-2"><Gauge className="w-4 h-4 text-sky-400" />Recorded summary</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Info label="Frames" value={String(selected.frames?.length ?? 0)} />
                <Info label="Near Miss Count" value={String(nearMissCount ?? 'N/A')} />
                <Info label="Average Headway" value={formatSeconds(avgHeadway)} />
                <Info label="Driver state" value={lastFrame?.driver?.state ?? 'N/A'} />
                <Info label="Average Risk Score" value={finite(selectedRanking?.avgRisk)} />
                <Info label="Risk Classification" value={selected.trip_aggregate?.risk_classification ?? 'N/A'} />
              </div>
            </div>
          </section>

          <div className="flex flex-wrap gap-3">
            <button onClick={() => onViewLiveFeed(selected)} className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-bold hover:bg-sky-500"><Video className="w-4 h-4" />Live monitor</button>
            <button onClick={() => onViewTripDetail(selected)} className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-bold hover:bg-slate-800">Trip detail</button>
            {status !== 'SAFE' && <button onClick={() => onIntervene(selected)} className="flex items-center gap-2 rounded-lg border border-red-500 px-4 py-2 text-sm font-bold text-red-300 hover:bg-red-950"><AlertTriangle className="w-4 h-4" />Intervene</button>}
            <button onClick={onOpenCopilot} className="ml-auto flex items-center gap-2 rounded-lg border border-indigo-500 px-4 py-2 text-sm font-bold text-indigo-300 hover:bg-indigo-950"><Sparkles className="w-4 h-4" />AI Copilot</button>
          </div>
        </div>
      </main>
    </div>
  );
};

const Metric = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-xl border border-[#1E293B] bg-[#0F172A] p-4"><span className="text-[10px] uppercase tracking-wider text-slate-500">{label}</span><div className="mt-1 text-xl font-mono font-bold">{value}</div></div>
);

const Info = ({ label, value }: { label: string; value: string }) => (
  <div><span className="block text-[10px] uppercase tracking-wider text-slate-500">{label}</span><span className="text-slate-200">{value}</span></div>
);
