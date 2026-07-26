import React, { useState } from 'react';
import { Trophy, AlertTriangle, TrendingUp, DollarSign, ChevronRight, Sparkles } from 'lucide-react';
import { MOCK_LEADERBOARD } from '../data/mockData';

interface PerformanceInsightsViewProps {
  onOpenCopilot: () => void;
}

export const PerformanceInsightsView: React.FC<PerformanceInsightsViewProps> = ({ onOpenCopilot }) => {
  const [driverA, setDriverA] = useState('8842');
  const [driverB, setDriverB] = useState('9102');

  // Slice to fit on screen without scrolling
  const topDrivers = MOCK_LEADERBOARD.filter((d) => d.type === 'SAFE').slice(0, 3);
  const atRiskDrivers = MOCK_LEADERBOARD.filter((d) => d.type === 'AT_RISK').slice(0, 2);

  return (
    <div className="h-full bg-[#070A12] p-4 md:p-6 overflow-hidden text-white flex flex-col">
      {/* Title Header - Shrink 0 */}
      <div className="shrink-0 mb-4">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Performance Insights
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Real-time analysis of fleet safety protocols and driver behavior.
        </p>
      </div>

      {/* Main Grid: 2 Rows, 12 Cols */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 grid-rows-2 gap-4">
        
        {/* ROW 1 */}
        {/* 1. Fleet Safety Leaderboard (Col span 4) */}
        <div className="lg:col-span-4 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3 shrink-0">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Fleet Safety Leaderboard
              </h2>
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-3 justify-around min-h-0">
            {/* Top Safe Drivers */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block">
                TOP SAFE DRIVERS
              </span>
              {topDrivers.map((item, idx) => (
                <div key={item.id} className="flex items-center justify-between p-2 rounded-lg bg-[#0F172A] border border-[#1E293B]">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-extrabold text-slate-400">#{idx + 1}</span>
                    <span className="text-xs font-bold text-slate-100">{item.name}</span>
                    {item.badge && (
                      <span className="text-[9px] font-extrabold bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-extrabold text-white font-mono">{item.score}</span>
                </div>
              ))}
            </div>

            {/* At-Risk Drivers */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block">
                AT-RISK (COACHING REQUIRED)
              </span>
              {atRiskDrivers.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 rounded-lg bg-[#0F172A] border border-amber-900/30">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    <span className="text-xs font-bold text-slate-100">{item.name}</span>
                  </div>
                  <span className="text-xs font-extrabold text-amber-300 font-mono">{item.score}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 3. Telemetry Comparison (Col span 8) */}
        <div className="lg:col-span-8 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 flex flex-col">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 shrink-0 mb-3">
            ✈️ Telemetry Comparison
          </h2>
          <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
            {/* Driver A */}
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 flex flex-col items-center justify-center">
              <select value={driverA} onChange={(e) => setDriverA(e.target.value)} className="bg-[#111827] border border-[#374151] text-[11px] text-slate-200 rounded-lg px-2 py-1 outline-none mb-2 w-3/4">
                <option value="8842">Tài xế A (ID: 8842)</option>
                <option value="9102">Tài xế B (ID: 9102)</option>
              </select>
              <svg className="w-full h-full max-h-[140px]" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
                <polygon points="50,15 85,50 50,85 15,50" fill="none" stroke="#334155" strokeWidth="1" />
                <polygon points="50,25 75,50 50,75 25,50" fill="none" stroke="#334155" strokeWidth="0.5" />
                <polygon points="50,20 80,45 50,70 30,55" fill="#1e3a8a" fillOpacity="0.7" stroke="#3b82f6" strokeWidth="1.5" />
                <text x="50" y="10" textAnchor="middle" fill="#94a3b8" fontSize="6">PERCLOS</text>
                <text x="90" y="52" textAnchor="start" fill="#94a3b8" fontSize="6">Speeding</text>
                <text x="50" y="93" textAnchor="middle" fill="#94a3b8" fontSize="6">Braking</text>
                <text x="10" y="52" textAnchor="end" fill="#94a3b8" fontSize="6">Lane Depart</text>
              </svg>
            </div>
            {/* Driver B */}
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 flex flex-col items-center justify-center">
              <select value={driverB} onChange={(e) => setDriverB(e.target.value)} className="bg-[#111827] border border-[#374151] text-[11px] text-slate-200 rounded-lg px-2 py-1 outline-none mb-2 w-3/4">
                <option value="9102">Tài xế B (ID: 9102)</option>
                <option value="8842">Tài xế A (ID: 8842)</option>
              </select>
              <svg className="w-full h-full max-h-[140px]" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
                <polygon points="50,15 85,50 50,85 15,50" fill="none" stroke="#334155" strokeWidth="1" />
                <polygon points="50,25 75,50 50,75 25,50" fill="none" stroke="#334155" strokeWidth="0.5" />
                <polygon points="50,30 85,50 50,75 35,50" fill="#78350f" fillOpacity="0.8" stroke="#f59e0b" strokeWidth="1.5" />
                <text x="50" y="10" textAnchor="middle" fill="#94a3b8" fontSize="6">PERCLOS</text>
                <text x="90" y="52" textAnchor="start" fill="#94a3b8" fontSize="6">Speeding</text>
                <text x="50" y="93" textAnchor="middle" fill="#94a3b8" fontSize="6">Braking</text>
                <text x="10" y="52" textAnchor="end" fill="#94a3b8" fontSize="6">Lane Depart</text>
              </svg>
            </div>
          </div>
        </div>

        {/* ROW 2 */}
        {/* 2. Analytics: Top Violations (Col span 4) */}
        <div className="lg:col-span-4 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between shrink-0 mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-sky-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Top Violations
              </h2>
            </div>
          </div>
          <div className="flex-1 flex flex-col justify-around min-h-0">
            <div>
              <div className="flex justify-between text-[11px] font-bold text-slate-300 mb-1">
                <span>Distracted Driving</span>
                <span className="font-mono text-red-400">142</span>
              </div>
              <div className="w-full h-2 bg-[#1E293B] rounded-full overflow-hidden">
                <div className="h-full bg-red-500 rounded-full" style={{ width: '85%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[11px] font-bold text-slate-300 mb-1">
                <span>Speeding</span>
                <span className="font-mono text-orange-400">98</span>
              </div>
              <div className="w-full h-2 bg-[#1E293B] rounded-full overflow-hidden">
                <div className="h-full bg-orange-500 rounded-full" style={{ width: '60%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[11px] font-bold text-slate-300 mb-1">
                <span>Harsh Braking</span>
                <span className="font-mono text-amber-400">65</span>
              </div>
              <div className="w-full h-2 bg-[#1E293B] rounded-full overflow-hidden">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: '42%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[11px] font-bold text-slate-300 mb-1">
                <span>Lane Departure</span>
                <span className="font-mono text-slate-400">41</span>
              </div>
              <div className="w-full h-2 bg-[#1E293B] rounded-full overflow-hidden">
                <div className="h-full bg-slate-400 rounded-full" style={{ width: '28%' }} />
              </div>
            </div>
          </div>
        </div>

        {/* 4. Operational Behavior & Cost Impact (Col span 8) */}
        <div className="lg:col-span-8 bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 flex flex-col">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 shrink-0 mb-3">
            📊 Operational Behavior &amp; Cost Impact
          </h2>
          <div className="flex-1 grid grid-cols-4 gap-3 min-h-0">
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 flex flex-col justify-center">
              <span className="text-[9px] text-slate-400 uppercase font-bold block">Hard Braking</span>
              <div className="text-xl font-black text-amber-400 my-0.5 font-mono">24</div>
              <span className="text-[9px] text-red-400 font-semibold">+12% vs LW</span>
            </div>
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 flex flex-col justify-center">
              <span className="text-[9px] text-slate-400 uppercase font-bold block">Harsh Accel.</span>
              <div className="text-xl font-black text-white my-0.5 font-mono">18</div>
              <span className="text-[9px] text-emerald-400 font-semibold">-5% vs LW</span>
            </div>
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 flex flex-col justify-center">
              <span className="text-[9px] text-slate-400 uppercase font-bold block">Idle Time</span>
              <div className="text-xl font-black text-white my-0.5 font-mono">4.2h</div>
              <span className="text-[9px] text-slate-400 font-semibold">Stable</span>
            </div>
            <div className="bg-[#0F172A] border border-amber-900/40 rounded-xl p-3 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-1 text-[10px] text-amber-300 font-bold">
                  <DollarSign className="w-3 h-3 text-amber-400" />
                  <span>Cost Impact</span>
                </div>
                <div className="text-lg font-black text-white mt-1 font-mono">
                  $1,240.00
                </div>
                <p className="text-[9px] text-slate-300 mt-1 leading-tight line-clamp-3">
                  Aggressive driving is increasing fuel consumption by 8.4% & brake wear by 15%.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Floating Copilot Button */}
      <button
        onClick={onOpenCopilot}
        className="fixed bottom-6 right-6 z-30 p-3.5 bg-sky-600 hover:bg-sky-500 rounded-full text-white shadow-xl flex items-center justify-center transition-all"
        title="Open AI Copilot"
      >
        <Sparkles className="w-5 h-5 text-amber-200" />
      </button>
    </div>
  );
};
