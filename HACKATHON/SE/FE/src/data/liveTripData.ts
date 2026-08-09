import { Frame, LiveSnapshot, LiveTripSession, TripData, Weather } from '../types';

const emptyWeather: Weather = {
  cloudiness: 0,
  precipitation: 0,
  precipitation_deposits: 0,
  sun_altitude_angle: 0,
  sun_azimuth_angle: 0,
  fog_density: 0,
  fog_distance: 0,
  wind_intensity: 0,
  wetness: 0,
};

const toFrame = (snapshot: LiveSnapshot): Frame => ({
  frame_id: snapshot.frame_id,
  world_frame: snapshot.frame_id,
  timestamp: snapshot.trip_timestamp_ms / 1000,
  ego: {
    speed_kmh: snapshot.speed_kmh ?? 0,
    longitudinal_accel: snapshot.longitudinal_accel ?? 0,
    lateral_accel: snapshot.lateral_accel ?? 0,
    location: { x: 0, y: 0, z: 0 },
    rotation: { yaw: 0, pitch: 0, roll: 0 },
    geolocation: { lat: 0, lon: 0, alt: 0 },
  },
  targets: [],
  driver: {
    state: snapshot.driver_state ?? 'unknown',
    alertness_score: snapshot.alertness_score ?? 0,
    eye_state: snapshot.eye_state ?? 'unknown',
    head_pose: snapshot.head_pose ?? 'unknown',
    mouth_state: snapshot.mouth_state ?? 'unknown',
    nthu_subject_id: 'runtime',
  },
  events_active: [],
  // predicted_ttc_sec can be null (no vehicle ahead = infinite clearance)
  min_ttc: snapshot.predicted_ttc_sec != null ? snapshot.predicted_ttc_sec : Number.POSITIVE_INFINITY,
  headway_sec: snapshot.predicted_ttc_sec != null ? snapshot.predicted_ttc_sec : Number.POSITIVE_INFINITY,
  behavior_flags: {
    harsh_brake: snapshot.harsh_brake ?? false,
    harsh_accel: snapshot.harsh_accel ?? false,
    harsh_corner: snapshot.harsh_corner ?? false,
    speeding: snapshot.speeding ?? false,
    tailgating: snapshot.tailgating ?? false,
  },
  risk: {
    base_risk: snapshot.risk_score ?? 0,
    driver_factor: snapshot.driver_confidence ?? 1,
    // final_risk_score is required by DriverRankingView.buildRankingRows
    final_risk_score: snapshot.risk_score ?? 0,
  },
});

const episodeCount = (
  values: LiveSnapshot[],
  predicate: (snapshot: LiveSnapshot) => boolean,
) => values.reduce(
  (count, value, index) => count + (
    predicate(value) && (index === 0 || !predicate(values[index - 1])) ? 1 : 0
  ),
  0,
);

// Maximum frames retained per trip in the UI. Keeping this low avoids:
//  1. Math.max(...largeArray) → "Maximum call stack size exceeded"
//  2. buildRankingRows iterating 100 000+ frames → frozen main thread
//  3. Recharts rendering thousands of data points → blank / crashed chart
const MAX_UI_FRAMES = 2400;

const clamp = (value: number, min = 0, max = 100) => Math.min(Math.max(value, min), max);

const capSafeScoreByRisk = (score: number, maxRisk: number, averageRisk: number) => {
  let capped = score;
  if (maxRisk >= 95) capped = Math.min(capped, 20);
  else if (maxRisk >= 85) capped = Math.min(capped, 35);
  else if (maxRisk >= 75) capped = Math.min(capped, 50);
  else if (maxRisk >= 60) capped = Math.min(capped, 65);
  else if (maxRisk >= 45) capped = Math.min(capped, 80);

  if (averageRisk >= 80) capped = Math.min(capped, 25);
  else if (averageRisk >= 65) capped = Math.min(capped, 45);
  else if (averageRisk >= 50) capped = Math.min(capped, 65);

  return clamp(capped);
};

