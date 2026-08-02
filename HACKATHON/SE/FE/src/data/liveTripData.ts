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
    speed_kmh: snapshot.speed_kmh,
    longitudinal_accel: 0,
    lateral_accel: 0,
    location: { x: 0, y: 0, z: 0 },
    rotation: { yaw: 0, pitch: 0, roll: 0 },
    geolocation: { lat: 0, lon: 0, alt: 0 },
  },
  targets: [],
  driver: {
    state: snapshot.driver_state,
    alertness_score: snapshot.alertness_score,
    eye_state: 'unknown',
    head_pose: 'unknown',
    mouth_state: 'unknown',
    nthu_subject_id: 'runtime',
  },
  events_active: [],
  min_ttc: snapshot.predicted_ttc_sec ?? Number.POSITIVE_INFINITY,
  headway_sec: snapshot.predicted_ttc_sec ?? Number.POSITIVE_INFINITY,
  behavior_flags: {
    harsh_brake: false,
    harsh_accel: false,
    harsh_corner: false,
    speeding: false,
    tailgating: false,
  },
  risk: {
    base_risk: snapshot.risk_score,
    driver_factor: 1,
    final_risk_score: snapshot.risk_score,
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

export const sessionToTrip = (session: LiveTripSession): TripData => {
  const snapshots = session.snapshot_history ?? [];
  const frames = snapshots.map(toFrame);
  const risks = snapshots.map((item) => item.risk_score);
  const alertness = snapshots.map((item) => item.alertness_score);
  const last = session.latest_snapshot ?? snapshots[snapshots.length - 1];
  const maxRisk = risks.length ? Math.max(...risks) : 0;
  const averageRisk = risks.length
    ? risks.reduce((sum, value) => sum + value, 0) / risks.length
    : 0;
  const averageAlertness = alertness.length
    ? alertness.reduce((sum, value) => sum + value, 0) / alertness.length
    : 1;
  const duration = snapshots.length
    ? snapshots[snapshots.length - 1].trip_timestamp_ms / 1000
    : 0;
  const metadata = session.metadata ?? {};

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
        distracted: snapshots.length
          ? 100 * snapshots.filter((item) => item.driver_state === 'distracted').length / snapshots.length
          : 0,
        alert: snapshots.length
          ? 100 * snapshots.filter((item) => item.driver_state === 'alert').length / snapshots.length
          : 0,
      },
      longest_drowsy_episode_sec: 0,
      microsleep_count: episodeCount(
        snapshots, (item) => item.driver_state === 'microsleep',
      ),
      average_alertness_score: averageAlertness,
      fatigue_score: (1 - averageAlertness) * 100,
    },
    trip_aggregate: {
      safe_driving_score: 100 - (last?.risk_score ?? 0),
      harsh_brake_count: 0,
      harsh_accel_count: 0,
      harsh_corner_count: 0,
      near_miss_count: episodeCount(
        snapshots,
        (item) => item.predicted_ttc_sec !== null && item.predicted_ttc_sec <= 1.5,
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
