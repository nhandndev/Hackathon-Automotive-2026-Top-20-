import React, { useState, useEffect } from 'react';
import { AlertTriangle, Gauge, Video, AlertCircle, RefreshCw, Volume2, VolumeX, ShieldAlert } from 'lucide-react';
import { TripData } from '../types';

interface VehicleLiveViewProps {
  vehicle: TripData;
  onIntervene?: () => void;
}

export const VehicleLiveView: React.FC<VehicleLiveViewProps> = ({ vehicle, onIntervene }) => {
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [meshPulse, setMeshPulse] = useState(0);

  const lastFrame = vehicle.frames?.[vehicle.frames.length - 1];
  const initialSpeed = lastFrame?.ego?.speed_kmh || 0;
  const [mockSpeed, setMockSpeed] = useState(initialSpeed);
  const [mockGear, setMockGear] = useState('D');
  const [mockDriveMode, setMockDriveMode] = useState('NORMAL');

  useEffect(() => {
    const interval = setInterval(() => {
      setMeshPulse((prev) => (prev + 1) % 100);
    }, 150);
    return () => clearInterval(interval);
  }, []);

  // Limit log items so they don't scroll infinitely
  const displayEvents = vehicle.events_log?.slice(0, 5) || [];

  return (
    <div className="h-full bg-[#070A12] p-4 md:p-6 overflow-hidden text-white flex flex-col gap-4">
      
      {/* Top Section Stats Grid (Shrink 0) */}
      <div className="shrink-0 grid grid-cols-1 lg:grid-cols-12 gap-4 h-28">
        {/* Risk Score */}
        <div className="lg:col-span-2 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-2 flex flex-col items-center justify-center relative overflow-hidden group">
          <span className="text-[9px] font-bold tracking-widest text-slate-400 uppercase mb-1">RISK SCORE</span>
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" stroke="#1E293B" strokeWidth="12" fill="transparent" />
              <circle cx="50" cy="50" r="40" stroke="#ef4444" strokeWidth="12" fill="transparent" strokeDasharray={251.2} strokeDashoffset={251.2 * (1 - (lastFrame?.risk?.final_risk_score || 0) / 100)} strokeLinecap="round" />
            </svg>
            <span className="absolute text-xl font-extrabold text-white">{lastFrame?.risk?.final_risk_score || 0}</span>
          </div>
        </div>

        {/* Alert Banner + Speed Meter */}
        <div className="lg:col-span-8 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-3 flex flex-col justify-between">
          <div className="bg-gradient-to-r from-amber-600 to-red-600 rounded-lg p-3 flex items-center justify-between text-white border border-orange-400/30">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-200 animate-bounce" />
              <div>
                <h3 className="text-sm font-black tracking-wide leading-none">CRITICAL: DROWSY DRIVER DETECTED (US-01)</h3>
                <p className="text-[10px] text-orange-100 font-medium mt-1">Phát hiện tài xế vi ngủ. Cần thực hiện can thiệp khẩn cấp.</p>
              </div>
            </div>
            <button onClick={() => setIsAudioMuted(!isAudioMuted)} className="p-1.5 bg-black/30 hover:bg-black/50 rounded-lg transition-colors">
              {isAudioMuted ? <VolumeX className="w-4 h-4 text-slate-300" /> : <Volume2 className="w-4 h-4 text-amber-300 animate-pulse" />}
            </button>
          </div>
          <div className="flex items-center justify-end gap-2 mt-2 pr-2">
            <Gauge className="w-4 h-4 text-slate-400" />
            <span className="text-xl font-black text-white">{mockSpeed} <span className="text-xs font-normal text-slate-400">km/h</span></span>
          </div>
        </div>

        {/* TTC */}
        <div className="lg:col-span-2 bg-[#0B0F19] border border-red-900/50 rounded-xl p-3 flex flex-col justify-between items-center text-center">
          <span className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">TTC KPI</span>
          <div className="text-3xl font-extrabold text-red-500 flex items-baseline gap-1 my-1">
            {lastFrame?.min_ttc || 0}<span className="text-sm text-red-400">s</span>
          </div>
          {onIntervene && (
            <button onClick={onIntervene} className="w-full py-1 bg-red-600 text-white font-bold text-[10px] rounded uppercase tracking-wider">
              Can Thiệp
            </button>
          )}
        </div>
      </div>

      {/* Main Bottom Section (Flex-1) */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Col (8) - Videos + Workbench */}
        <div className="lg:col-span-8 flex flex-col gap-4 min-h-0">
          <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
            {/* Road Cam */}
            <div className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-2 flex flex-col">
              <div className="flex justify-between items-center px-1 mb-1 shrink-0">
                <span className="text-[10px] font-bold text-slate-300 tracking-wider uppercase flex items-center gap-1.5">
                  <Video className="w-3 h-3 text-sky-400" /> ROAD CAM
                </span>
                <span className="text-[9px] text-slate-500 font-mono">1080P</span>
              </div>
              <div className="relative flex-1 bg-slate-950 rounded-lg overflow-hidden border border-slate-800">
                <img src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" alt="Road" className="w-full h-full object-cover filter brightness-90 contrast-110" />
                <div className="absolute top-[35%] left-[38%] w-[28%] h-[40%] border-2 border-red-500/90 rounded bg-red-500/10 animate-pulse pointer-events-none">
                  <div className="absolute -top-5 left-0 bg-red-900/90 border border-red-500 text-[8px] text-red-100 font-mono px-1 rounded whitespace-nowrap">VEH AHEAD 2.4s</div>
                </div>
              </div>
            </div>

            {/* Cabin Cam */}
            <div className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-2 flex flex-col">
              <div className="flex justify-between items-center px-1 mb-1 shrink-0">
                <span className="text-[10px] font-bold text-slate-300 tracking-wider uppercase flex items-center gap-1.5">
                  <Video className="w-3 h-3 text-indigo-400" /> CABIN CAM
                </span>
                <div className="flex items-center gap-1 bg-amber-950/80 border border-amber-500/50 text-amber-300 text-[9px] font-bold px-1.5 py-0.5 rounded-full">
                  <ShieldAlert className="w-3 h-3" /> {Math.round((lastFrame?.driver?.alertness_score || 0) * 100)}%
                </div>
              </div>
              <div className="relative flex-1 bg-slate-950 rounded-lg overflow-hidden border border-slate-800">
                <img src="https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" alt="Cabin" className="w-full h-full object-cover filter brightness-75 contrast-125" />
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100">
                  <circle cx="48" cy="42" r="1.5" fill="#38bdf8" opacity="0.8" />
                  <circle cx="56" cy="42" r="1.5" fill="#38bdf8" opacity="0.8" />
                  <polygon points="42,35 62,35 65,58 52,65 39,58" fill="none" stroke="#38bdf8" strokeWidth="0.3" strokeDasharray="1,1" />
                  <line x1="35" y1={30 + (meshPulse % 40)} x2="68" y2={30 + (meshPulse % 40)} stroke="#ef4444" strokeWidth="0.5" opacity="0.6" />
                </svg>
                <div className="absolute bottom-2 left-2 bg-black/70 px-2 py-0.5 rounded text-[9px] font-mono text-slate-300 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" /> FATIGUE: HIGH
                </div>
              </div>
            </div>
          </div>

          {/* Workbench (Shrink 0) */}
          <div className="shrink-0 bg-[#111827] border border-[#374151] rounded-xl p-3 flex gap-4 items-center">
            <h2 className="text-[10px] font-bold text-sky-400 tracking-wider uppercase flex items-center gap-1.5 shrink-0">
              <Gauge className="w-3 h-3" /> Workbench
            </h2>
            <div className="flex-1 flex gap-4">
              <div className="flex-1">
                <label className="text-[9px] text-slate-400 font-bold block mb-1">Speed ({mockSpeed})</label>
                <input type="range" min="0" max="180" value={mockSpeed} onChange={(e) => setMockSpeed(parseInt(e.target.value))} className="w-full accent-sky-500 h-1" />
              </div>
              <div className="flex-1">
                <label className="text-[9px] text-slate-400 font-bold block mb-1">Gear</label>
                <div className="flex gap-1">
                  {['P', 'R', 'N', 'D'].map(g => (
                    <button key={g} onClick={() => setMockGear(g)} className={`flex-1 py-1 text-[9px] font-bold rounded ${mockGear === g ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-400'}`}>{g}</button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Col (4) - Event Log Table */}
        <div className="lg:col-span-4 bg-[#0B0F19] border border-[#1E293B] rounded-xl overflow-hidden flex flex-col min-h-0">
          <div className="px-4 py-2.5 border-b border-[#1E293B] flex items-center justify-between shrink-0">
            <h2 className="text-[10px] font-bold tracking-wider text-slate-300 uppercase">EVENT LOG</h2>
            <button className="text-slate-400 hover:text-white" title="Refresh"><RefreshCw className="w-3 h-3" /></button>
          </div>
          <div className="flex-1 overflow-hidden">
            <table className="w-full text-left text-[10px]">
              <thead className="bg-[#0F172A] text-slate-400 font-bold uppercase border-b border-[#1E293B]">
                <tr>
                  <th className="py-2 px-3">TIME</th>
                  <th className="py-2 px-3">EVENT</th>
                  <th className="py-2 px-3 text-right">SEV</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B] font-mono">
                {displayEvents.map((item, idx) => {
                  const severity = item.params?.severity || 'LOW';
                  return (
                    <tr key={idx} className={severity === 'CRITICAL' ? 'bg-red-950/50 text-red-200 border-l-2 border-l-red-500' : 'text-slate-200'}>
                      <td className="py-2.5 px-3 text-slate-400">{item.t}</td>
                      <td className="py-2.5 px-3 font-sans truncate max-w-[120px]">{item.type}</td>
                      <td className="py-2.5 px-3 text-right font-bold">
                        {severity === 'CRITICAL' && <span className="text-red-400">CRIT</span>}
                        {severity === 'HIGH' && <span className="text-orange-400">HIGH</span>}
                        {severity === 'MEDIUM' && <span className="text-amber-400">MED</span>}
                        {severity === 'LOW' && <span className="text-slate-400">LOW</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};
