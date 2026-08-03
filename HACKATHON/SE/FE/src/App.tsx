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

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('MAP');
  const [vehicles, setVehicles] = useState<TripData[]>(btcTripData);
  const [selectedVehicle, setSelectedVehicle] = useState<TripData>(btcTripData[0]);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isInterventionOpen, setIsInterventionOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [liveAlerts, setLiveAlerts] = useState<DecisionAlert[]>([]);
  const [alertsConnected, setAlertsConnected] = useState(false);
  const followRunningTrip = useRef(true);
  const urlParams = new URLSearchParams(window.location.search);
  const standaloneView = urlParams.get('view');
  const rankingTripId = urlParams.get('trip_id');
  const copilotReportType = urlParams.get('type');
  const copilotReportTripIds = urlParams.get('trip_ids');

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
    const loadTrips = async () => {
      try {
        const response = await fetch(`${alertsHttp}/trips`);
        if (!response.ok) return;
        const payload = await response.json() as { items?: LiveTripSession[] };
        const dynamicTrips = (payload.items ?? []).map(sessionToTrip);
        if (!dynamicTrips.length) return;
        setVehicles(dynamicTrips);
        setSelectedVehicle((current) => (
          (followRunningTrip.current
            ? dynamicTrips.find((trip) => trip.runtime_status === 'running')
            : undefined)
          ?? dynamicTrips.find((trip) => trip.trip_id === current?.trip_id)
          ?? dynamicTrips[0]
        ));
      } catch {
        // Keep the last valid dashboard state while Backend is unavailable.
      }
    };
    void loadRecent();
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
            />
          )}

          {currentView === 'VEHICLE_LIVE' && (
            <VehicleLiveView
              vehicle={selectedVehicle}
              liveAlerts={liveAlerts}
              alertsConnected={alertsConnected}
              onIntervene={() => handleOpenIntervention(selectedVehicle)}
            />
          )}

          {currentView === 'TRIP_DETAIL' && (
            <TripDetailView
              vehicle={selectedVehicle}
              liveAlerts={liveAlerts}
              alertsConnected={alertsConnected}
              onViewLiveFeed={() => handleViewLiveFeed(selectedVehicle)}
              onOpenCopilot={() => setIsCopilotOpen(true)}
            />
          )}

          {currentView === 'INSIGHTS' && (
            <PerformanceInsightsView
              vehicle={selectedVehicle}
              liveAlerts={liveAlerts}
              onOpenCopilot={() => setIsCopilotOpen(true)}
            />
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
          handleOpenIntervention(selectedVehicle);
        }}
      />

      {/* Emergency Intervention Dialog Modal */}
      <InterventionModal
        vehicle={selectedVehicle}
        isOpen={isInterventionOpen}
        onClose={() => setIsInterventionOpen(false)}
      />
    </div>
  );
}