export const sessionToTrip = (session: LiveTripSession): TripData => {
  const snapshots = session.snapshot_history ?? [];

  // FIX: cap to recent window so the UI never processes a huge array
  const recentSnapshots = snapshots.length > MAX_UI_FRAMES
    ? snapshots.slice(snapshots.length - MAX_UI_FRAMES)
    : snapshots;

  const frames = recentSnapshots.map(toFrame);

  const risks = recentSnapshots.map((item) => item.risk_score ?? 0);
  const alertness = recentSnapshots.map((item) => item.alertness_score ?? 0);
  const finiteHeadways = recentSnapshots
    .map((item) => item.predicted_ttc_sec)
    .filter((value): value is number => value !== null && value !== undefined && Number.isFinite(value));
  const last = session.latest_snapshot ?? recentSnapshots[recentSnapshots.length - 1];

  // FIX: use reduce() instead of Math.max(...array).
  // Math.max spread crashes with "Maximum call stack size exceeded"
  // when snapshot_history grows beyond ~10 000 entries.
  const maxRisk = risks.length
    ? risks.reduce((max, v) => (v > max ? v : max), 0)
    : 0;
  const averageRisk = risks.length
    ? risks.reduce((sum, value) => sum + value, 0) / risks.length
    : 0;
  const averageAlertness = alertness.length
    ? alertness.reduce((sum, value) => sum + value, 0) / alertness.length
    : 1;
  const averageHeadway = typeof last?.avg_headway_sec === 'number' && Number.isFinite(last.avg_headway_sec) && last.avg_headway_sec > 0
    ? last.avg_headway_sec
    : finiteHeadways.length
      ? finiteHeadways.reduce((sum, value) => sum + value, 0) / finiteHeadways.length
      : 0;

  const duration = recentSnapshots.length
    ? recentSnapshots[recentSnapshots.length - 1].trip_timestamp_ms / 1000
    : 0;
  const metadata = session.metadata ?? {};

  const currentRisk = last?.risk_score ?? averageRisk;
  const rawSafeScore = 100 - currentRisk;
  const safeDrivingScore = typeof last?.safe_driving_score === 'number'
    ? clamp(last.safe_driving_score)
    : capSafeScoreByRisk(rawSafeScore, maxRisk, averageRisk);

  return {
    trip_id: session.trip_id,
    runtime_status: session.status,
    metadata: {
      trip_id: session.trip_id,
      description: String(metadata.description ?? 'BTC dataset fleet replay'),
      duration_sec: Number(metadata.duration_sec ?? duration),
      fps: Number(metadata.fps ?? 20),
      map: String(metadata.map ?? 'BTC dataset'),
      weather: { ...emptyWeather, ...(metadata.weather ?? {}) },
      driver_profile: String(metadata.driver_profile ?? 'dataset'),
      carla_version: String(metadata.carla_version ?? 'unknown'),
      random_seed: Number(metadata.random_seed ?? 0),
      speed_limit_kmh: Number(metadata.speed_limit_kmh ?? 0),
    },
    driver_summary: {
      subject_id: 'runtime',
      condition_subset: 'dataset replay',
      state_distribution_pct: {
        distracted: recentSnapshots.length
          ? 100 * recentSnapshots.filter((item) => item.driver_state === 'distracted').length / recentSnapshots.length
          : 0,
        alert: recentSnapshots.length
          ? 100 * recentSnapshots.filter((item) => item.driver_state === 'alert').length / recentSnapshots.length
          : 0,
      },
      longest_drowsy_episode_sec: 0,
      microsleep_count: last?.microsleep_count ?? episodeCount(
        recentSnapshots, (item) => item.driver_state === 'microsleep',
      ),
      average_alertness_score: averageAlertness,
      fatigue_score: (1 - averageAlertness) * 100,
    },
    trip_aggregate: {
      safe_driving_score: safeDrivingScore,
      harsh_brake_count: last?.harsh_brake_count ?? recentSnapshots.filter((item) => item.harsh_brake).length,
      harsh_accel_count: last?.harsh_accel_count ?? recentSnapshots.filter((item) => item.harsh_accel).length,
      harsh_corner_count: last?.harsh_corner_count ?? recentSnapshots.filter((item) => item.harsh_corner).length,
      near_miss_count: last?.near_miss_count ?? episodeCount(
        recentSnapshots,
        (item) => item.predicted_ttc_sec !== null && item.predicted_ttc_sec !== undefined && item.predicted_ttc_sec <= 1.5,
      ),
      speeding_pct_time: last?.speeding_pct_time ?? (
        recentSnapshots.length
          ? 100 * recentSnapshots.filter((item) => item.speeding).length / recentSnapshots.length
          : 0
      ),
      tailgating_pct_time: last?.tailgating_pct_time ?? (
        recentSnapshots.length
          ? 100 * recentSnapshots.filter((item) => item.tailgating).length / recentSnapshots.length
          : 0
      ),
      avg_headway_sec: averageHeadway,
      max_risk_score: maxRisk,
      avg_risk_score: averageRisk,
      risk_classification: maxRisk >= 75 ? 'high' : maxRisk >= 50 ? 'medium' : 'low',
    },
    events_log: [],
    frames,
  };
};
