export type ViewMode = 'MAP' | 'INSIGHTS' | 'RANKING' | 'SAFETY' | 'TRIP_DETAIL' | 'VEHICLE_LIVE' | 'SETTINGS';

export type EventSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface EventLogItem {
  id: string;
  time: string;
  event: string;
  severity: EventSeverity;
  location?: string;
  details?: string;
}

export interface Metadata {
  trip_id: string;
  description: string;
  duration_sec: number;
  fps: number;
  map: string;
  weather: Weather;
  driver_profile: string;
  carla_version: string;
  random_seed: number;
  speed_limit_kmh: number;
}

export interface Weather {
  cloudiness: number;
  precipitation: number;
  precipitation_deposits: number;
  sun_altitude_angle: number;
  sun_azimuth_angle: number;
  fog_density: number;
  fog_distance: number;
  wind_intensity: number;
  wetness: number;
}

export interface DriverSummary {
  subject_id: string;
  condition_subset: string;
  state_distribution_pct: {
    distracted: number;
    alert: number;
  };
  longest_drowsy_episode_sec: number;
  microsleep_count: number;
  average_alertness_score: number;
  fatigue_score: number;
}

export interface TripAggregate {
  safe_driving_score: number;
  harsh_brake_count: number;
  harsh_accel_count: number;
  harsh_corner_count: number;
  near_miss_count: number;
  speeding_pct_time: number;
  tailgating_pct_time: number;
  avg_headway_sec: number;
  max_risk_score: number;
  avg_risk_score: number;
  risk_classification: string;
}

export interface EventLog {
  t: number;
  type: string;
  params: Record<string, any>;
}

export interface Frame {
  frame_id: number;
  world_frame: number;
  timestamp: number;
  ego: Ego;
  targets: Target[];
  driver: Driver;
  events_active: any[];
  min_ttc: number;
  headway_sec: number;
  behavior_flags: BehaviorFlags;
  risk: Risk;
}

export interface Ego {
  speed_kmh: number;
  longitudinal_accel: number;
  lateral_accel: number;
  location: { x: number; y: number; z: number };
  rotation: { yaw: number; pitch: number; roll: number };
  geolocation: { lat: number; lon: number; alt: number };
}

export interface Target {
  target_id: number;
  target_class: string;
  rel_pos: { x: number; y: number };
  rel_velocity: { x: number; y: number };
  longitudinal_distance: number;
  lateral_distance: number;
  closing_speed: number;
  ttc_simple: number;
  ttc_2d: number;
  in_collision_cone: boolean;
}

export interface Driver {
  state: string;
  alertness_score: number;
  eye_state: string;
  head_pose: string;
  mouth_state: string;
  nthu_subject_id: string;
}

export interface BehaviorFlags {
  harsh_brake: boolean;
  harsh_accel: boolean;
  harsh_corner: boolean;
  speeding: boolean;
  tailgating: boolean;
}

export interface Risk {
  base_risk: number;
  driver_factor: number;
  final_risk_score: number;
}

export interface TripData {
  trip_id: string;
  runtime_status?: 'pending' | 'running' | 'completed';
  metadata: Metadata;
  driver_summary: DriverSummary;
  trip_aggregate: TripAggregate;
  events_log: EventLog[];
  frames: Frame[];
}

export interface TelemetryPoint {
  time: string;
  speed: number;
  hr: number;
  min_ttc: number;
  headway: number;
  isAnomaly?: boolean;
  anomalyType?: string;
  driver_state?: string;
  risk_score?: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  cardType?: 'DRI_RISK' | 'RECOMMENDATION' | 'COMPARISON' | 'MAINTENANCE';
  cardData?: any;
}

export interface DriverLeaderboard {
  id: string;
  name: string;
  score: number;
  badge?: string;
  type: 'SAFE' | 'AT_RISK';
}

export interface DecisionAlert {
  event_id: string;
  trip_id: string;
  frame_id: number;
  trip_timestamp_ms: number;
  status: 'open' | 'update' | 'resolved';
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  confidence: number;
  audiences: string[];
  recommended_action: string;
  evidence: Record<string, unknown>;
}

export interface LiveSnapshot {
  schema_version: '1.0';
  trip_id: string;
  frame_id: number;
  trip_timestamp_ms: number;
  speed_kmh: number;
  predicted_ttc_sec: number | null;
  risk_score: number;
  driver_state: string;
  driver_confidence: number;
  alertness_score: number;
  eye_state?: string;
  head_pose?: string;
  mouth_state?: string;
  longitudinal_accel?: number;
  lateral_accel?: number;
  speed_limit_kmh?: number;
  safe_driving_score?: number;
  penalty_points?: number;
  harsh_brake?: boolean;
  harsh_accel?: boolean;
  harsh_corner?: boolean;
  speeding?: boolean;
  tailgating?: boolean;
  harsh_brake_count?: number;
  harsh_accel_count?: number;
  harsh_corner_count?: number;
  near_miss_count?: number;
  microsleep_count?: number;
  speeding_pct_time?: number;
  tailgating_pct_time?: number;
  avg_headway_sec?: number;
}

export interface LiveTripSession {
  trip_id: string;
  status: 'pending' | 'running' | 'completed';
  metadata: Partial<Metadata>;
  latest_snapshot: LiveSnapshot | null;
  snapshot_history: LiveSnapshot[];
}

export type InterventionNotifType = 'alarm' | 'stop' | 'call';

export interface InterventionNotif {
  type: InterventionNotifType;
  tripId: string;
  message: string;
  timestamp: number;
}
