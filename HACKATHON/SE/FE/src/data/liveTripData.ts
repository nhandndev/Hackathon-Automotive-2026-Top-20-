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
    longitudinal_accel: 0,
    lateral_accel: 0,
    location: { x: 0, y: 0, z: 0 },
    rotation: { yaw: 0, pitch: 0, roll: 0 },
    geolocation: { lat: 0, lon: 0, alt: 0 },
  },
  targets: [],
  driver: {
    state: snapshot.driver_state ?? 'unknown',
    alertness_score: snapshot.alertness_score ?? 0,
    eye_state: 'unknown',
    head_pose: 'unknown',
    mouth_state: 'unknown',
    nthu_subject_id: 'runtime',
  },
  events_active: [],
  // predicted_ttc_sec can be null (no vehicle ahead = infinite clearance)
  min_ttc: snapshot.predicted_ttc_sec != null ? snapshot.predicted_ttc_sec : Number.POSITIVE_INFINITY,
  headway_sec: snapshot.predicted_ttc_sec != null ? snapshot.predicted_ttc_sec : Number.POSITIVE_INFINITY,
  behavior_flags: {
    harsh_brake: false,
    harsh_accel: false,
    harsh_corner: false,
    speeding: false,
    tailgating: false,
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

export const sessionToTrip = (session: LiveTripSession): TripData => {
  const snapshots = session.snapshot_history ?? [];

  // FIX: cap to recent window so the UI never processes a huge array
  const recentSnapshots = snapshots.length > MAX_UI_FRAMES
    ? snapshots.slice(snapshots.length - MAX_UI_FRAMES)
    : snapshots;

  const frames = recentSnapshots.map(toFrame);

  const risks = recentSnapshots.map((item) => item.risk_score ?? 0);
  const alertness = recentSnapshots.map((item) => item.alertness_score ?? 0);
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

  const duration = recentSnapshots.length
    ? recentSnapshots[recentSnapshots.length - 1].trip_timestamp_ms / 1000
    : 0;
  const metadata = session.metadata ?? {};

  // FIX: clamp safe_driving_score to [0, 100].
  // Backend risk_score may occasionally exceed 100, which would produce a
  // negative safe_driving_score and break DriverRankingView score labels.
  const rawSafeScore = 100 - (last?.risk_score ?? 0);
  const safeDrivingScore = Math.min(100, Math.max(0, rawSafeScore));

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
      microsleep_count: episodeCount(
        recentSnapshots, (item) => item.driver_state === 'microsleep',
      ),
      average_alertness_score: averageAlertness,
      fatigue_score: (1 - averageAlertness) * 100,
    },
    trip_aggregate: {
      safe_driving_score: safeDrivingScore,
      harsh_brake_count: 0,
      harsh_accel_count: 0,
      harsh_corner_count: 0,
      near_miss_count: episodeCount(
        recentSnapshots,
        (item) => item.predicted_ttc_sec !== null && item.predicted_ttc_sec !== undefined && item.predicted_ttc_sec <= 1.5,
      ),
      speeding_pct_time: 0,
      tailgating_pct_time: 0,
      avg_headway_sec: 0,
      max_risk_score: maxRisk,
      avg_risk_score: averageRisk,
      risk_classification: maxRisk >= 75 ? 'high' : maxRisk >= 50 ? 'medium' : 'low',
    },
    events_log: [],
    frames,
  };
};
