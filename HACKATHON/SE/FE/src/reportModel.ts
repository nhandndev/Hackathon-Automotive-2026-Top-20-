import { TripData } from './types';
import { buildRankingRows } from './components/DriverRankingView';

export type ReportMode = 'safety_detail' | 'safety_overview' | 'maintenance_detail' | 'maintenance_overview';
export type MaintenancePriority = 'NORMAL' | 'WATCH' | 'INSPECT';

export interface CanonicalSafetyEvent {
  timestampSec: number;
  timeLabel: string;
  type: string;
  severity: 'safe' | 'warning' | 'danger';
  detail: string;
}

export interface VehicleReportModel {
  tripId: string;
  driverName: string;
  score: number;
  riskLevel: 'SAFE' | 'WATCH' | 'AT_RISK' | 'CRITICAL';
  rank: number;
  avgRisk: number;
  maxRisk: number;
  distractedPct: number;
  fatigueEvents: number;
  speedingPct: number;
  tailgatingPct: number;
  nearMissCount: number;
  harshBrakeCount: number;
  rawCriticalRiskFrames: number;
  events: CanonicalSafetyEvent[];
  eventSummary: { safe: number; warning: number; danger: number; total: number };
  safetyAction: 'COACHING_24H' | 'WARNING' | 'SAFE';
  maintenance: {
    brakeStress: number;
    tireStress: number;
    priority: MaintenancePriority;
    dtcCode: string;
    estimatedCostVnd: number;
    estimatedDowntime: string;
    workOrderStatus: 'Recommended - not created';
  };
  trip: TripData;
}

const finite = (value: unknown, fallback = 0) =>
  typeof value === 'number' && Number.isFinite(value) ? value : fallback;

const pct = (count: number, total: number) => (total > 0 ? (count / total) * 100 : 0);

export const resolveDriverName = (trip: TripData) =>
  trip.driver_summary?.subject_id && trip.driver_summary.subject_id !== 'runtime'
    ? trip.driver_summary.subject_id
    : trip.trip_id;

export const extractCanonicalSafetyEvents = (trip: TripData): CanonicalSafetyEvent[] => {
  const events: CanonicalSafetyEvent[] = [];
  const lastEventTimeByType: Record<string, number> = {};
  let previousState: string | undefined;

  for (const frame of trip.frames ?? []) {
    const state = frame.driver?.state ?? 'alert';
    const ts = finite(frame.timestamp);
    const risk = finite(frame.risk?.final_risk_score);
    const isLowTtc = Number.isFinite(frame.min_ttc) && frame.min_ttc > 0 && frame.min_ttc <= 2.5;
    const behavior = frame.behavior_flags;
    const stateChanged = previousState !== undefined && previousState !== state;

    let type = '';
    if (stateChanged) type = `Chuyển trạng thái: ${previousState} -> ${state}`;
    else if (behavior?.harsh_brake) type = 'Phanh gấp (Harsh brake)';
    else if (behavior?.tailgating) type = 'Bám đuôi gần (Tailgating)';
    else if (behavior?.speeding) type = 'Vượt quá tốc độ (Speeding)';
    else if (state !== 'alert') type = `Tài xế ${state}`;
    else if (isLowTtc) type = 'TTC thấp / near miss';
    else if (risk >= 50) type = 'Risk score cao';

    if (type) {
      const lastTs = lastEventTimeByType[type] ?? -999;
      if (ts - lastTs >= 3) {
        lastEventTimeByType[type] = ts;
        const severity: CanonicalSafetyEvent['severity'] =
          risk >= 70 || state === 'microsleep' || isLowTtc ? 'danger'
            : risk >= 40 || state === 'drowsy' || state === 'yawning' || state === 'distracted' || behavior?.harsh_brake || behavior?.tailgating || behavior?.speeding ? 'warning'
              : 'safe';
        events.push({
          timestampSec: ts,
          timeLabel: `${ts.toFixed(1)}s`,
          type,
          severity,
          detail: `risk=${risk.toFixed(1)}, ttc=${Number.isFinite(frame.min_ttc) ? `${frame.min_ttc.toFixed(2)}s` : 'Infinity'}, alertness=${finite(frame.driver?.alertness_score).toFixed(2)}`,
        });
      }
    }
    previousState = state;
  }

  if (events.length === 0 && (trip.frames?.length ?? 0) > 0) {
    return [{
      timestampSec: 0,
      timeLabel: '0.0s',
      type: 'Không ghi nhận cảnh báo',
      severity: 'safe',
      detail: 'Trip không có sự kiện rủi ro sau debounce.',
    }];
  }

  return events;
};

const summarizeEvents = (events: CanonicalSafetyEvent[]) => ({
  safe: events.filter((event) => event.severity === 'safe').length,
  warning: events.filter((event) => event.severity === 'warning').length,
  danger: events.filter((event) => event.severity === 'danger').length,
  total: events.length,
});

