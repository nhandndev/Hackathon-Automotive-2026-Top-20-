import React, { useState } from 'react';
import { ViewMode, TripData } from './types';
import { mockTripData } from './data/mockData';
import { Header } from './components/Header';
import { SidebarNav } from './components/SidebarNav';
import { FleetMapView } from './components/FleetMapView';
import { VehicleLiveView } from './components/VehicleLiveView';
import { TripDetailView } from './components/TripDetailView';
import { PerformanceInsightsView } from './components/PerformanceInsightsView';
import { AICopilotDrawer } from './components/AICopilotDrawer';
import { InterventionModal } from './components/InterventionModal';

export default function App() {
  const [currentView, setCurrentView] = useState<ViewMode>('MAP');
  const [vehicles] = useState<TripData[]>(mockTripData);
  const [selectedVehicle, setSelectedVehicle] = useState<TripData>(mockTripData[0]); // VH-04 default
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isInterventionOpen, setIsInterventionOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Handle vehicle selection
  const handleSelectVehicle = (vehicle: TripData) => {
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
              vehicle={selectedVehicle || vehicles[1]} // Default VH-01 if none
              onIntervene={() => handleOpenIntervention(selectedVehicle)}
            />
          )}

          {currentView === 'TRIP_DETAIL' && (
            <TripDetailView
              vehicle={selectedVehicle}
              onViewLiveFeed={() => handleViewLiveFeed(selectedVehicle)}
              onOpenCopilot={() => setIsCopilotOpen(true)}
            />
          )}

          {currentView === 'INSIGHTS' && (
            <PerformanceInsightsView
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
