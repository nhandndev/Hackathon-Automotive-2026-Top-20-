import React, { useEffect, useRef, useState } from 'react';
import { DecisionAlert, LiveTripSession, ViewMode, TripData } from './types';
import { btcTripData } from './data/btcTripData';
import { sessionToTrip } from './data/liveTripData';
import { Header } from './components/Header';
import { SidebarNav } from './components/SidebarNav';
import { FleetMapView } from './components/FleetMapView';
import { VehicleLiveView } from './components/VehicleLiveView';
import { TripDetailView } from './components/TripDetailView';
import { PerformanceInsightsView } from './components/PerformanceInsightsView';
import { DriverRankingView } from './components/DriverRankingView';
import { DriverRankingAnalysisPage } from './components/DriverRankingAnalysisPage';
import { CopilotFleetReportPage } from './components/CopilotFleetReportPage';
import { AICopilotDrawer } from './components/AICopilotDrawer';
import { InterventionModal } from './components/InterventionModal';

/** Shown when no backend / saved trips are available yet. */
const WaitingForData = () => (
  <div className="flex-1 flex flex-col items-center justify-center gap-4 bg-[#070A12] text-slate-400 p-8">
    <div className="w-10 h-10 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
    <p className="text-sm font-mono text-slate-500">Đang chờ dữ liệu từ backend…</p>
    <p className="text-xs text-slate-600 max-w-xs text-center">
      Khởi động AI pipeline và kết nối backend để dữ liệu chuyến đi xuất hiện ở đây.
    </p>
  </div>
);