const getRealDtcCode = (trip: TripData) => {
  const source = (trip as any).obd?.dtc_codes ?? (trip as any).vehicle_health?.dtc_codes ?? (trip.trip_aggregate as any)?.dtc_codes;
  return Array.isArray(source) && source.length > 0 ? source.join(', ') : 'N/A';
};

const buildMaintenance = (trip: TripData, events: CanonicalSafetyEvent[], score: number, harshBrakeCount: number, speedingPct: number, maxRisk: number) => {
  const brakeEventCount = harshBrakeCount;
  const tireEventCount = events.filter((event) => event.type.toLowerCase().includes('speed') || event.type.toLowerCase().includes('tốc độ') || event.type.toLowerCase().includes('tailgating')).length;
  const brakeStress = Math.min(100, Math.round(15 + brakeEventCount * 3.5 + Math.max(0, maxRisk - 60) * 0.2));
  const tireStress = Math.min(100, Math.round(10 + speedingPct * 0.4 + tireEventCount * 2));
  const dtcCode = getRealDtcCode(trip);
  const priority: MaintenancePriority =
    dtcCode !== 'N/A' || brakeStress >= 75 || tireStress >= 75 || score < 45 ? 'INSPECT'
      : brakeStress >= 50 || tireStress >= 50 || score < 65 ? 'WATCH'
        : 'NORMAL';
  const estimatedCostVnd = priority === 'INSPECT' ? 2500000 + brakeEventCount * 250000 : priority === 'WATCH' ? 1500000 + brakeEventCount * 150000 : 900000;
  return {
    brakeStress,
    tireStress,
    priority,
    dtcCode,
    estimatedCostVnd,
    estimatedDowntime: priority === 'INSPECT' ? '1.0 ngày (dự tính)' : priority === 'WATCH' ? '0.5 ngày (dự tính)' : '0.5 ngày hoặc gộp lịch định kỳ (dự tính)',
    workOrderStatus: 'Recommended - not created' as const,
  };
};

export const buildVehicleReportModels = (vehicles: TripData[], selectedTrips: TripData[]) => {
  const selectedSet = new Set(selectedTrips.map((trip) => trip.trip_id));
  const rankingRows = buildRankingRows(vehicles).filter((row) => selectedSet.has(row.trip_id));

  return rankingRows.map<VehicleReportModel>((row) => {
    const events = extractCanonicalSafetyEvents(row.trip);
    const eventSummary = summarizeEvents(events);
    const rawCriticalRiskFrames = (row.trip.frames ?? []).filter((frame) => finite(frame.risk?.final_risk_score) >= 80).length;
    const safetyAction: VehicleReportModel['safetyAction'] =
      row.score < 60 || row.fatigueEvents > 0 || row.distractedPct > 30 ? 'COACHING_24H'
        : row.score < 80 || row.distractedPct > 15 || row.nearMissCount > 0 ? 'WARNING'
          : 'SAFE';

    return {
      tripId: row.trip_id,
      driverName: resolveDriverName(row.trip),
      score: row.score,
      riskLevel: row.riskLevel,
      rank: row.rank,
      avgRisk: row.avgRisk,
      maxRisk: row.maxRisk,
      distractedPct: row.distractedPct,
      fatigueEvents: row.fatigueEvents,
      speedingPct: row.speedingPct,
      tailgatingPct: row.tailgatingPct,
      nearMissCount: row.nearMissCount,
      harshBrakeCount: row.harshEvents,
      rawCriticalRiskFrames,
      events,
      eventSummary,
      safetyAction,
      maintenance: buildMaintenance(row.trip, events, row.score, row.harshEvents, row.speedingPct, row.maxRisk),
      trip: row.trip,
    };
  });
};

export const inferReportMode = (reportType: string | null, modelCount: number): ReportMode =>
  reportType === 'maintenance'
    ? modelCount === 1 ? 'maintenance_detail' : 'maintenance_overview'
    : modelCount === 1 ? 'safety_detail' : 'safety_overview';

export const buildCopilotInput = (models: VehicleReportModel[], reportMode: ReportMode) => ({
  request_id: `report-${Date.now()}`,
  policy_version: 'report-canonical-v1',
  report_mode: reportMode,
  trips: models.map((model) => ({
    tripId: model.tripId,
    driverName: model.driverName,
    rank: model.rank,
    safety: {
      score: model.score,
      riskLevel: model.riskLevel,
      avgRisk: model.avgRisk,
      maxRisk: model.maxRisk,
      highRiskFrames: model.rawCriticalRiskFrames,
      distractedPct: model.distractedPct,
      fatigueEvents: model.fatigueEvents,
      speedingPct: model.speedingPct,
      tailgatingPct: model.tailgatingPct,
      nearMissCount: model.nearMissCount,
      harshBrakeCount: model.harshBrakeCount,
      safetyAction: model.safetyAction,
    },
    eventSummary: model.eventSummary,
    events: model.events,
    maintenance: model.maintenance,
  })),
});
