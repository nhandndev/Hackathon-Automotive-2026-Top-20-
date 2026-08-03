import React, { useEffect, useMemo, useState } from 'react';
import { CalendarDays, Download, FileText, Shield, UserRound, Wrench } from 'lucide-react';
import { TripData } from '../types';
import { buildRankingRows } from './DriverRankingView';

interface CopilotFleetReportPageProps {
  vehicles: TripData[];
  reportType: string | null;
  tripIds: string | null;
}

const panel = 'rounded-lg border border-[#1E293B] bg-[#111827] shadow-lg shadow-black/20';

const finite = (value: unknown, digits = 1) =>
  typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';

const severityClass = (level: string) => {
  if (level === 'CRITICAL') return 'border-red-500/50 bg-red-950/30 text-red-200';
  if (level === 'AT_RISK') return 'border-orange-500/50 bg-orange-950/30 text-orange-200';
  if (level === 'WATCH') return 'border-amber-500/50 bg-amber-950/30 text-amber-200';
  return 'border-emerald-500/50 bg-emerald-950/30 text-emerald-200';
};

const columnClass = (count: number) => {
  if (count <= 1) return 'grid-cols-1';
  if (count === 2) return 'grid-cols-2';
  if (count === 3) return 'grid-cols-3';
  return 'grid-cols-4';
};

const eventRowsFor = (trip: TripData) => {
  const frames = trip.frames ?? [];
  // mock: replace with Backend intervention/event-history endpoint when it exists.
  return frames
    .filter((frame) => (
      frame.driver?.state !== 'alert'
      || frame.behavior_flags?.harsh_brake
      || frame.behavior_flags?.speeding
      || frame.behavior_flags?.tailgating
      || Number(frame.risk?.final_risk_score ?? 0) >= 50
      || (Number.isFinite(frame.min_ttc) && frame.min_ttc <= 3)
    ))
    .slice(0, 5)
    .map((frame) => ({
      time: `${finite(frame.timestamp, 1)}s`,
      type: frame.driver?.state !== 'alert'
        ? `Driver ${frame.driver?.state}`
        : frame.behavior_flags?.harsh_brake
          ? 'Harsh brake'
          : frame.behavior_flags?.tailgating
            ? 'Tailgating'
            : 'Risk event',
      severity: Number(frame.risk?.final_risk_score ?? 0) >= 70 ? 'Cao' : 'Trung bình',
      detail: `risk=${finite(frame.risk?.final_risk_score)}, ttc=${Number.isFinite(frame.min_ttc) ? `${frame.min_ttc.toFixed(2)}s` : 'Infinity'}, alertness=${finite(frame.driver?.alertness_score, 2)}`,
    }));
};

