import React, { useEffect, useMemo, useState } from 'react';
import { VideoOff } from 'lucide-react';

interface LiveCameraFrameProps {
  tripId: string;
  camera: 'road' | 'cabin';
  className?: string;
}

export const LiveCameraFrame: React.FC<LiveCameraFrameProps> = ({ tripId, camera, className = '' }) => {
  const [revision, setRevision] = useState(() => Date.now());
  const [available, setAvailable] = useState(false);
  const endpoint = camera === 'road'
    ? (import.meta.env.VITE_ROAD_FRAME_URL || 'http://127.0.0.1:8000/api/v1/alerts/road-frame')
    : (import.meta.env.VITE_CABIN_FRAME_URL || 'http://127.0.0.1:8000/api/v1/alerts/cabin-frame');

  useEffect(() => {
    setAvailable(false);
    const timer = window.setInterval(() => setRevision(Date.now()), 200);
    return () => window.clearInterval(timer);
  }, [camera, tripId]);

  const frameUrl = useMemo(() => {
    const separator = endpoint.includes('?') ? '&' : '?';
    return `${endpoint}${separator}trip_id=${encodeURIComponent(tripId)}&v=${revision}`;
  }, [endpoint, revision, tripId]);

  const label = camera === 'road' ? 'BTC ROAD FRAME' : 'LIVE WEBCAM';
  return (
    <>
      <img src={frameUrl} alt={`${label} ${tripId}`} onLoad={() => setAvailable(true)} onError={() => setAvailable(false)} className={`${className} ${available ? 'opacity-100' : 'opacity-0'} transition-opacity duration-150`} />
      {!available && <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-950 text-slate-500"><VideoOff className="h-7 w-7" /><span className="text-[10px] font-bold tracking-wider">WAITING FOR {label}</span></div>}
      <div className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-0.5 text-[9px] font-mono text-slate-200"><span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${available ? 'animate-pulse bg-emerald-400' : 'bg-slate-500'}`} />{available ? label : `${camera.toUpperCase()} OFFLINE`}</div>
    </>
  );
};
