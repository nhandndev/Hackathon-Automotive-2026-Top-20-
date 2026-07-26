import React, { useState } from 'react';
import { Truck, Video, Layers, Sun, Shield, Plus, Minus, Target, Sparkles, AlertTriangle, ChevronRight } from 'lucide-react';
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

export const FleetMapView: React.FC<FleetMapViewProps> = ({
  vehicles,
  selectedVehicle,
  onSelectVehicle,
  onViewLiveFeed,
  onViewTripDetail,
  onIntervene,
  onOpenCopilot,
}) => {
  const [activeTab, setActiveTab] = useState<'RISK' | 'ALL'>('RISK');
  const [zoomLevel, setZoomLevel] = useState(12);

  const getComputedStatus = (v: TripData) => {
    const risk = v.trip_aggregate?.risk_classification?.toLowerCase();
    if (risk === 'high') return 'CRITICAL';
    if (risk === 'medium') return 'WARNING';
    if (v.frames?.[0]?.ego?.speed_kmh === 0) return 'IDLE';
    return 'SAFE';
  };

  const criticalVehicles = vehicles.filter((v) => getComputedStatus(v) === 'CRITICAL' || getComputedStatus(v) === 'WARNING');
  const displayedVehicles = activeTab === 'RISK' ? criticalVehicles : vehicles;

  return (
    <div className="flex-1 flex flex-col md:flex-row bg-[#070A12] overflow-hidden relative text-white">
      {/* Secondary Left Fleet Drawer ("ACTIVE FLEET") */}
      <div className="w-full md:w-80 bg-[#0B0F19] border-r border-[#1E293B] flex flex-col z-10 shrink-0">
        {/* Drawer Header & Tabs */}
        <div className="p-4 border-b border-[#1E293B] space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold tracking-widest text-slate-300 uppercase">
              ACTIVE FLEET
            </h2>
            <span className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live
            </span>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-2">
            <button
              id="btn-fleet-tab-risk"
              onClick={() => setActiveTab('RISK')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-all ${
                activeTab === 'RISK'
                  ? 'bg-red-950/80 border-red-500 text-red-200 shadow-sm shadow-red-900/40'
                  : 'bg-[#111827] border-[#1F2937] text-slate-400 hover:text-slate-200'
              }`}
            >
              Risk Zone ({criticalVehicles.length})
            </button>
            <button
              id="btn-fleet-tab-all"
              onClick={() => setActiveTab('ALL')}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-all ${
                activeTab === 'ALL'
                  ? 'bg-sky-950/80 border-sky-500 text-sky-200 shadow-sm'
                  : 'bg-[#111827] border-[#1F2937] text-slate-400 hover:text-slate-200'
              }`}
            >
              All Assets ({vehicles.length})
            </button>
          </div>
        </div>

        {/* Vehicle Card List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {displayedVehicles.map((veh) => {
            const isSelected = selectedVehicle?.trip_id === veh.trip_id;
            const status = getComputedStatus(veh);
            const isCritical = status === 'CRITICAL';
            const lastFrame = veh.frames?.[veh.frames.length - 1];
            const speed = lastFrame?.ego?.speed_kmh || 0;
            const ttc = lastFrame?.min_ttc || 'N/A';

            if (isCritical) {
              return (
                <div
                  key={veh.trip_id}
                  onClick={() => onSelectVehicle(veh)}
                  className={`bg-[#201114] border border-red-500/80 rounded-xl p-3.5 space-y-3 cursor-pointer transition-all shadow-lg hover:shadow-red-950/50 ${
                    isSelected ? 'ring-2 ring-red-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse" />
                      <span className="text-base font-extrabold text-white tracking-wide">
                        {veh.trip_id}
                      </span>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-red-950 text-red-300 font-extrabold text-[10px] tracking-wider uppercase border border-red-600/50">
                      CRITICAL
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">
                        Driver Status
                      </span>
                      <span className="font-bold text-red-300">Drowsy / Vi ngủ</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 block uppercase">
                        TTC
                      </span>
                      <span className="font-mono font-extrabold text-red-400 text-sm">
                        {ttc}s
                      </span>
                    </div>
                  </div>

                  {/* Intervene Button & Camera Preview Toggle */}
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      id={`btn-intervene-${veh.trip_id}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onIntervene(veh);
                      }}
                      className="flex-1 py-1.5 bg-[#f87171] hover:bg-[#ef4444] text-slate-950 font-bold text-xs rounded-lg transition-colors shadow-sm"
                    >
                      Intervene
                    </button>
                    <button
                      id={`btn-cam-${veh.trip_id}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewLiveFeed(veh);
                      }}
                      className="p-1.5 bg-[#1F2937] hover:bg-[#374151] rounded-lg text-slate-200 transition-colors"
                      title="View Live Dual Cam"
                    >
                      <Video className="w-4 h-4 text-sky-400" />
                    </button>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={veh.trip_id}
                onClick={() => onSelectVehicle(veh)}
                className={`bg-[#0F172A] border border-[#1E293B] hover:border-slate-600 rounded-xl p-3.5 flex items-center justify-between cursor-pointer transition-all ${
                  isSelected ? 'border-sky-500 bg-slate-900/90' : ''
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Truck className="w-4 h-4 text-slate-400" />
                    <span className="text-sm font-bold text-white">{veh.trip_id}</span>
                    <span
                      className={`w-2 h-2 rounded-full ${
                        status === 'WARNING'
                          ? 'bg-amber-400 animate-pulse'
                          : status === 'IDLE'
                          ? 'bg-slate-400'
                          : 'bg-sky-400'
                      }`}
                    />
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {status === 'IDLE' ? 'Status: Idling' : `Speed: ${speed} km/h`}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onViewTripDetail(veh);
                    }}
                    className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
                    title="Trip details"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Center Dark Map Canvas Area */}
      <div className="flex-1 relative bg-[#090D16] overflow-hidden flex flex-col justify-between p-4">
        {/* Map Vector Graphic / Satellite Dark Theme Background simulation */}
        <div className="absolute inset-0 bg-[#090E1A] overflow-hidden pointer-events-none">
          {/* Simulated Dark Map Grid Lines */}
          <svg className="w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#334155" strokeWidth="0.8" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            {/* Simulated Road Paths */}
            <path
              d="M -100,200 Q 300,100 600,400 T 1200,600"
              fill="none"
              stroke="#1E293B"
              strokeWidth="12"
            />
            <path
              d="M 200,-50 Q 400,300 700,500 T 1000,900"
              fill="none"
              stroke="#1E293B"
              strokeWidth="16"
            />
          </svg>
        </div>

        {/* Map Floating Controls (Top Right) */}
        <div className="absolute top-4 right-4 flex flex-col gap-2 z-20">
          <button className="p-2.5 bg-[#0F172A]/90 hover:bg-[#1E293B] border border-[#1E293B] rounded-lg text-slate-300 shadow-lg backdrop-blur-md transition-colors" title="Map Layers">
            <Layers className="w-4 h-4" />
          </button>
          <button className="p-2.5 bg-[#0F172A]/90 hover:bg-[#1E293B] border border-[#1E293B] rounded-lg text-slate-300 shadow-lg backdrop-blur-md transition-colors" title="Contrast Mode">
            <Sun className="w-4 h-4" />
          </button>
          <button className="p-2.5 bg-[#0F172A]/90 hover:bg-[#1E293B] border border-[#1E293B] rounded-lg text-slate-300 shadow-lg backdrop-blur-md transition-colors" title="Geofence Safety">
            <Shield className="w-4 h-4" />
          </button>
          <div className="h-2" />
          <button
            onClick={() => setZoomLevel((z) => Math.min(z + 1, 18))}
            className="p-2.5 bg-[#0F172A]/90 hover:bg-[#1E293B] border border-[#1E293B] rounded-lg text-slate-300 shadow-lg backdrop-blur-md transition-colors"
            title="Zoom In"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoomLevel((z) => Math.max(z - 1, 5))}
            className="p-2.5 bg-[#0F172A]/90 hover:bg-[#1E293B] border border-[#1E293B] rounded-lg text-slate-300 shadow-lg backdrop-blur-md transition-colors"
            title="Zoom Out"
          >
            <Minus className="w-4 h-4" />
          </button>
          <button className="p-2.5 bg-[#0F172A]/90 hover:bg-[#1E293B] border border-[#1E293B] rounded-lg text-slate-300 shadow-lg backdrop-blur-md transition-colors" title="Recenter Target">
            <Target className="w-4 h-4" />
          </button>
        </div>

        {/* Interactive Vehicle Markers overlay on the map */}
        <div className="relative w-full h-full min-h-[450px] z-10 flex items-center justify-center">
          {/* VH-04 Marker (Critical Callout) */}
          <div
            onClick={() => onSelectVehicle(vehicles.find((v) => v.trip_id === 'VH-04') || vehicles[0])}
            className="absolute top-[42%] left-[58%] -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-30"
          >
            {/* Pulsating Callout speech bubble */}
            <div className="flex flex-col items-center animate-bounce">
              <div className="bg-[#f87171] border border-red-600 text-slate-950 font-black text-xs px-3 py-1 rounded-full shadow-xl flex items-center gap-1.5">
                <span>VH-04</span>
              </div>
              <div className="w-3 h-3 bg-[#f87171] rotate-45 -mt-1.5 border-r border-b border-red-600" />
            </div>
            {/* Pulsating truck node */}
            <div className="relative mt-1">
              <span className="absolute -inset-2 rounded-full bg-red-500/40 animate-ping" />
              <div className="w-9 h-9 rounded-full bg-red-600 border-2 border-white flex items-center justify-center text-white shadow-xl">
                <Truck className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* VH-01 Marker */}
          <div
            onClick={() => onSelectVehicle(vehicles.find((v) => v.trip_id === 'VH-01') || vehicles[1])}
            className="absolute top-[32%] left-[68%] cursor-pointer group z-20"
          >
            <div className="flex items-center gap-1.5 bg-[#1E293B] border border-slate-600 text-slate-200 text-[10px] font-bold px-2 py-0.5 rounded-md shadow">
              <Truck className="w-3 h-3 text-slate-300" />
              <span>VH-01</span>
            </div>
          </div>

          {/* VH-02 Marker */}
          <div
            onClick={() => onSelectVehicle(vehicles.find((v) => v.trip_id === 'VH-02') || vehicles[2])}
            className="absolute top-[62%] left-[52%] cursor-pointer group z-20"
          >
            <div className="flex items-center gap-1.5 bg-[#1E293B] border border-slate-600 text-slate-200 text-[10px] font-bold px-2 py-0.5 rounded-md shadow">
              <Truck className="w-3 h-3 text-slate-300" />
              <span>VH-02</span>
            </div>
          </div>

          {/* VH-05 Marker */}
          <div
            onClick={() => onSelectVehicle(vehicles.find((v) => v.trip_id === 'VH-05') || vehicles[3])}
            className="absolute top-[22%] left-[48%] cursor-pointer group z-20"
          >
            <div className="flex items-center gap-1.5 bg-[#1E293B] border border-slate-600 text-slate-300 text-[10px] font-bold px-2 py-0.5 rounded-md shadow">
              <Truck className="w-3 h-3 text-slate-400" />
              <span>VH-05</span>
            </div>
          </div>

          {/* VH-08 Warning Marker */}
          <div
            onClick={() => onSelectVehicle(vehicles.find((v) => v.trip_id === 'VH-08') || vehicles[4])}
            className="absolute top-[52%] left-[78%] cursor-pointer group z-20"
          >
            <div className="flex items-center gap-1.5 bg-amber-950/90 border border-amber-500 text-amber-200 text-[10px] font-bold px-2 py-0.5 rounded-md shadow">
              <Truck className="w-3 h-3 text-amber-400" />
              <span>VH-08</span>
            </div>
          </div>
        </div>

        {/* Bottom Bar Controls & Legend */}
        <div className="flex flex-wrap items-center justify-between gap-3 z-20 pt-2">
          {/* Active stats summary pill bar */}
          <div className="bg-[#0F172A]/90 border border-[#1E293B] rounded-full px-4 py-1.5 backdrop-blur-md text-xs font-mono flex items-center gap-4 text-slate-300 shadow-xl">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-sky-400" /> Active (8)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-400" /> Idle (3)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" /> Critical (1)
            </span>
          </div>

          {/* Status Legend Box (Bottom Right) */}
          <div className="bg-[#0F172A]/95 border border-[#1E293B] rounded-xl p-3 backdrop-blur-md shadow-2xl text-xs space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">
              STATUS LEGEND
            </span>
            <div className="space-y-1 font-medium text-slate-200 text-[11px]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                <span>Critical</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                <span>Warning</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                <span>Safe / Idle</span>
              </div>
            </div>
          </div>
        </div>

        {/* Floating Sparkle Copilot Action Button (Bottom Right) */}
        <button
          id="btn-fab-copilot"
          onClick={onOpenCopilot}
          className="absolute bottom-20 right-6 z-30 w-12 h-12 rounded-full bg-gradient-to-tr from-sky-500 via-blue-600 to-indigo-600 text-white shadow-xl shadow-sky-500/30 flex items-center justify-center hover:scale-110 active:scale-95 transition-transform border border-white/20"
          title="Open Fleet AI Copilot"
        >
          <Sparkles className="w-6 h-6 text-amber-200" />
        </button>
      </div>
    </div>
  );
};
