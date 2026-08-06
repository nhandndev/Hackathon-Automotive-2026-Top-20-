import React from 'react';
import { AlertTriangle, Database, Gauge, MapPin, Sparkles, Truck, Video } from 'lucide-react';
import { TripData } from '../types';

interface FleetMapViewProps {
  vehicles: TripData[];
  selectedVehicle: TripData | null;
  onSelectVehicle: (v: TripData) => void;
  onViewLiveFeed: (v: TripData) => void;
  onViewTripDetail: (v: TripData) => void;
  onIntervene: (v: TripData) => void;
  onOpenCopilot: () => void;
}

const finite = (value: unknown, digits = 1) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';

const statusFor = (trip: TripData) => {
  if (trip.runtime_status === 'running') return 'LIVE';
  if (trip.runtime_status === 'pending') return 'PENDING';
  const risk = trip.trip_aggregate?.risk_classification?.toLowerCase();
  if (risk === 'high' || risk === 'critical') return 'CRITICAL';
  if (risk === 'medium' || risk === 'at_risk') return 'WARNING';
  return 'SAFE';
};

export const FleetMapView: React.FC<FleetMapViewProps> = ({
  vehicles,
  selectedVehicle,
  onSelectVehicle,
  onViewLiveFeed,
  onViewTripDetail,
  onIntervene,
  onOpenCopilot,
}) => {
  const selected = selectedVehicle ?? vehicles[0] ?? null;

  if (!selected) {
    return (
      <div className="flex-1 grid place-items-center bg-[#070A12] text-slate-400">
        No organizer trip data loaded.
      </div>
    );
  }

  const lastFrame = selected.frames?.[selected.frames.length - 1];
  const status = statusFor(selected);
  const coordinates = lastFrame?.ego?.geolocation;

  return (
    <div className="flex-1 flex flex-col md:flex-row bg-[#070A12] overflow-hidden text-white">
      <aside className="w-full md:w-80 bg-[#0B0F19] border-r border-[#1E293B] flex flex-col shrink-0">
        <div className="p-4 border-b border-[#1E293B]">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold tracking-widest text-slate-300 uppercase">Dataset Fleet</h2>
            <span className="flex items-center gap-1.5 text-[10px] text-sky-300 font-mono">
              <Database className="w-3 h-3" /> ORGANIZER DATA
            </span>
          </div>
          <p className="mt-2 text-xs text-slate-500">Trips replay sequentially; completed histories remain selectable.</p>
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
                  <span>TTC<br /><b className="text-slate-200">{finite(frame?.min_ttc, 2)} s</b></span>
                  <span>Driver<br /><b className="text-slate-200">{frame?.driver?.state ?? 'N/A'}</b></span>
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
              <span className="text-xs font-mono text-sky-400">ORGANIZER DATASET SNAPSHOT</span>
              <h1 className="mt-1 text-2xl font-extrabold">{selected.trip_id}</h1>
              <p className="mt-2 text-sm text-slate-400">{selected.metadata?.description ?? 'No trip description provided.'}</p>
            </div>
            <span className={`rounded-full border px-3 py-1 text-xs font-bold ${status === 'CRITICAL' ? 'border-red-500 text-red-300' : status === 'WARNING' ? 'border-amber-500 text-amber-300' : 'border-emerald-500 text-emerald-300'}`}>
              {status}
            </span>
          </div>

          <section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Metric label="Last speed" value={`${finite(lastFrame?.ego?.speed_kmh)} km/h`} />
            <Metric label="Last TTC" value={`${finite(lastFrame?.min_ttc, 2)} s`} />
            <Metric label="Safe score" value={finite(selected.trip_aggregate?.safe_driving_score)} />
            <Metric label="Max risk" value={finite(selected.trip_aggregate?.max_risk_score)} />
          </section>

          <section className="grid md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5 space-y-4">
              <h2 className="font-bold flex items-center gap-2"><MapPin className="w-4 h-4 text-sky-400" />Recorded location</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Info label="Latitude" value={finite(coordinates?.lat, 6)} />
                <Info label="Longitude" value={finite(coordinates?.lon, 6)} />
                <Info label="Map source" value={selected.metadata?.map ?? 'N/A'} />
                <Info label="Weather" value={selected.metadata?.weather ? `cloud ${finite(selected.metadata.weather.cloudiness, 0)}%` : 'N/A'} />
              </div>
              <p className="text-xs text-slate-500">No synthetic map or vehicle positions are rendered.</p>
            </div>

            <div className="rounded-xl border border-[#1E293B] bg-[#0B0F19] p-5 space-y-4">
              <h2 className="font-bold flex items-center gap-2"><Gauge className="w-4 h-4 text-sky-400" />Recorded summary</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Info label="Frames" value={String(selected.frames?.length ?? 0)} />
                <Info label="Near misses" value={String(selected.trip_aggregate?.near_miss_count ?? 'N/A')} />
                <Info label="Avg. headway" value={`${finite(selected.trip_aggregate?.avg_headway_sec, 2)} s`} />
                <Info label="Driver state" value={lastFrame?.driver?.state ?? 'N/A'} />
              </div>
            </div>
          </section>

          <div className="flex flex-wrap gap-3">
            <button onClick={() => onViewLiveFeed(selected)} className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-bold hover:bg-sky-500"><Video className="w-4 h-4" />Live cameras</button>
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
