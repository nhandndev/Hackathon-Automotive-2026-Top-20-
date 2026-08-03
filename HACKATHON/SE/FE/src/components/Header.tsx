import React from 'react';
import { Bell, User, Radio, ArrowLeft, Search } from 'lucide-react';
import { ViewMode, TripData } from '../types';

interface HeaderProps {
  currentView: ViewMode;
  setCurrentView: (view: ViewMode) => void;
  selectedVehicle?: TripData | null;
  onBackToMap?: () => void;
  onOpenCopilot: () => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  setCurrentView,
  selectedVehicle,
  onBackToMap,
  onOpenCopilot,
  searchQuery,
  setSearchQuery,
}) => {
  return (
    <header className="h-16 bg-[#0B0F19] border-b border-[#1E293B] px-4 md:px-6 flex items-center justify-between text-white select-none z-30">
      {/* Left side title / back button */}
      <div className="flex items-center gap-3">
        {currentView === 'VEHICLE_LIVE' ? (
          <>
            <button
              id="btn-back-to-map"
              onClick={onBackToMap || (() => setCurrentView('MAP'))}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-[#1E293B] hover:bg-[#334155] rounded-md transition-colors text-slate-200"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Map</span>
            </button>
            <div className="h-5 w-[1px] bg-[#334155]" />
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-extrabold tracking-wider text-white">
                {selectedVehicle ? selectedVehicle.trip_id : 'NO TRIP'}
              </h1>
              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-950/80 border border-red-500/40 text-[11px] font-semibold text-red-400 animate-pulse">
                <Radio className="w-3 h-3 text-red-500" />
                LIVE
              </span>
            </div>
          </>
        ) : (
          <div className="flex items-center gap-3">
            <h1
              className="text-xl font-bold tracking-tight text-white cursor-pointer flex items-center gap-2"
              onClick={() => setCurrentView('MAP')}
            >
              <span className="text-sky-400">Vision</span> Command
            </h1>
            <span className="text-xs text-slate-400 hidden sm:inline-block px-2 py-0.5 rounded bg-[#1E293B]/60 font-mono border border-slate-700/50">
              Active Ops
            </span>
          </div>
        )}
      </div>

      {/* Middle search bar for Map and Insights views */}
      {currentView !== 'VEHICLE_LIVE' && (
        <div className="hidden md:flex items-center max-w-md w-full mx-4">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              id="header-search-input"
              type="text"
              placeholder={
                currentView === 'INSIGHTS'
                  ? 'Hỏi Trợ lý AI về đoàn xe của bạn...'
                  : 'Search vehicles, drivers...'
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && searchQuery.trim()) {
                  onOpenCopilot();
                }
              }}
              className="w-full bg-[#111827] border border-[#1F2937] hover:border-[#374151] focus:border-sky-500 text-sm text-slate-200 placeholder-slate-400 rounded-lg pl-9 pr-4 py-1.5 outline-none transition-all"
            />
          </div>
        </div>
      )}

      {/* Right side actions */}
      <div className="flex items-center gap-3">
        {/* Quick view selector buttons for previewing all screenshots */}
        <div className="hidden xl:flex items-center gap-1 bg-[#111827] p-1 rounded-lg border border-[#1F2937] text-xs">
          <button
            id="nav-tab-map"
            onClick={() => setCurrentView('MAP')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              currentView === 'MAP'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            1. Map
          </button>
          <button
            id="nav-tab-vehicle-live"
            onClick={() => setCurrentView('VEHICLE_LIVE')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              currentView === 'VEHICLE_LIVE'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            2. Live Cam
          </button>
          <button
            id="nav-tab-trip-detail"
            onClick={() => setCurrentView('TRIP_DETAIL')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              currentView === 'TRIP_DETAIL'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            3. Trip Detail
          </button>
          <button
            id="nav-tab-insights"
            onClick={() => setCurrentView('INSIGHTS')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              currentView === 'INSIGHTS'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            4. Insights
          </button>
          <button
            id="nav-tab-ranking"
            onClick={() => setCurrentView('RANKING')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all ${
              currentView === 'RANKING'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            5. Ranking
          </button>
        </div>

        {/* Notifications Icon */}
        <button
          id="btn-header-notifications"
          className="relative p-2 text-slate-300 hover:text-white bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] rounded-lg transition-colors"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#1E293B]">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    </header>
  );
};