export default function App() {
  const urlParams = new URLSearchParams(window.location.search);
  const standaloneView = urlParams.get('view');
  const rankingTripId = urlParams.get('trip_id');
  const copilotReportType = urlParams.get('type');
  const copilotReportTripIds = urlParams.get('trip_ids');

  const initialView = (
    standaloneView === 'TRIP_DETAIL' ||
    standaloneView === 'MAP' ||
    standaloneView === 'VEHICLE_LIVE' ||
    standaloneView === 'INSIGHTS' ||
    standaloneView === 'RANKING'
  ) ? (standaloneView as ViewMode) : 'MAP';

  const [currentView, setCurrentView] = useState<ViewMode>(initialView);
  const [vehicles, setVehicles] = useState<TripData[]>(btcTripData);
  // selectedVehicle is null until the first backend/saved-trip data arrives.
  const [selectedVehicle, setSelectedVehicle] = useState<TripData | null>(null);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isInterventionOpen, setIsInterventionOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [liveAlerts, setLiveAlerts] = useState<DecisionAlert[]>([]);
  const [alertsConnected, setAlertsConnected] = useState(false);
  const [savedTripsLoaded, setSavedTripsLoaded] = useState(false);
  const followRunningTrip = useRef(true);
  // Ref: IDs of trips that were 'running' in the last poll tick — used to
  // detect the running→completed transition and trigger an auto-save.
  const runningTripIdsRef = useRef<Set<string>>(new Set());
  // Ref: historical trips loaded from server disk (data/saved_trips/).
  const savedTripsCacheRef = useRef<TripData[]>([]);

  useEffect(() => {
    const alertsHttp = import.meta.env.VITE_ALERTS_HTTP_URL || 'http://127.0.0.1:8000/api/v1/alerts';
    const endpoint = import.meta.env.VITE_ALERTS_WS_URL || 'ws://127.0.0.1:8000/api/v1/alerts/live';

    const upsert = (incoming: DecisionAlert[]) => {
      setLiveAlerts((current) => {
        const merged = [...incoming, ...current];
        return merged.filter(
          (item, index) => merged.findIndex(
            (candidate) => candidate.event_id === item.event_id,
          ) === index,
        ).slice(0, 1000);
      });
    };

    const loadRecent = async () => {
      try {
        const response = await fetch(`${alertsHttp}/recent?limit=1000`);
        if (!response.ok) return;
        const payload = await response.json() as { items?: DecisionAlert[] };
        upsert([...(payload.items ?? [])].reverse());
      } catch {
        // WebSocket reconnect/reload can recover later.
      }
    };

    // ── Trip persistence helpers ────────────────────────────────────────────

    /** Persist a completed TripData to disk via the Express server. */
    const saveTripToServer = async (tripData: TripData) => {
      try {
        const resp = await fetch('/api/trips/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(tripData),
        });
        if (resp.ok) {
          console.info(`[trip-persist] Saved ${tripData.trip_id} to disk.`);
          savedTripsCacheRef.current = [
            ...savedTripsCacheRef.current.filter(t => t.trip_id !== tripData.trip_id),
            tripData,
          ];
        }
      } catch (err) {
        console.warn('[trip-persist] Auto-save failed:', err);
      }
    };

    /** Load all previously persisted trips from disk on startup. */
    const loadSavedTrips = async () => {
      try {
        const listResp = await fetch('/api/trips/saved');
        if (!listResp.ok) return;
        const { trips } = await listResp.json() as { trips: string[] };
        const loaded: TripData[] = [];
        await Promise.all(trips.map(async (tripId) => {
          try {
            const r = await fetch(`/api/trips/saved/${encodeURIComponent(tripId)}`);
            if (r.ok) loaded.push(await r.json() as TripData);
          } catch { /* skip corrupt file */ }
        }));
        savedTripsCacheRef.current = loaded;
        if (loaded.length > 0) {
          setVehicles((prev) => {
            const existingIds = new Set(prev.map(v => v.trip_id));
            const newOnes = loaded.filter(t => !existingIds.has(t.trip_id));
            return newOnes.length > 0 ? [...prev, ...newOnes] : prev;
          });
          // Select the first saved trip if nothing is selected yet
          setSelectedVehicle((prev) => prev ?? loaded[0]);
        }
      } catch (err) {
        console.warn('[trip-persist] Could not load saved trips:', err);
      } finally {
        setSavedTripsLoaded(true);
      }
    };

    const loadTrips = async () => {
      try {
        const response = await fetch(`${alertsHttp}/trips`);
        if (!response.ok) return;
        const payload = await response.json() as { items?: LiveTripSession[] };
        const liveSessions = payload.items ?? [];
        const dynamicTrips = liveSessions.map(sessionToTrip);
        if (!dynamicTrips.length) return;

        // ── Detect running → completed transition and auto-save ─────────────
        for (const session of liveSessions) {
          if (
            session.status === 'completed'
            && runningTripIdsRef.current.has(session.trip_id)
          ) {
            const completedTrip = dynamicTrips.find(t => t.trip_id === session.trip_id);
            if (completedTrip) void saveTripToServer(completedTrip);
          }
        }
        runningTripIdsRef.current = new Set(
          liveSessions.filter(s => s.status === 'running').map(s => s.trip_id),
        );

        // ── Merge: live trips take priority; saved trips fill the rest ───────
        const liveTripIds = new Set(dynamicTrips.map(t => t.trip_id));
        const savedOnlyTrips = savedTripsCacheRef.current.filter(t => !liveTripIds.has(t.trip_id));
        const mergedTrips = [...dynamicTrips, ...savedOnlyTrips];

        setVehicles(mergedTrips);
        setSelectedVehicle((current) => (
          (followRunningTrip.current
            ? mergedTrips.find((trip) => trip.runtime_status === 'running')
            : undefined)
          ?? mergedTrips.find((trip) => trip.trip_id === current?.trip_id)
          ?? mergedTrips[0]
        ));
      } catch {
        // Keep the last valid dashboard state while Backend is unavailable.
      }
    };

    void loadRecent();
    void loadSavedTrips(); // load persisted trips before first live poll
    void loadTrips();
    const tripTimer = window.setInterval(loadTrips, 1000);
    const socket = new WebSocket(endpoint);
    socket.onopen = () => setAlertsConnected(true);
    socket.onclose = () => setAlertsConnected(false);
    socket.onerror = () => setAlertsConnected(false);
    socket.onmessage = (message) => {
      try {
        const alert = JSON.parse(message.data) as DecisionAlert;
        upsert([alert]);
      } catch {
        // Invalid external messages are ignored; Backend owns validation.
      }
    };
    return () => {
      window.clearInterval(tripTimer);
      socket.close();
    };
  }, []);

  // Handle vehicle selection
  const handleSelectVehicle = (vehicle: TripData) => {
    followRunningTrip.current = false;
    setSelectedVehicle(vehicle);
  };

  const handleViewLiveFeed = (vehicle?: TripData) => {
    if (vehicle) setSelectedVehicle(vehicle);
    setCurrentView('VEHICLE_LIVE');
  };

  const handleViewTripDetail = (vehicle?: TripData) => {
    if (vehicle) setSelectedVehicle(vehicle);
    setCurrentView('TRIP_DETAIL');
  };

  const handleOpenIntervention = (vehicle?: TripData) => {
    if (vehicle) setSelectedVehicle(vehicle);
    setIsInterventionOpen(true);
  };

  const handleClearSavedTrips = async () => {
    try {
      const resp = await fetch('/api/trips/saved', { method: 'DELETE' });
      if (!resp.ok) {
        throw new Error(`DELETE /api/trips/saved returned ${resp.status}`);
      }
      savedTripsCacheRef.current = [];
      const liveOnly = vehicles.filter((trip) => trip.runtime_status !== 'completed');
      setVehicles(liveOnly);
      setSelectedVehicle((selected) => (
        selected && liveOnly.some((trip) => trip.trip_id === selected.trip_id)
          ? selected
          : liveOnly[0] ?? null
      ));
      followRunningTrip.current = true;
      console.info('[trip-clear] Cleared saved demo trips.');
    } catch (err) {
      console.warn('[trip-clear] Could not clear saved trips:', err);
      window.alert('Không xoá được saved trips. Kiểm tra Fleet Dashboard server.');
    }
  };

  if (standaloneView === 'ranking-analysis') {
    return (
      <DriverRankingAnalysisPage
        vehicles={vehicles}
        tripId={rankingTripId}
      />
    );
  }

  if (standaloneView === 'copilot-report') {
    return (
      <CopilotFleetReportPage
        vehicles={vehicles}
        reportType={copilotReportType}
        tripIds={copilotReportTripIds}
        dataReady={savedTripsLoaded}
      />
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-[#070A12] font-sans antialiased overflow-hidden select-none">
      {/* Top Main Navigation Header */}
      <Header
        currentView={currentView}
        setCurrentView={setCurrentView}
        selectedVehicle={selectedVehicle}
        onBackToMap={() => setCurrentView('MAP')}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />

      {/* Center Main Application Stage */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Vertical Navigation Sidebar */}
        <SidebarNav
          currentView={currentView}
          setCurrentView={setCurrentView}
          onOpenCopilot={() => setIsCopilotOpen(true)}
        />

        {/* View Content Switching */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {currentView === 'MAP' && (
            <FleetMapView
              vehicles={vehicles}
              selectedVehicle={selectedVehicle}
              onSelectVehicle={handleSelectVehicle}
              onViewLiveFeed={handleViewLiveFeed}
              onViewTripDetail={handleViewTripDetail}
              onIntervene={handleOpenIntervention}
              onOpenCopilot={() => setIsCopilotOpen(true)}
              onClearSavedTrips={handleClearSavedTrips}
            />
          )}

          {currentView === 'VEHICLE_LIVE' && (
            selectedVehicle
              ? <VehicleLiveView
                  vehicle={selectedVehicle}
                  liveAlerts={liveAlerts}
                  alertsConnected={alertsConnected}
                  onIntervene={() => handleOpenIntervention(selectedVehicle)}
                />
              : <WaitingForData />
          )}

          {currentView === 'TRIP_DETAIL' && (
            selectedVehicle
              ? <TripDetailView
                  vehicle={selectedVehicle}
                  liveAlerts={liveAlerts}
                  alertsConnected={alertsConnected}
                  onViewLiveFeed={() => handleViewLiveFeed(selectedVehicle)}
                  onOpenCopilot={() => setIsCopilotOpen(true)}
                />
              : <WaitingForData />
          )}

          {currentView === 'INSIGHTS' && (
            selectedVehicle
              ? <PerformanceInsightsView
                  vehicle={selectedVehicle}
                  liveAlerts={liveAlerts}
                  onOpenCopilot={() => setIsCopilotOpen(true)}
                />
              : <WaitingForData />
          )}

          {currentView === 'RANKING' && (
            <DriverRankingView
              vehicles={vehicles}
              selectedVehicle={selectedVehicle}
              liveAlerts={liveAlerts}
              onSelectVehicle={handleSelectVehicle}
              onViewTripDetail={handleViewTripDetail}
              onOpenCopilot={() => setIsCopilotOpen(true)}
            />
          )}

          {/* Settings or fallback placeholder */}
          {currentView === 'SETTINGS' && (
            <div className="flex-1 bg-[#070A12] p-8 text-white flex flex-col items-center justify-center space-y-4">
              <h2 className="text-xl font-extrabold text-slate-200">System Settings &amp; AI Calibration</h2>
              <p className="text-xs text-slate-400 max-w-md text-center">
                Cấu hình ngưỡng phát hiện vi ngủ (PERCLOS), độ nhạy cảm biến phanh gấp, cài đặt đồng bộ camera cabin dual-cam và API trợ lý Copilot.
              </p>
              <button
                onClick={() => setCurrentView('MAP')}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 rounded-lg text-xs font-bold transition-colors"
              >
                Quay lại Bản đồ Đội xe
              </button>
            </div>
          )}
        </main>
      </div>

      {/* Fleet AI Copilot Slide-over Drawer */}
      <AICopilotDrawer
        isOpen={isCopilotOpen}
        vehicles={vehicles}
        onClose={() => setIsCopilotOpen(false)}
        onNavigateToTrip={() => {
          setIsCopilotOpen(false);
          setCurrentView('TRIP_DETAIL');
        }}
        onSendBreakSchedule={() => {
          if (selectedVehicle) handleOpenIntervention(selectedVehicle);
        }}
      />

      {/* Emergency Intervention Dialog Modal */}
      {selectedVehicle && (
        <InterventionModal
          vehicle={selectedVehicle}
          isOpen={isInterventionOpen}
          onClose={() => setIsInterventionOpen(false)}
        />
      )}
    </div>
  );
}
