import React from 'react';
import { Map, BarChart3, AlertTriangle, Settings, Sparkles, User, Trophy, Route } from 'lucide-react';
import { ViewMode } from '../types';

interface SidebarNavProps {
  currentView: ViewMode;
  setCurrentView: (view: ViewMode) => void;
  onOpenCopilot: () => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  currentView,
  setCurrentView,
  onOpenCopilot,
}) => {
  const navItems = [
    { id: 'MAP', label: 'MAP', icon: Map, view: 'MAP' as ViewMode },
    { id: 'ALERTS', label: 'ALERTS', icon: AlertTriangle, view: 'VEHICLE_LIVE' as ViewMode },
    { id: 'TRIP_DETAIL', label: 'TRIP DETAIL', icon: Route, view: 'TRIP_DETAIL' as ViewMode },
    { id: 'INSIGHTS', label: 'INSIGHTS', icon: BarChart3, view: 'INSIGHTS' as ViewMode },
    { id: 'RANKING', label: 'RANKING', icon: Trophy, view: 'RANKING' as ViewMode },
    { id: 'SETTINGS', label: 'SETTINGS', icon: Settings, view: 'SETTINGS' as ViewMode },
  ];

  return (
    <aside className="w-16 md:w-20 bg-[#070A12] border-r border-[#1E293B] flex flex-col items-center justify-between py-4 z-20 select-none">
      {/* Top Logo / Avatar */}
      <div className="flex flex-col items-center gap-6 w-full">
        <div className="w-9 h-9 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center overflow-hidden shadow-inner">
          <User className="h-5 w-5 text-slate-300" aria-label="User" />
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-col items-center gap-4 w-full">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.view;
            return (
              <button
                key={item.id}
                id={`sidebar-nav-${item.id.toLowerCase()}`}
                onClick={() => setCurrentView(item.view)}
                className={`w-full flex flex-col items-center justify-center py-2.5 px-1 transition-all group relative ${
                  isActive
                    ? 'text-sky-400 bg-slate-900/80 border-l-2 border-sky-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                }`}
                title={item.label}
              >
                <Icon className={`w-5 h-5 transition-transform group-hover:scale-110 ${isActive ? 'text-sky-400' : ''}`} />
                <span className="text-[9px] font-semibold mt-1 tracking-wider uppercase opacity-80">
                  {item.label}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom AI Copilot Quick Launcher & Admin profile */}
      <div className="flex flex-col items-center gap-3 w-full px-2">
        <button
          id="btn-sidebar-copilot"
          onClick={onOpenCopilot}
          className="w-full py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white rounded-lg flex flex-col items-center justify-center gap-1 shadow-lg shadow-sky-900/30 transition-all hover:scale-105"
          title="Fleet AI Copilot"
        >
          <Sparkles className="w-4 h-4 text-amber-300 animate-spin" style={{ animationDuration: '4s' }} />
          <span className="text-[9px] font-bold tracking-tight">AI Copilot</span>
        </button>

        <div className="text-[10px] text-slate-500 flex items-center gap-1 py-1">
          <User className="w-3 h-3 text-slate-400" />
          <span className="hidden md:inline">Admin</span>
        </div>
      </div>
    </aside>
  );
};
