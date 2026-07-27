import React from 'react';
import { Download, Play, AlertTriangle, Sparkles, Brain, ShieldAlert } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, ReferenceDot } from 'recharts';
import { TripData } from '../types';
import { MOCK_TELEMETRY } from '../data/mockData';

interface TripDetailViewProps {
  vehicle: TripData;
  onViewLiveFeed: () => void;
  onOpenCopilot: () => void;
}

export const TripDetailView: React.FC<TripDetailViewProps> = ({
  vehicle,
  onViewLiveFeed,
  onOpenCopilot,
}) => {
  const lastFrame = vehicle.frames?.[vehicle.frames.length - 1];
  const safetyScore = vehicle.trip_aggregate?.safe_driving_score || 0;

  return (
    <div className="h-full bg-[#070A12] p-4 md:p-6 overflow-hidden text-white flex flex-col gap-4">
      {/* Top Header - Shrink 0 */}
      <div className="shrink-0 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono mb-0.5">
            <span>FLEET</span> <span>&gt;</span> <span>SAFETY</span> <span>&gt;</span> <span className="text-slate-200 font-bold">TRIP {vehicle.trip_id}</span>
          </div>
          <h1 className="text-xl font-black text-white tracking-tight">Trip Detail: {vehicle.trip_id}</h1>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 bg-[#111827] border border-[#1F2937] text-slate-200 text-[11px] rounded transition-colors">
            <Download className="w-3.5 h-3.5 text-slate-400" /> Export
          </button>
          <button onClick={onViewLiveFeed} className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 text-white font-bold text-[11px] rounded transition-colors">
            <Play className="w-3.5 h-3.5 fill-current" /> Live Feed
          </button>
        </div>
      </div>

      {/* Main Grid: 12 Cols (Flex-1) */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column (8 cols) - Cameras + Chart */}
        <div className="lg:col-span-8 flex flex-col gap-4 min-h-0">
          
          {/* Dual Cam (Flex-1) */}
          <div className="flex-1 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-3 flex flex-col min-h-0">
            <div className="flex justify-between items-center shrink-0 mb-2">
              <span className="text-[10px] font-bold text-slate-300 uppercase flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" /> Sync Dual Cam Feed
              </span>
              <span className="text-[9px] text-red-400 bg-red-950 px-1.5 py-0.5 rounded font-mono font-bold">● REC</span>
            </div>
            <div className="flex-1 grid grid-cols-2 gap-3 min-h-0">
              <div className="relative bg-slate-950 rounded-lg overflow-hidden border border-slate-800 h-full">
                <img src="https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" alt="Cabin" className="absolute inset-0 w-full h-full object-cover filter brightness-85" />
                <div className="absolute top-1 left-1 bg-black/60 px-1.5 py-0.5 rounded text-[9px] font-mono">CABIN</div>
              </div>
              <div className="relative bg-slate-950 rounded-lg overflow-hidden border border-slate-800 h-full">
                <img src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" alt="Road" className="absolute inset-0 w-full h-full object-cover filter brightness-90" />
                <div className="absolute top-1 left-1 bg-black/60 px-1.5 py-0.5 rounded text-[9px] font-mono">ROAD</div>
                <div className="absolute bottom-1 right-1 bg-black/70 px-1.5 py-0.5 rounded text-[8px] font-mono text-slate-200">HDWY 2.4s</div>
              </div>
            </div>
          </div>

          {/* Chart (Shrink-0, fixed height to ensure cameras get space) */}
          <div className="h-48 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-3 flex flex-col shrink-0">
            <div className="flex justify-between items-center mb-1 shrink-0">
              <span className="text-[10px] font-bold text-slate-300 uppercase">📈 Telemetry Sync</span>
              <div className="flex gap-3 text-[9px] font-mono text-slate-400">
                <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-sky-400"/> Speed</span>
                <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-indigo-400"/> HR</span>
              </div>
            </div>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={MOCK_TELEMETRY} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="time" stroke="#475569" fontSize={9} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 100]} stroke="#475569" fontSize={9} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', fontSize: '10px' }} />
                  <Line type="monotone" dataKey="speed" stroke="#38bdf8" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="hr" stroke="#818cf8" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                  <ReferenceDot x="01:30" y={65} r={4} fill="#ef4444" stroke="#fff" />
                  <ReferenceDot x="01:45" y={65} r={4} fill="#ef4444" stroke="#fff" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols) - Stats & Reasoning */}
        <div className="lg:col-span-4 flex flex-col gap-4 min-h-0">
          
          {/* Safety Score */}
          <div className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 flex flex-col items-center shrink-0">
            <div className="flex justify-between w-full mb-2">
              <span className="text-[10px] font-bold text-slate-300 uppercase">SAFETY SCORE</span>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="relative w-24 h-24 flex items-center justify-center my-1">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" stroke="#1E293B" strokeWidth="10" fill="transparent" />
                <circle cx="50" cy="50" r="40" stroke="#f97316" strokeWidth="10" fill="transparent" strokeDasharray={251.2} strokeDashoffset={251.2 * (1 - safetyScore / 100)} strokeLinecap="round" />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-2xl font-extrabold">{safetyScore}</span>
              </div>
            </div>
            <div className="w-full bg-red-950/60 border border-red-800/50 rounded-lg p-2 text-[9px] text-red-200 mt-2 flex gap-1.5">
              <ShieldAlert className="w-3 h-3 text-red-400 shrink-0" />
              <span>Score dropped 28 points due to critical events.</span>
            </div>
          </div>

          {/* AI Reasoning (Flex-1) */}
          <div className="flex-1 bg-[#0B0F19] border border-sky-900/50 rounded-xl p-4 flex flex-col min-h-0">
            <div className="flex items-center gap-1.5 text-sky-400 text-[10px] font-bold uppercase mb-2 shrink-0">
              <Brain className="w-3.5 h-3.5" /> AI Risk Reasoning
            </div>
            <div className="bg-[#0F172A] border border-sky-900/30 rounded-lg p-3 text-[10px] text-slate-200 leading-relaxed overflow-y-auto">
              <span className="block mb-1.5 font-mono text-[9px] text-sky-300">
                [Base Risk: {lastFrame?.risk?.base_risk} × Factor: {lastFrame?.risk?.driver_factor} = {lastFrame?.risk?.final_risk_score}]
              </span>
              Chuyến đi bị trừ điểm do tài xế ở trạng thái <span className="font-bold text-red-400">{lastFrame?.driver?.state}</span>. Mức tỉnh táo: <span className="font-bold text-amber-400">{Math.round((lastFrame?.driver?.alertness_score || 0) * 100)}%</span>.
            </div>
          </div>

          {/* Anomalies (Shrink-0) */}
          <div className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 shrink-0">
            <span className="text-[10px] font-bold text-slate-300 uppercase block mb-2">ANOMALIES</span>
            <div className="flex flex-col gap-1.5 text-[10px]">
              <div className="flex justify-between p-1.5 rounded bg-red-950/40 text-red-200 border border-red-800/30">
                <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-red-500" /> Microsleep</span>
                <span className="font-mono font-bold">x{vehicle.driver_summary?.microsleep_count || 0}</span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-amber-950/40 text-amber-200 border border-amber-800/30">
                <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" /> Hard Braking</span>
                <span className="font-mono font-bold">x{vehicle.trip_aggregate?.harsh_brake_count || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <button onClick={onOpenCopilot} className="fixed bottom-6 right-6 z-30 p-3 bg-sky-600 hover:bg-sky-500 rounded-full text-white shadow-xl flex items-center justify-center">
        <Sparkles className="w-4 h-4 text-amber-200" />
      </button>
    </div>
  );
};
