import { TripData, TelemetryPoint, DriverLeaderboard } from '../types';
import sampleData from './T01-Sample.json';

export const mockTripData: TripData[] = [sampleData as unknown as TripData];

export const MOCK_LEADERBOARD: DriverLeaderboard[] = [
  { id: '1', name: 'John Doe', score: 95, type: 'SAFE', badge: 'Gold' },
  { id: '2', name: 'Jane Smith', score: 92, type: 'SAFE', badge: 'Silver' },
  { id: '3', name: 'Bob Johnson', score: 65, type: 'AT_RISK' },
];

export const mockAnomalies = [
  { name: 'Harsh Braking', count: 4 },
  { name: 'Tailgating', count: 2 },
  { name: 'Speeding', count: 1 },
];

export const initialTelemetry: TelemetryPoint[] = [];

export const INITIAL_CHAT_MESSAGES = [
  {
    id: '1',
    role: 'assistant',
    text: 'Hệ thống Fleet AI Copilot đã được kích hoạt. Tôi đang theo dõi toàn bộ đội xe. Bạn cần hỗ trợ gì?',
  },
];

export const MOCK_TELEMETRY = [
  { time: '00:00', speed: 0, hr: 65 },
  { time: '00:30', speed: 45, hr: 68 },
  { time: '01:00', speed: 60, hr: 72 },
  { time: '01:30', speed: 120, hr: 95 },
  { time: '02:00', speed: 50, hr: 80 },
];