export const CopilotFleetReportPage: React.FC<CopilotFleetReportPageProps> = ({ vehicles, reportType, tripIds }) => {
  const [copilotInsight, setCopilotInsight] = useState('AI Copilot đang tạo insight từ Bedrock...');
  const selectedIds = (tripIds ?? '').split(',').filter(Boolean);
  const selectedTrips = useMemo(() => (
    selectedIds.length
      ? vehicles.filter((vehicle) => selectedIds.includes(vehicle.trip_id))
      : vehicles.slice(0, 2)
  ), [selectedIds.join(','), vehicles]);
  const rows = useMemo(() => buildRankingRows(selectedTrips.length ? selectedTrips : vehicles.slice(0, 2)), [selectedTrips, vehicles]);
  const reportTitle = reportType === 'maintenance'
    ? 'Vehicle Maintenance Priority Report'
    : reportType === 'safety'
      ? 'Fleet Safety Executive Report'
      : 'Vehicle Safety Comparison';
  const subtitle = reportType === 'maintenance'
    ? 'AI Copilot đánh giá xe cần ưu tiên bảo trì dựa trên harsh events, risk score và behavior flags.'
    : reportType === 'safety'
      ? 'Tổng hợp an toàn fleet, driver risk, TTC/headway và coaching priority.'
      : `So sánh và đánh giá mức độ an toàn của ${rows.length} xe`;
  const fleetAverage = rows.length ? rows.reduce((sum, row) => sum + row.score, 0) / rows.length : 0;

  useEffect(() => {
    let cancelled = false;
    const loadInsight = async () => {
      try {
        const response = await fetch('/api/copilot/report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reportType,
            tripIds: rows.map((row) => row.trip_id),
            rows: rows.map((row) => ({
              trip_id: row.trip_id,
              rank: row.rank,
              score: row.score,
              riskLevel: row.riskLevel,
              coachingPriority: row.coachingPriority,
              avgRisk: row.avgRisk,
              maxRisk: row.maxRisk,
              distractedPct: row.distractedPct,
              fatigueEvents: row.fatigueEvents,
              nearMissCount: row.nearMissCount,
              tailgatingPct: row.tailgatingPct,
              speedingPct: row.speedingPct,
              harshEvents: row.harshEvents,
              criticalEvents: row.criticalEvents,
            })),
            vehicles: selectedTrips.map((trip) => ({
              trip_id: trip.trip_id,
              metadata: trip.metadata,
              driver_summary: trip.driver_summary,
              trip_aggregate: trip.trip_aggregate,
            })),
          }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || `Copilot report HTTP ${response.status}`);
        if (!cancelled) setCopilotInsight(payload.insight || 'AI Copilot chưa trả insight.');
      } catch (err) {
        if (!cancelled) {
          setCopilotInsight(`AI Copilot Insight chưa khả dụng: ${err instanceof Error ? err.message : 'unknown error'}`);
        }
      }
    };
    void loadInsight();
    return () => {
      cancelled = true;
    };
  }, [reportType, rows, selectedTrips]);

  return (
    <div className="min-h-screen overflow-y-auto bg-[#070A12] px-6 py-7 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        <header className="flex items-center justify-between gap-4 border-b border-[#1E293B] pb-5">
          <div className="flex items-start gap-4">
            <div className="grid h-12 w-12 place-items-center rounded-xl bg-sky-500/10 text-sky-300">
              {reportType === 'maintenance' ? <Wrench className="h-7 w-7" /> : <Shield className="h-7 w-7" />}
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight">{reportTitle}</h1>
              <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`${panel} flex items-center gap-3 px-4 py-2 text-sm text-slate-300`}>
              <CalendarDays className="h-4 w-4 text-slate-500" />
              03/08/2026 ~ 03/08/2026
            </div>
            <button className={`${panel} flex items-center gap-2 px-4 py-2 text-sm font-bold text-slate-200 hover:bg-slate-800`}>
              <Download className="h-4 w-4 text-sky-400" />
              Export Report
            </button>
          </div>
        </header>

        <section className={`grid gap-4 ${columnClass(rows.length)}`}>
          {rows.map((row, index) => (
            <div key={row.trip_id} className={`${panel} min-w-0 overflow-hidden p-4 ${index % 2 === 0 ? 'bg-sky-950/20' : 'bg-emerald-950/20'}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                    <span className={`h-2.5 w-2.5 rounded-full ${index % 2 === 0 ? 'bg-sky-400' : 'bg-emerald-400'}`} />
                    XE {String(index + 1).padStart(2, '0')}
                  </div>
                  <h2 className="mt-2 truncate text-2xl font-black">{row.trip_id}</h2>
                  <p className="mt-1 truncate text-xs text-slate-400">{row.trip.metadata?.description ?? 'AI trip session'}</p>
                </div>
                <span className={`shrink-0 rounded border px-2 py-1 text-[10px] font-black ${severityClass(row.riskLevel)}`}>{row.riskLevel}</span>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-2 text-sm">
                <MiniMetric label="Score" value={`${row.score.toFixed(0)}/100`} />
                <MiniMetric label="Rank" value={`#${row.rank}`} />
                <MiniMetric label="Max Risk" value={row.maxRisk.toFixed(1)} />
                <MiniMetric label="Events" value={String(row.criticalEvents)} />
              </div>
              <div className="mt-4 flex items-center gap-2 text-xs text-slate-300">
                <UserRound className="h-4 w-4 text-sky-400" />
                Driver profile: {row.trip.metadata?.driver_profile ?? row.trip.driver_summary?.subject_id ?? 'N/A'}
              </div>
            </div>
          ))}
        </section>

        <section className={`${panel} overflow-hidden`}>
          <div className="grid grid-cols-[1fr_180px_180px] border-b border-[#1E293B] px-5 py-4 text-xs font-black uppercase tracking-widest text-slate-400">
            <span>Business KPI</span>
            <span className="text-center">Fleet Average</span>
            <span className="text-center">Best Driver</span>
          </div>
          {[
            ['Tổng điểm an toàn', `${fleetAverage.toFixed(1)}/100`, rows[0] ? `${rows[0].score.toFixed(1)}/100` : 'N/A'],
            ['TTC / near miss risk', `${rows.reduce((sum, row) => sum + row.nearMissCount, 0)} near misses`, rows[0] ? `${rows[0].nearMissCount} near misses` : 'N/A'],
            ['An toàn của bác tài', `${(rows.reduce((sum, row) => sum + row.distractedPct, 0) / Math.max(rows.length, 1)).toFixed(1)}% distracted`, rows[0] ? `${rows[0].distractedPct.toFixed(1)}% distracted` : 'N/A'],
            ['Số log / sự kiện', `${rows.reduce((sum, row) => sum + row.criticalEvents, 0)} events`, rows[0] ? `${rows[0].criticalEvents} events` : 'N/A'],
          ].map(([label, avg, best]) => (
            <div key={label} className="grid grid-cols-[1fr_180px_180px] border-b border-[#1E293B] px-5 py-4 text-sm">
              <span className="font-bold text-slate-200">{label}</span>
              <span className="text-center font-mono text-sky-300">{avg}</span>
              <span className="text-center font-mono text-emerald-300">{best}</span>
            </div>
          ))}
        </section>

        <section className={`grid gap-4 ${columnClass(rows.length)}`}>
          {rows.map((row) => (
            <div key={row.trip_id} className={`${panel} overflow-hidden`}>
              <div className="border-b border-[#1E293B] px-4 py-3">
                <h3 className="truncate text-sm font-black text-slate-100">{row.trip_id} event log</h3>
              </div>
              <div className="grid grid-cols-[70px_1fr_82px] text-xs">
                {eventRowsFor(row.trip).map((event) => (
                  <React.Fragment key={`${event.time}-${event.type}`}>
                    <span className="border-b border-[#1E293B] px-3 py-2 font-mono text-slate-400">{event.time}</span>
                    <span className="border-b border-[#1E293B] px-3 py-2 text-slate-300">
                      <b className="block text-slate-100">{event.type}</b>
                      {event.detail}
                    </span>
                    <span className="border-b border-[#1E293B] px-3 py-2 text-center text-amber-300">{event.severity}</span>
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
        </section>

        <section className={`${panel} p-5`}>
          <div className="mb-3 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400">
            <FileText className="h-4 w-4 text-sky-400" />
            AI Copilot Insight
            <span className="ml-auto text-emerald-400">Bedrock</span>
          </div>
          <p className="whitespace-pre-line text-sm leading-relaxed text-slate-300">
            {copilotInsight}
          </p>
        </section>
      </div>
    </div>
  );
};

const MiniMetric = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-2">
    <span className="block text-[10px] font-bold uppercase text-slate-500">{label}</span>
    <span className="mt-1 block truncate font-mono text-base font-black text-slate-100">{value}</span>
  </div>
);
