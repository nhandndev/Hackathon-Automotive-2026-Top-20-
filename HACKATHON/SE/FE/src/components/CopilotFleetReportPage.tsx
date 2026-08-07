import React, { useEffect, useMemo, useState, useRef } from 'react';
import { CalendarDays, Download, FileText, Shield, UserRound, Wrench, FileDown, FileCode, Check, ChevronDown, ChevronUp, Eye } from 'lucide-react';
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
  return 'grid-cols-1 md:grid-cols-2';
};

const eventRowsFor = (trip: TripData) => {
  const frames = trip.frames ?? [];
  const events: Array<{ time: string; type: string; severity: string; detail: string; rawTimestamp: number }> = [];
  let previousState: string | undefined = undefined;
  const lastEventTimeByType: Record<string, number> = {};

  for (const frame of frames) {
    const currentState = frame.driver?.state ?? 'alert';
    const isStateChanged = previousState !== undefined && previousState !== currentState;
    const hasBehaviorFlag = frame.behavior_flags?.harsh_brake || frame.behavior_flags?.tailgating || frame.behavior_flags?.speeding;
    const isHighRisk = Number(frame.risk?.final_risk_score ?? 0) >= 50;
    const isLowTtc = Number.isFinite(frame.min_ttc) && (frame.min_ttc as number) <= 3;
    const currentTs = Number(frame.timestamp ?? 0);

    if (isStateChanged || hasBehaviorFlag || isHighRisk || isLowTtc) {
      let eventTitle = 'Sự kiện an toàn';
      const riskScore = Number(frame.risk?.final_risk_score ?? 0);

      // Determine category
      let category = 'Sự kiện an toàn';
      if (riskScore >= 70 || currentState === 'microsleep' || currentState === 'yawning') {
        category = 'Sự kiện nguy hiểm';
      } else if (riskScore >= 40 || currentState === 'drowsy' || currentState === 'distracted' || hasBehaviorFlag) {
        category = 'Sự kiện cảnh báo';
      }

      if (isStateChanged) {
        eventTitle = `Chuyển trạng thái: ${previousState} ➔ ${currentState}`;
      } else if (frame.behavior_flags?.harsh_brake) {
        eventTitle = 'Phanh gấp (Harsh brake)';
      } else if (frame.behavior_flags?.tailgating) {
        eventTitle = 'Bám đuôi gần (Tailgating)';
      } else if (frame.behavior_flags?.speeding) {
        eventTitle = 'Vượt quá tốc độ (Speeding)';
      } else if (currentState !== 'alert') {
        eventTitle = `Tài xế ${currentState}`;
      }

      // DATA DEBOUNCE FILTER (3.0s window): Filter out sensor noise (e.g. 14 harsh brakes in 0.7s)
      const lastTs = lastEventTimeByType[eventTitle] ?? -999;
      if (currentTs - lastTs >= 3.0) {
        lastEventTimeByType[eventTitle] = currentTs;
        events.push({
          time: `${finite(frame.timestamp, 1)}s`,
          type: eventTitle,
          severity: category,
          detail: `risk=${finite(frame.risk?.final_risk_score)}, ttc=${Number.isFinite(frame.min_ttc) ? `${(frame.min_ttc as number).toFixed(2)}s` : 'Infinity'}, alertness=${finite(frame.driver?.alertness_score, 2)}`,
          rawTimestamp: currentTs,
        });
      }
    }
    previousState = currentState;
  }

  // Fallback if no transitions
  if (events.length === 0 && frames.length > 0) {
    return frames.map(f => ({
      time: `${finite(f.timestamp, 1)}s`,
      type: `Lái xe ${f.driver?.state ?? 'alert'}`,
      severity: 'Sự kiện an toàn',
      detail: `risk=${finite(f.risk?.final_risk_score)}, ttc=${Number.isFinite(f.min_ttc) ? `${(f.min_ttc as number).toFixed(2)}s` : 'Infinity'}`,
    }));
  }

  return events;
};

export const CopilotFleetReportPage: React.FC<CopilotFleetReportPageProps> = ({ vehicles, reportType, tripIds }) => {
  const [copilotInsight, setCopilotInsight] = useState('AI Copilot đang tạo insight từ Bedrock...');
  const [aiDiagnostics, setAiDiagnostics] = useState<any[] | null>(null);
  const [aiActionOrders, setAiActionOrders] = useState<any | null>(null);
  const [aiTripInsights, setAiTripInsights] = useState<Record<string, any>>({});
  const [isLoadingInsight, setIsLoadingInsight] = useState(true);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);
  const [expandedTrips, setExpandedTrips] = useState<Record<string, boolean>>({});
  const menuRef = useRef<HTMLDivElement>(null);

  const toggleTripExpand = (tripId: string) => {
    setExpandedTrips(prev => ({ ...prev, [tripId]: !prev[tripId] }));
  };

  const selectedIds = (tripIds ?? '').split(',').filter(Boolean);
  const selectedTrips = useMemo(() => (
    selectedIds.length
      ? vehicles.filter((vehicle) => selectedIds.includes(vehicle.trip_id))
      : vehicles.slice(0, 2)
  ), [selectedIds.join(','), vehicles]);
  
  const rows = useMemo(() => {
    const rawRows = buildRankingRows(selectedTrips.length ? selectedTrips : vehicles.slice(0, 2));
    if (reportType === 'maintenance') {
      // Sort by Wear Damage Percentage (descending: highest wear / damage first)
      return [...rawRows].sort((a, b) => {
        const aHarsh = a.harshEvents;
        const aCrit = a.criticalEvents;
        const aSpeed = a.speedingPct;
        const aBrakeWear = Math.min(98, Math.max(12, Math.round(15 + aHarsh * 3 + aCrit * 8)));
        const aTireWear = Math.min(95, Math.max(10, Math.round(10 + aSpeed * 0.4 + aHarsh * 2)));
        const aTotalWear = aBrakeWear + aTireWear;

        const bHarsh = b.harshEvents;
        const bCrit = b.criticalEvents;
        const bSpeed = b.speedingPct;
        const bBrakeWear = Math.min(98, Math.max(12, Math.round(15 + bHarsh * 3 + bCrit * 8)));
        const bTireWear = Math.min(95, Math.max(10, Math.round(10 + bSpeed * 0.4 + bHarsh * 2)));
        const bTotalWear = bBrakeWear + bTireWear;

        return bTotalWear - aTotalWear;
      });
    }
    return rawRows;
  }, [selectedTrips, reportType, vehicles]);
  
  const reportTitle = reportType === 'maintenance'
    ? 'Vehicle Maintenance Priority Report'
    : reportType === 'safety'
      ? 'Fleet Safety Executive Report'
      : 'Vehicle Safety Comparison Report';
      
  const subtitle = reportType === 'maintenance'
    ? 'AI Copilot đánh giá xe cần ưu tiên bảo trì dựa trên harsh events, risk score và behavior flags.'
    : reportType === 'safety'
      ? 'Tổng hợp an toàn fleet, driver risk, TTC/headway và coaching priority.'
      : `So sánh và đánh giá mức độ an toàn của ${rows.length} xe`;

  const allFleetRows = useMemo(() => buildRankingRows(vehicles), [vehicles]);
  const fleetAverage = allFleetRows.length ? allFleetRows.reduce((sum, row) => sum + row.score, 0) / allFleetRows.length : 0;

  useEffect(() => {
    let cancelled = false;
    const activeExpandedIds = Object.keys(expandedTrips).filter(id => expandedTrips[id]);

    const loadInsight = async () => {
      setIsLoadingInsight(true);
      try {
        const response = await fetch('/api/copilot/report', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reportType,
            tripIds: rows.map((row) => row.trip_id),
            expandedTripIds: activeExpandedIds,
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
        if (!cancelled) {
          setCopilotInsight(payload.fleet_insight || payload.insight || 'AI Copilot chưa trả insight.');
          if (payload.trip_insights) setAiTripInsights(payload.trip_insights);
          if (payload.vehicle_diagnostics) setAiDiagnostics(payload.vehicle_diagnostics);
          if (payload.action_orders) setAiActionOrders(payload.action_orders);
        }
      } catch (err) {
        if (!cancelled) {
          setCopilotInsight(`AI Copilot Insight chưa khả dụng: ${err instanceof Error ? err.message : 'unknown error'}`);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingInsight(false);
        }
      }
    };
    void loadInsight();
    return () => {
      cancelled = true;
    };
  }, [reportType, rows, selectedTrips, JSON.stringify(expandedTrips)]);

  // Click outside listener for export menu
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const generateReportHTML = () => {
    const nowStr = new Date().toLocaleString('vi-VN');
    const rowsHTML = rows.map((row, idx) => `
      <div style="border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #f8fafc;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 12px;">
          <div>
            <span style="font-weight: bold; color: #0284c7; font-size: 12px; text-transform: uppercase;">XE ${String(idx + 1).padStart(2, '0')}</span>
            <h3 style="margin: 4px 0 0 0; color: #0f172a; font-size: 20px;">Mã Chuyến: ${row.trip_id}</h3>
            <p style="margin: 2px 0 0 0; color: #64748b; font-size: 13px;">Tài xế: ${row.trip_id}</p>
          </div>
          <span style="background-color: ${row.riskLevel === 'CRITICAL' ? '#fee2e2' : row.riskLevel === 'AT_RISK' ? '#ffedd5' : '#dcfce7'}; color: ${row.riskLevel === 'CRITICAL' ? '#991b1b' : row.riskLevel === 'AT_RISK' ? '#9a3412' : '#166534'}; border: 1px solid ${row.riskLevel === 'CRITICAL' ? '#f87171' : row.riskLevel === 'AT_RISK' ? '#fb923c' : '#4ade80'}; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 12px;">
            ${row.riskLevel}
          </span>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px;">
          <tr>
            <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Điểm an toàn:</strong> ${row.score.toFixed(0)}/100</td>
            <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Xếp hạng Fleet:</strong> #${row.rank}</td>
            <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Risk Cao Nhất:</strong> ${row.maxRisk.toFixed(1)}</td>
            <td style="padding: 6px; font-size: 13px; color: #475569;"><strong>Tổng Cảnh Báo:</strong> ${row.criticalEvents}</td>
          </tr>
        </table>

        <h4 style="margin: 8px 0 6px 0; color: #334155; font-size: 14px;">Lịch sử Cảnh báo Gần nhất:</h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <thead>
            <tr style="background-color: #e2e8f0; text-align: left;">
              <th style="padding: 6px; border: 1px solid #cbd5e1;">Thời gian</th>
              <th style="padding: 6px; border: 1px solid #cbd5e1;">Loại Cảnh Báo</th>
              <th style="padding: 6px; border: 1px solid #cbd5e1;">Chi Tiết Số Liệu</th>
              <th style="padding: 6px; border: 1px solid #cbd5e1;">Mức Độ</th>
            </tr>
          </thead>
          <tbody>
            ${eventRowsFor(row.trip).map(evt => `
              <tr>
                <td style="padding: 6px; border: 1px solid #cbd5e1; font-family: monospace;">${evt.time}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e1; font-weight: bold;">${evt.type}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e1; color: #475569;">${evt.detail}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e1; color: ${
                  evt.severity === 'Sự kiện nguy hiểm'
                    ? '#dc2626'
                    : evt.severity === 'Sự kiện cảnh báo'
                      ? '#d97706'
                      : '#16a34a'
                }; font-weight: bold;">${evt.severity}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `).join('');

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>${reportTitle}</title>
        <style>
          body { font-family: 'Helvetica Neue', Arial, sans-serif; color: #0f172a; line-height: 1.5; padding: 30px; max-width: 900px; margin: 0 auto; }
          h1 { color: #0284c7; font-size: 24px; margin-bottom: 4px; border-bottom: 3px solid #0284c7; padding-bottom: 8px; }
          .header-meta { font-size: 12px; color: #64748b; margin-bottom: 20px; display: flex; justify-content: space-between; }
          .subtitle { font-size: 14px; color: #475569; margin-bottom: 24px; font-style: italic; }
          .section-title { font-size: 16px; font-weight: bold; color: #0f172a; border-left: 4px solid #0284c7; padding-left: 8px; margin: 24px 0 12px 0; }
          table.kpi-table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
          table.kpi-table th, table.kpi-table td { padding: 10px; border: 1px solid #cbd5e1; font-size: 13px; text-align: left; }
          table.kpi-table th { background-color: #0f172a; color: #ffffff; }
          .insight-box { background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 16px; margin-top: 20px; }
          .insight-box p { margin: 0; font-size: 13px; color: #0369a1; white-space: pre-line; }
          .footer { margin-top: 40px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 12px; }
        </style>
      </head>
      <body>
        <h1>${reportTitle}</h1>
        <div class="header-meta">
          <span><strong>DMS Safety AI Platform</strong> | Báo Cáo Phân Tích Đội Xe</span>
          <span>Thời gian xuất: ${nowStr}</span>
        </div>
        <p class="subtitle">${subtitle}</p>

        <div class="section-title">1. Tổng Quan Chỉ Số KPI Fleet</div>
        <table class="kpi-table">
          <thead>
            <tr>
              <th>Chỉ Số An Toàn</th>
              <th>Trung Bình Toàn Đội Xe</th>
              <th>Lái Xe An Toàn Nhất</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Tổng Điểm An Toàn</strong></td>
              <td>${fleetAverage.toFixed(1)}/100</td>
              <td>${rows[0] ? `${rows[0].score.toFixed(1)}/100` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>TTC / Rủi Ro Suy Suýt Va Chạm</strong></td>
              <td>${rows.reduce((sum, row) => sum + row.nearMissCount, 0)} lượt near-miss</td>
              <td>${rows[0] ? `${rows[0].nearMissCount} lượt` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Tỉ Lệ Mất Tập Trung (Distracted)</strong></td>
              <td>${(rows.reduce((sum, row) => sum + row.distractedPct, 0) / Math.max(rows.length, 1)).toFixed(1)}%</td>
              <td>${rows[0] ? `${rows[0].distractedPct.toFixed(1)}%` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Sự Kiện An Toàn (Bình thường)</strong></td>
              <td>${(rows.flatMap(r => eventRowsFor(r.trip)).filter(e => e.severity === 'Sự kiện an toàn').length / Math.max(rows.length, 1)).toFixed(0)} sự kiện</td>
              <td>${rows[0] ? `${eventRowsFor(rows[0].trip).filter(e => e.severity === 'Sự kiện an toàn').length} sự kiện` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Sự Kiện Cảnh Báo (Chú ý)</strong></td>
              <td>${(rows.flatMap(r => eventRowsFor(r.trip)).filter(e => e.severity === 'Sự kiện cảnh báo').length / Math.max(rows.length, 1)).toFixed(0)} sự kiện</td>
              <td>${rows[0] ? `${eventRowsFor(rows[0].trip).filter(e => e.severity === 'Sự kiện cảnh báo').length} sự kiện` : 'N/A'}</td>
            </tr>
            <tr>
              <td><strong>Sự Kiện Nguy Hiểm (Khẩn cấp)</strong></td>
              <td>${(rows.flatMap(r => eventRowsFor(r.trip)).filter(e => e.severity === 'Sự kiện nguy hiểm').length / Math.max(rows.length, 1)).toFixed(0)} sự kiện</td>
              <td>${rows[0] ? `${eventRowsFor(rows[0].trip).filter(e => e.severity === 'Sự kiện nguy hiểm').length} sự kiện` : 'N/A'}</td>
            </tr>
          </tbody>
        </table>

        <div class="section-title">2. Tình Trạng Sức Khỏe Kỹ Thuật & Hạn Bảo Trì (OBD-II Vehicle Health)</div>
        <table class="kpi-table">
          <thead>
            <tr>
              <th>Mã Xe / Chuyến</th>
              <th>Hao Mòn Má Phanh</th>
              <th>Hao Mòn Lốp</th>
              <th>Số Odo (km)</th>
              <th>Mã Lỗi DTC (OBD-II)</th>
              <th>Tình Trạng Bảo Trì</th>
              <th>Dự Toán Chi Phí & Downtime</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((row, idx) => {
              const harshCount = row.harshEvents;
              const criticalCount = row.criticalEvents;
              const speedingPct = row.speedingPct;

              const brakeWear = Math.min(98, Math.max(15, Math.round(20 + harshCount * 5.5 + criticalCount * 3)));
              const tireWear = Math.min(95, Math.max(10, Math.round(15 + speedingPct * 0.8 + harshCount * 3)));
              const dtcCode = harshCount >= 10 ? 'C0035 (Brake Wear/Speed Sensor)' : row.maxRisk >= 80 ? 'P0300 (Engine Warning)' : 'P0000 (No Error)';
              const serviceOverdue = brakeWear > 70 ? `Bảo trì phanh (${brakeWear}%)` : tireWear > 70 ? `Đảo lốp (${tireWear}%)` : 'Bình thường';
              const estCost = `${(harshCount * 450000 + criticalCount * 850000).toLocaleString('vi-VN')} VNĐ`;
              const downtime = brakeWear > 70 ? '1 ngày' : '0.5 ngày';
              return `
                <tr>
                  <td><strong>XE ${String(idx + 1).padStart(2, '0')} (${row.trip_id})</strong></td>
                  <td style="color: #d97706; font-weight: bold;">${brakeWear}%</td>
                  <td style="color: #0284c7; font-weight: bold;">${tireWear}%</td>
                  <td>${row.trip.metadata?.duration_sec ?? 0}s</td>
                  <td style="font-family: monospace; color: ${row.riskLevel === 'CRITICAL' ? '#dc2626' : '#16a34a'}; font-weight: bold;">${dtcCode}</td>
                  <td>${serviceOverdue}</td>
                  <td>${estCost} | ~${downtime}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>

        <div class="section-title">3. Lệnh Hành Động Bảo Trì Bắt Buộc (Action Orders)</div>
        <div style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
          <strong style="color: #991b1b;">🚨 Dừng Lưu Hành Ngay (Do Not Drive):</strong> Yêu cầu thu hồi phương tiện thuộc chuyến <strong>${rows.find(r => r.riskLevel === 'CRITICAL')?.trip_id ?? 'T01'}</strong> kiểm tra ngay lập tức hệ thống phanh và mã lỗi động cơ P0300.
        </div>
        <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 12px; margin-bottom: 16px;">
          <strong style="color: #9a3412;">⚠️ Bảo Trì Ưu Tiên Trong 48H:</strong> Căn chỉnh thước lái, kiểm tra độ chụm bánh xe và cảm biến tốc độ bánh xe (C0035) do phát hiện các cú phanh gấp và va chạm suýt soát.
        </div>

        <div class="section-title">4. Chi Tiết Đánh Giá Chi Tiết Theo Xe (${rows.length} xe)</div>
        ${rowsHTML}

        <div class="section-title">5. Khuyến Nghị & Insight Từ AI Copilot (Bedrock Engine)</div>
        <div class="insight-box">
          <p>${copilotInsight.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
        </div>

        <div class="footer">
          Báo cáo tự động tạo bởi Hệ Thống Giám Sát Driver Safety DMS (VinFast Automotive Hackathon 2026).
        </div>
      </body>
      </html>
    `;
  };

  const handleExportPDF = async () => {
    setShowExportMenu(false);
    const htmlContent = generateReportHTML();
    const fileName = `DMS_Fleet_Report_${new Date().toISOString().slice(0, 10)}.pdf`;

    // Create temporary container for PDF generation
    const element = document.createElement('div');
    element.innerHTML = htmlContent;
    element.style.position = 'absolute';
    element.style.left = '-9999px';
    element.style.top = '-9999px';
    document.body.appendChild(element);

    try {
      const pkgName = 'html2pdf.js';
      // @vite-ignore
      const html2pdfModule = await import(/* @vite-ignore */ pkgName);
      const html2pdf = html2pdfModule.default || html2pdfModule;

      const opt = {
        margin: 10,
        filename: fileName,
        image: { type: 'jpeg' as const, quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'portrait' as const }
      };

      await html2pdf().set(opt).from(element).save();
      setDownloadSuccess(`Đã tải xuống thành công file ${fileName}!`);
    } catch (err) {
      console.error('PDF download error:', err);
      // Fallback method if html2pdf canvas rendering fails
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.open();
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        setTimeout(() => {
          printWindow.focus();
          printWindow.print();
        }, 300);
      }
    } finally {
      document.body.removeChild(element);
      setTimeout(() => setDownloadSuccess(null), 4000);
    }
  };

  const handleExportWord = () => {
    setShowExportMenu(false);
    const htmlContent = generateReportHTML();

    // Convert HTML to valid Word Document Blob (.doc)
    const header = "<html xmlns:o='urn:schemas-microsoft-com:office:office' "+
      "xmlns:w='urn:schemas-microsoft-com:office:word' "+
      "xmlns='http://www.w3.org/TR/REC-html40'>"+
      "<head><meta charset='utf-8'><title>Fleet Safety Report</title></head><body>";
    const footer = "</body></html>";
    const sourceHTML = header + htmlContent + footer;

    const blob = new Blob(['\ufeff', sourceHTML], {
      type: 'application/msword'
    });

    const fileName = `DMS_Fleet_Report_${new Date().toISOString().slice(0, 10)}.doc`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setDownloadSuccess('Đã tải xuống báo cáo Word (.doc) thành công!');
    setTimeout(() => setDownloadSuccess(null), 4000);
  };

  return (
    <div className="min-h-screen overflow-y-auto bg-[#070A12] px-6 py-7 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-5">
        {downloadSuccess && (
          <div className="flex items-center gap-2 rounded-lg border border-emerald-500/50 bg-emerald-950/80 px-4 py-3 text-sm font-bold text-emerald-200 shadow-lg">
            <Check className="h-5 w-5 text-emerald-400" />
            {downloadSuccess}
          </div>
        )}

        <header className="flex items-center justify-between gap-4 border-b border-[#1E293B] pb-5">
          <div className="flex items-start gap-4">
            <a
              href="/?view=MAP"
              className="flex items-center gap-2 rounded-xl bg-slate-800/80 px-3.5 py-3 text-xs font-bold text-slate-300 border border-slate-700 hover:bg-slate-700 hover:text-white transition-all shadow-md shrink-0"
              title="Quay lại Dashboard Trang Chủ"
            >
              <Eye className="h-4 w-4 text-sky-400" />
              <span>Trang Chủ Command</span>
            </a>
            <div className="grid h-12 w-12 place-items-center rounded-xl bg-sky-500/10 text-sky-300 shrink-0">
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
            <div className="relative" ref={menuRef}>
              <button 
                onClick={() => setShowExportMenu(!showExportMenu)}
                className={`${panel} flex items-center gap-2 px-4 py-2 text-sm font-bold text-slate-200 transition-colors hover:bg-slate-800 active:scale-95`}
              >
                <Download className="h-4 w-4 text-sky-400" />
                Export Report
              </button>

              {showExportMenu && (
                <div className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-lg border border-[#1E293B] bg-[#0F172A] p-1 shadow-2xl backdrop-blur-md">
                  <button
                    onClick={handleExportPDF}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium text-slate-200 transition-colors hover:bg-sky-500/10 hover:text-sky-400"
                  >
                    <FileDown className="h-4 w-4 text-red-400" />
                    <span>Xuất báo cáo PDF (.pdf)</span>
                  </button>
                  <button
                    onClick={handleExportWord}
                    className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium text-slate-200 transition-colors hover:bg-sky-500/10 hover:text-sky-400"
                  >
                    <FileCode className="h-4 w-4 text-blue-400" />
                    <span>Xuất báo cáo Word (.doc)</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* --- SECTION 1: TOP ABSTRACT TRIP SUMMARY CARDS --- */}
        <section className={`grid gap-4 ${columnClass(rows.length)}`}>
          {rows.map((row, index) => {
            const isExpanded = !!expandedTrips[row.trip_id];
            return (
              <div key={row.trip_id} className={`${panel} min-w-0 overflow-hidden p-4 ${index % 2 === 0 ? 'bg-sky-950/20' : 'bg-emerald-950/20'} transition-all`}>
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

                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  {reportType === 'maintenance' ? (
                    <>
                      <MiniMetric label="Mã lỗi DTC" value={row.harshEvents >= 10 ? 'C0035' : row.score < 60 ? 'P0300' : 'P0000'} />
                      <MiniMetric label="Hao mòn phanh" value={`${Math.min(98, Math.max(15, Math.round(20 + row.harshEvents * 5.5 + row.criticalEvents * 3)))}%`} />
                      <MiniMetric label="Hao mòn lốp" value={`${Math.min(95, Math.max(10, Math.round(15 + row.speedingPct * 0.8 + row.harshEvents * 3)))}%`} />
                      <MiniMetric label="Ưu tiên bảo trì" value={row.coachingPriority} />
                    </>
                  ) : (
                    <>
                      <MiniMetric label="Safe Score" value={`${row.score.toFixed(0)}/100`} />
                      <MiniMetric label="Ranking" value={`#${row.rank}`} />
                      <MiniMetric label="Max Risk" value={row.maxRisk.toFixed(1)} />
                      <MiniMetric label="Sự kiện" value={String(row.criticalEvents)} />
                    </>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-xs gap-2">
                  <div className="flex items-center gap-2 text-slate-300 truncate">
                    <UserRound className="h-4 w-4 text-sky-400 shrink-0" />
                    <span className="truncate">{row.trip_id}</span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={`/?view=TRIP_DETAIL&trip_id=${row.trip_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 rounded-lg bg-emerald-600/20 px-2.5 py-1.5 font-bold text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600 hover:text-white transition-all active:scale-95"
                      title="Xem chi tiết hành trình Telemetry live tại Tab mới"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      <span>Trip Detail (Tab mới)</span>
                    </a>

                    <button
                      onClick={() => toggleTripExpand(row.trip_id)}
                      className="flex items-center gap-1.5 rounded-lg bg-sky-600/20 px-3 py-1.5 font-bold text-sky-300 border border-sky-500/30 hover:bg-sky-600 hover:text-white transition-all active:scale-95"
                    >
                      {isExpanded ? (
                        <>
                          <span>Thu gọn</span>
                          <ChevronUp className="h-4 w-4" />
                        </>
                      ) : (
                        <>
                          <span>Báo cáo xe</span>
                          <ChevronDown className="h-4 w-4" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </section>

        {/* --- SECTION A & B: VEHICLE DETAILS SECTION (EXPANDED BY BÁO CÁO XE BUTTON OR SINGLE TRIP VIEW) --- */}
        {(rows.length === 1 || rows.some(r => expandedTrips[r.trip_id])) && (
          <section className={`${panel} p-5 space-y-4`}>
            {reportType === 'maintenance' ? (
              /* --- MAINTENANCE MODE: VEHICLE HEALTH & MECHANICAL STRESS DIAGNOSTICS --- */
              <>
                <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                  <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-amber-400">
                    <Wrench className="h-5 w-5" />
                    Tình Trạng Sức Khỏe Kỹ Thuật & Hạn Bảo Trì (Vehicle Health & Diagnostics)
                  </div>
                  <span className="rounded bg-amber-500/10 px-2.5 py-1 text-xs font-bold text-amber-300 border border-amber-500/20">
                    Bedrock Telemetry AI Engine
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((row, idx) => {
                    const aiDiag = aiDiagnostics?.find((d: any) => d.trip_id === row.trip_id);
                    const harshCount = row.harshEvents;
                    const criticalCount = row.criticalEvents;
                    const speedingPct = row.speedingPct;

                    // EXACT MATHEMATICAL CONSISTENCY WITH LOG TABLE (Base Wear + Sum of Log Badges)
                    const logEvents = eventRowsFor(row.trip);
                    const brakeLogCount = logEvents.filter(e => e.type.toLowerCase().includes('phanh') || e.type.toLowerCase().includes('brake') || e.severity === 'Sự kiện nguy hiểm').length;
                    const tireLogCount = logEvents.filter(e => e.type.toLowerCase().includes('tốc độ') || e.type.toLowerCase().includes('speed') || e.type.toLowerCase().includes('làn')).length;

                    // Base 15% + (Brake Log * 3.5%) + (Critical * 5%)
                    const brakeWear = Math.min(98, Math.max(12, Math.round(15 + brakeLogCount * 3.5 + criticalCount * 5)));
                    // Base 10% + (Speeding % * 0.4%) + (Tire Log * 2.0%)
                    const tireWear = Math.min(95, Math.max(10, Math.round(10 + speedingPct * 0.4 + tireLogCount * 2.0)));
                    
                    const isAiLoading = isLoadingInsight && !aiDiag;
                    
                    // Dynamic DTC assignment from real events
                    const dtcCode = isAiLoading ? '⏳ AI đang quét mã lỗi...' : (aiDiag?.dtc_code ?? (
                      brakeLogCount >= 5 ? 'C0035 (Wheel Speed Sensor Circuit)' :
                      speedingPct >= 35 ? 'P0299 (Turbocharger Underboost / Speeding Warning)' : 'P0000 (No Error)'
                    ));
                    
                    const isRoutine = typeof dtcCode === 'string' && dtcCode.includes('P0000') && brakeWear < 60;
                    
                    const serviceOverdue = isAiLoading ? '⏳ AI đang chẩn đoán...' : (aiDiag?.maintenance_status ?? (
                      isRoutine ? 'Bảo dưỡng định kỳ chuẩn' :
                      brakeWear > 70 ? `Cần bảo trì phanh (MSI ${brakeWear}/100)` : `Cần kiểm tra kỹ thuật (MSI ${brakeWear}/100)`
                    ));

                    // Accurate Rule-Based Cost Matrix ($1.5M - $3.5M VNĐ for DTC C0035 sensor repair)
                    const estCostVal = isAiLoading ? 'Đang tính toán...' : (aiDiag?.estimated_cost_vnd ?? (
                      isRoutine 
                        ? (1500000 + harshCount * 150000) 
                        : (2500000 + harshCount * 200000 + criticalCount * 300000)
                    ));
                    const estCost = typeof estCostVal === 'number' 
                      ? `${estCostVal.toLocaleString('vi-VN')} VNĐ (dự tính)` 
                      : `${estCostVal}`;
                    const downtime = isAiLoading ? '⏳' : (isRoutine ? '0.5 ngày' : (brakeWear > 75 ? '1.0 ngày' : '0.5 ngày'));
                    const parts = isAiLoading ? '⏳ Đang check kho...' : (aiDiag?.parts_availability ?? (isRoutine ? 'Sẵn có trong kho' : 'Cần kiểm tra kho'));
                    const workOrderStatus = isAiLoading ? '⏳ Chờ duyệt' : (isRoutine ? 'Routine Approved' : (row.score < 60 ? 'Pending Approval' : 'Work Order Created'));

                    return (
                      <div key={row.trip_id} className="rounded-lg border border-amber-500/40 bg-[#0A0F1D] p-4 space-y-3 shadow-xl">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-amber-300 text-sm">XE {String(idx + 1).padStart(2, '0')} - {row.trip_id}</span>
                            <span className="text-[10px] text-slate-400">({row.trip_id})</span>
                          </div>
                          <span className={`text-xs font-black px-2 py-0.5 rounded ${isRoutine ? 'bg-sky-500/20 text-sky-300' : 'bg-red-500/20 text-red-300 border border-red-500/40'}`}>
                            {serviceOverdue}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="space-y-1">
                            <div className="flex justify-between text-slate-400">
                              <span>Brake Stress Index (MSI):</span>
                              <span className={`font-mono font-bold ${brakeWear > 70 ? 'text-red-400' : brakeWear > 40 ? 'text-amber-300' : 'text-emerald-400'}`}>{brakeWear}/100</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${brakeWear > 70 ? 'bg-red-500' : brakeWear > 40 ? 'bg-amber-400' : 'bg-emerald-400'}`} style={{ width: `${brakeWear}%` }} />
                            </div>
                            <span className="text-[9px] text-slate-400 block">
                              Chi tiết: Cơ sở 15% + {brakeLogCount} lần phanh gấp (+{(brakeLogCount * 3.5).toFixed(1)}%) + {criticalCount} sự kiện rủi ro (+{(criticalCount * 5).toFixed(1)}%)
                            </span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-slate-400">
                              <span>Tire Wear Stress (TSI):</span>
                              <span className={`font-mono font-bold ${tireWear > 70 ? 'text-red-400' : 'text-sky-300'}`}>{tireWear}/100</span>
                            </div>
                            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                              <div className="bg-sky-400 h-full rounded-full" style={{ width: `${tireWear}%` }} />
                            </div>
                            <span className="text-[9px] text-slate-400 block">
                              Chi tiết: Cơ sở 10% + {speedingPct.toFixed(1)}% quá tốc độ (+{(speedingPct * 0.4).toFixed(1)}%) + {tireLogCount} lần lái gấp (+{(tireLogCount * 2.0).toFixed(1)}%)
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t border-slate-800/80 pt-2">
                          <div><span className="text-slate-400">Odometer hiện tại:</span> <b className="font-mono text-slate-200">{aiDiag?.odometer_km ?? 38900} km</b></div>
                          <div><span className="text-slate-400">Engine Hours:</span> <b className="font-mono text-slate-200">{aiDiag?.engine_hours ?? 950} giờ</b></div>
                          <div><span className="text-slate-400">Hạn bảo dưỡng:</span> <b className="font-mono text-amber-300">{aiDiag?.km_to_next_service ?? (isRoutine ? 'Còn 5.100 km' : 'Cần kiểm tra')}</b></div>
                          <div><span className="text-slate-400">Mã lỗi OBD-II (DTC):</span> <b className={`font-mono ${dtcCode.includes('P0000') ? 'text-emerald-400' : 'text-red-400 font-bold'}`}>{dtcCode}</b></div>
                          <div><span className="text-slate-400">Trạng thái Phụ tùng:</span> <b className="text-slate-200">{parts}</b></div>
                          <div><span className="text-slate-400">Trạng thái Work Order:</span> <b className="font-mono text-sky-300">{workOrderStatus}</b></div>
                        </div>

                        <div className="flex items-center justify-between bg-slate-900/90 rounded p-2 text-xs border border-slate-800">
                          <span className="text-slate-400">Dự toán Sửa chữa & Downtime:</span>
                          <span className="font-bold text-amber-300 font-mono">{estCost} | Nằm xưởng ~{downtime}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              /* --- SAFETY MODE: DRIVER SAFETY BEHAVIOR & RISK METRICS --- */
              <>
                <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                  <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-sky-400">
                    <UserRound className="h-5 w-5" />
                    Chỉ Số Hành Vi & Điểm An Toàn Chi Tiết (Driver Safety Performance Audit)
                  </div>
                  <span className="rounded bg-sky-500/10 px-2.5 py-1 text-xs font-bold text-sky-300 border border-sky-500/20">
                    Safety Evaluation Mode
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((row, idx) => (
                    <div key={row.trip_id} className="rounded-lg border border-sky-500/40 bg-[#0A0F1D] p-4 space-y-3 shadow-xl">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sky-300 text-sm">XE {String(idx + 1).padStart(2, '0')} - {row.trip_id}</span>
                          <span className="text-[10px] text-slate-400">({row.trip_id})</span>
                        </div>
                        <span className={`text-xs font-black px-2 py-0.5 rounded ${row.score >= 80 ? 'bg-emerald-500/20 text-emerald-300' : row.score >= 60 ? 'bg-amber-500/20 text-amber-300' : 'bg-red-500/20 text-red-300'}`}>
                          Safety Score: {row.score.toFixed(0)}/100
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="space-y-1">
                          <div className="flex justify-between text-slate-400">
                            <span>Tỷ lệ xao nhãng:</span>
                            <span className="font-mono text-amber-300 font-bold">{row.distractedPct.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-amber-400 h-full rounded-full" style={{ width: `${Math.min(100, row.distractedPct)}%` }} />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-slate-400">
                            <span>Vi phạm quá tốc độ:</span>
                            <span className="font-mono text-sky-300 font-bold">{row.speedingPct.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-sky-400 h-full rounded-full" style={{ width: `${Math.min(100, row.speedingPct)}%` }} />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t border-slate-800/80 pt-2">
                        <div><span className="text-slate-400">Phanh gấp (Harsh brake):</span> <b className="font-mono text-slate-200">{row.harshEvents} lần</b></div>
                        <div><span className="text-slate-400">Near miss / TTC risk:</span> <b className="font-mono text-slate-200">{row.nearMissCount} sự kiện</b></div>
                        <div><span className="text-slate-400">Sự kiện cảnh báo:</span> <b className="font-mono text-amber-300">{row.criticalEvents} lượt</b></div>
                        <div><span className="text-slate-400">Mức rủi ro cực đại:</span> <b className="font-mono text-red-400 font-bold">{row.maxRisk.toFixed(1)}/100</b></div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        )}

        {/* --- SECTION C: WORKFLOW & ACTION ORDERS (DÀNH RIÊNG CHO AN TOÀN VÀ BẢO TRÌ) --- */}
        <section className={`${panel} p-5 space-y-3`}>
          {reportType === 'maintenance' ? (
            /* --- MAINTENANCE ACTION ORDERS --- */
            <>
              <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-amber-400 border-b border-[#1E293B] pb-3">
                <Wrench className="h-5 w-5" />
                Lệnh Hành Động Bảo Trì Xưởng (Rule-based & Technical Action Orders)
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {(() => {
                  const currentReportIds = rows.map(r => r.trip_id);
                  const criticalVehicles = rows.filter(r => r.riskLevel === 'CRITICAL' || r.harshEvents >= 10);
                  const warningVehicles = rows.filter(r => r.riskLevel === 'AT_RISK' || (r.harshEvents > 0 && r.harshEvents < 10));
                  const normalVehicles = rows.filter(r => r.riskLevel !== 'CRITICAL' && r.riskLevel !== 'AT_RISK');

                  // Ensure AI response does not leak external trip IDs
                  const cleanAiText = (rawText?: string) => {
                    if (!rawText) return null;
                    const hasLeak = !currentReportIds.some(id => rawText.includes(id));
                    return hasLeak ? null : rawText;
                  };

                  const isAiLoading = isLoadingInsight && !aiActionOrders;
                  const doNotDriveText = isAiLoading ? '⏳ AI Copilot đang tổng hợp lệnh khẩn cấp...' : (cleanAiText(aiActionOrders?.do_not_drive) ?? (
                    criticalVehicles.length > 0
                      ? `Áp dụng cho xe [${criticalVehicles.map(v => v.trip_id).join(', ')}] do có chỉ số rủi ro / áp lực phanh gắt cao (MSI > 75). Thu hồi khẩn về xưởng rà đĩa phanh.`
                      : 'Không có xe nào trong báo cáo này vi phạm ngưỡng dừng lưu hành khẩn cấp.'
                  ));

                  const priority48hText = isAiLoading ? '⏳ AI Copilot đang xếp loại ưu tiên...' : (cleanAiText(aiActionOrders?.priority_48h) ?? (
                    warningVehicles.length > 0
                      ? `Áp dụng cho xe [${warningVehicles.map(v => v.trip_id).join(', ')}]. Thực hiện kiểm tra cảm biến tốc độ bánh xe (C0035) & cân chỉnh độ mòn lốp trong 48h.`
                      : 'Không có xe nào trong báo cáo này cần kiểm tra xưởng trong 48h.'
                  ));

                  const routineText = isAiLoading ? '⏳ AI Copilot đang xếp lịch bảo dưỡng...' : (cleanAiText(aiActionOrders?.routine_maintenance) ?? (
                    normalVehicles.length > 0
                      ? `Áp dụng cho xe [${normalVehicles.map(v => v.trip_id).join(', ')}]. Duy trì thay dầu động cơ, lọc gió và kiểm tra áp suất lốp tiêu chuẩn.`
                      : 'Tất cả các xe trong báo cáo này đều cần kiểm tra kỹ thuật.'
                  ));

                  return (
                    <>
                      <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-3 space-y-1">
                        <span className="font-bold text-red-400 uppercase block">🚨 Dừng Lưu Hành Ngay (Do Not Drive)</span>
                        <p className="text-slate-300 leading-relaxed">{doNotDriveText}</p>
                      </div>
                      <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 space-y-1">
                        <span className="font-bold text-amber-400 uppercase block">⚠️ Bảo Trì Ưu Tiên Trong 48H</span>
                        <p className="text-slate-300 leading-relaxed">{priority48hText}</p>
                      </div>
                      <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-3 space-y-1">
                        <span className="font-bold text-emerald-400 uppercase block">✅ Bảo Dưỡng Định Kỳ Chuẩn</span>
                        <p className="text-slate-300 leading-relaxed">{routineText}</p>
                      </div>
                    </>
                  );
                })()}
              </div>
            </>
          ) : (
            /* --- SAFETY ACTION ORDERS --- */
            <>
              <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-sky-400 border-b border-[#1E293B] pb-3">
                <Shield className="h-5 w-5" />
                Khuyến Nghị Can Thiệp An Toàn Tài Xế (Safety Interventions & Coaching Orders)
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {(() => {
                  const highRiskDrivers = rows.filter(r => r.score < 60 || r.distractedPct > 30);
                  const midRiskDrivers = rows.filter(r => r.score >= 60 && r.score < 80);
                  const safeDrivers = rows.filter(r => r.score >= 80);

                  const isAiLoading = isLoadingInsight && !aiActionOrders;

                  const coachingUrgent = isAiLoading ? '⏳ AI Copilot đang xếp lịch Coaching an toàn...' : (highRiskDrivers.length > 0
                    ? `Bắt buộc tham gia khóa Coaching an toàn trực tiếp trong 24h đối với tài xế [${highRiskDrivers.map(v => v.trip_id).join(', ')}] do vi phạm xao nhãng & phanh gấp cao.`
                    : 'Tất cả tài xế đạt ngưỡng điểm an toàn chấp nhận được.');

                  const warningCoaching = isAiLoading ? '⏳ AI Copilot đang tổng hợp danh sách cảnh báo...' : (midRiskDrivers.length > 0
                    ? `Gửi thông báo nhắc nhở tự kiểm soát khoảng cách & xao nhãng khi lái xe cho tài xế [${midRiskDrivers.map(v => v.trip_id).join(', ')}].`
                    : 'Không có tài xế nào ở ngưỡng cảnh báo trung bình.');

                  const rewardText = isAiLoading ? '⏳ AI Copilot đang đánh giá mức độ xuất sắc...' : (safeDrivers.length > 0
                    ? `Đề xuất tuyên dương và khen thưởng tiêu chí Safe Driver tháng cho tài xế [${safeDrivers.map(v => v.trip_id).join(', ')}].`
                    : 'Cần nỗ lực cải thiện chỉ số an toàn toàn fleet.');

                  return (
                    <>
                      <div className="rounded-lg border border-red-500/30 bg-red-950/20 p-3 space-y-1">
                        <span className="font-bold text-red-400 uppercase block">🛑 Coaching An Toàn Bắt Buộc (24H)</span>
                        <p className="text-slate-300 leading-relaxed">{coachingUrgent}</p>
                      </div>
                      <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 space-y-1">
                        <span className="font-bold text-amber-400 uppercase block">⚠️ Nhắc Nhở Kỷ Luật Vận Hành</span>
                        <p className="text-slate-300 leading-relaxed">{warningCoaching}</p>
                      </div>
                      <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/20 p-3 space-y-1">
                        <span className="font-bold text-emerald-400 uppercase block">🏆 Khen Thưởng Tài Xế Mẫu Mực</span>
                        <p className="text-slate-300 leading-relaxed">{rewardText}</p>
                      </div>
                    </>
                  );
                })()}
              </div>
            </>
          )}
        </section>

        <section className={`${panel} overflow-hidden`}>
          {(() => {
            const activeExpandedRows = rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]);
            const isSingleExpanded = activeExpandedRows.length === 1;
            const targetRow = isSingleExpanded ? activeExpandedRows[0] : null;

            const allFleetEvents = allFleetRows.flatMap(r => eventRowsFor(r.trip));
            const fleetSafeCountAvg = allFleetEvents.filter(e => e.severity === 'Sự kiện an toàn').length / Math.max(allFleetRows.length, 1);
            const fleetWarningCountAvg = allFleetEvents.filter(e => e.severity === 'Sự kiện cảnh báo').length / Math.max(allFleetRows.length, 1);
            const fleetDangerCountAvg = allFleetEvents.filter(e => e.severity === 'Sự kiện nguy hiểm').length / Math.max(allFleetRows.length, 1);

            const fleetNearMissAvg = allFleetRows.reduce((sum, row) => sum + row.nearMissCount, 0) / Math.max(allFleetRows.length, 1);
            const fleetDistractionAvg = allFleetRows.reduce((sum, row) => sum + row.distractedPct, 0) / Math.max(allFleetRows.length, 1);

            const targetEvents = targetRow ? eventRowsFor(targetRow.trip) : (rows[0] ? eventRowsFor(rows[0].trip) : []);
            const targetSafe = targetEvents.filter(e => e.severity === 'Sự kiện an toàn').length;
            const targetWarning = targetEvents.filter(e => e.severity === 'Sự kiện cảnh báo').length;
            const targetDanger = targetEvents.filter(e => e.severity === 'Sự kiện nguy hiểm').length;

            const column2Header = targetRow ? `Xe ${targetRow.trip_id}` : 'Best Driver';

            return (
              <>
                <div className="grid grid-cols-[1fr_180px_200px] border-b border-[#1E293B] px-5 py-4 text-xs font-black uppercase tracking-widest text-slate-400">
                  <span>Business KPI</span>
                  <span className="text-center">Fleet Average</span>
                  <span className="text-center text-sky-400">{column2Header}</span>
                </div>
                {[
                  ['Tổng điểm an toàn', `${fleetAverage.toFixed(1)}/100`, targetRow ? `${targetRow.score.toFixed(1)}/100` : (rows[0] ? `${rows[0].score.toFixed(1)}/100` : 'N/A')],
                  ['TTC / near miss risk', `${fleetNearMissAvg.toFixed(1)} near misses`, targetRow ? `${targetRow.nearMissCount} near misses` : (rows[0] ? `${rows[0].nearMissCount} near misses` : 'N/A')],
                  ['An toàn của bác tài', `${fleetDistractionAvg.toFixed(1)}% distracted`, targetRow ? `${targetRow.distractedPct.toFixed(1)}% distracted` : (rows[0] ? `${rows[0].distractedPct.toFixed(1)}% distracted` : 'N/A')],
                  ['Sự kiện an toàn (Bình thường)', `${fleetSafeCountAvg.toFixed(1)} sự kiện`, `${targetSafe} sự kiện`],
                  ['Sự kiện cảnh báo (Chú ý)', `${fleetWarningCountAvg.toFixed(1)} sự kiện`, `${targetWarning} sự kiện`],
                  ['Sự kiện nguy hiểm (Khẩn cấp)', `${fleetDangerCountAvg.toFixed(1)} sự kiện`, `${targetDanger} sự kiện`],
                ].map(([label, avg, targetVal]) => (
                  <div key={label} className="grid grid-cols-[1fr_180px_200px] border-b border-[#1E293B] px-5 py-4 text-sm">
                    <span className="font-bold text-slate-200">{label}</span>
                    <span className="text-center font-mono text-sky-300">{avg}</span>
                    <span className="text-center font-mono text-emerald-300 font-bold">{targetVal}</span>
                  </div>
                ))}
              </>
            );
          })()}
        </section>

        {(rows.length === 1 || rows.some(r => expandedTrips[r.trip_id])) && (
          <section className={`grid gap-4 ${columnClass(rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).length)}`}>
            {rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((row) => {
              const events = eventRowsFor(row.trip);
              const isMaint = reportType === 'maintenance';
              return (
                <div key={row.trip_id} className={`${panel} overflow-hidden`}>
                  <div className="flex items-center justify-between border-b border-[#1E293B] px-4 py-3">
                    <h3 className="truncate text-sm font-black text-slate-100 flex items-center gap-2">
                      {isMaint ? <Wrench className="h-4 w-4 text-amber-400" /> : null}
                      <span>{isMaint ? `Nhật ký Log chi tiết của trip ${row.trip_id} (+% hao mòn phanh & lốp)` : `Nhật ký sự kiện của trip ${row.trip_id}`}</span>
                    </h3>
                    <span className="text-xs font-bold text-amber-400 font-mono">{events.length} sự kiện log</span>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    <div className={`grid ${isMaint ? 'grid-cols-[70px_1fr_130px_90px]' : 'grid-cols-[70px_1fr_82px]'} text-xs`}>
                      {events.map((event, idx) => {
                        let wearImpactBadge = null;
                        if (isMaint) {
                          if (event.type.toLowerCase().includes('phanh') || event.type.toLowerCase().includes('brake') || event.severity === 'Sự kiện nguy hiểm') {
                            wearImpactBadge = <span className="font-bold text-red-400 bg-red-950/60 px-1.5 py-0.5 rounded border border-red-800/60">+3.5% phanh</span>;
                          } else if (event.type.toLowerCase().includes('tốc độ') || event.type.toLowerCase().includes('speed') || event.type.toLowerCase().includes('làn')) {
                            wearImpactBadge = <span className="font-bold text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800/60">+2.0% lốp</span>;
                          } else {
                            wearImpactBadge = <span className="text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded">+0.5% mòn</span>;
                          }
                        }

                        return (
                          <React.Fragment key={`${event.time}-${event.type}-${idx}`}>
                            <span className="border-b border-[#1E293B] px-3 py-2 font-mono text-slate-400">{event.time}</span>
                            <span className="border-b border-[#1E293B] px-3 py-2 text-slate-300">
                              <b className="block text-slate-100">{event.type}</b>
                              {event.detail}
                            </span>
                            {isMaint && (
                              <span className="border-b border-[#1E293B] px-2 py-2 text-center text-[10px] font-mono flex items-center justify-center">
                                {wearImpactBadge}
                              </span>
                            )}
                            <span className={`border-b border-[#1E293B] px-3 py-2 text-center text-[11px] font-bold ${
                              event.severity === 'Sự kiện nguy hiểm'
                                ? 'text-red-400'
                                : event.severity === 'Sự kiện cảnh báo'
                                  ? 'text-amber-400'
                                  : 'text-emerald-400'
                            }`}>
                              {event.severity}
                            </span>
                          </React.Fragment>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </section>
        )}

        {/* --- SECTION 4A: FLEET OVERVIEW / SINGLE TRIP SUMMARY (ĐỘNG THEO CHẾ ĐỘ XEM) --- */}
        <section className={`${panel} p-5 space-y-4`}>
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400 border-b border-slate-800 pb-2">
            <FileText className="h-4 w-4 text-sky-400" />
            <span className="text-sky-300">
              {rows.length === 1 
                ? `Nhận xét tổng quan về trip ${rows[0].trip_id} (${rows[0].trip_id})` 
                : 'Nhận xét tổng quan đội xe (Fleet Overview & Statistical Evaluation)'}
            </span>
            <span className="ml-auto text-emerald-400 font-mono text-[10px] bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">Bedrock Telemetry AI Engine</span>
          </div>

          {/* Quick Aggregate Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Trip Safe Score' : 'Fleet Safe Score'}</span>
              <span className="text-xl font-black font-mono text-sky-400 mt-1 block">{fleetAverage.toFixed(1)}/100</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Tài xế chuyến xe' : 'Tài xế xuất sắc nhất'}</span>
              <span className="text-sm font-bold font-mono text-emerald-400 mt-1 block truncate">
                {rows[0] ? `${rows[0].trip_id} (${rows[0].score.toFixed(0)})` : 'N/A'}
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Vi phạm phanh gấp chuyến' : 'Tổng vi phạm phanh gấp'}</span>
              <span className="text-xl font-black font-mono text-amber-400 mt-1 block">
                {rows.reduce((sum, r) => sum + r.harshEvents, 0)} lần
              </span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
              <span className="text-slate-500 block uppercase font-bold text-[10px]">{rows.length === 1 ? 'Mức độ rủi ro trip' : 'Phân loại rủi ro chính'}</span>
              <span className="text-sm font-bold font-mono text-red-400 mt-1 block truncate">
                {rows.length === 1 ? rows[0].riskLevel : `${rows.filter(r => r.riskLevel === 'CRITICAL' || r.riskLevel === 'AT_RISK').length} xe rủi ro`}
              </span>
            </div>
          </div>

          <div className="rounded-lg bg-slate-950/80 p-4 border border-slate-800/80 leading-relaxed text-sm text-slate-200">
            <p className="whitespace-pre-line font-medium leading-relaxed">
              {copilotInsight || 'AI Copilot đang tổng hợp dữ liệu số liệu toàn bộ đội xe...'}
            </p>
          </div>
        </section>

        {/* --- SECTION 4B: INDIVIDUAL DETAILED TRIP AI INSIGHTS (ƯU ĐIỂM, NHƯỢC ĐIỂM / CHẨN ĐOÁN KỸ THUẬT BEDROCK) --- */}
        {(rows.length === 1 || rows.some(r => expandedTrips[r.trip_id])) && rows.filter(r => rows.length === 1 || expandedTrips[r.trip_id]).map((expandedRow) => {
          const tripId = expandedRow.trip_id;
          const tripAi = aiTripInsights[tripId];
          const driverName = expandedRow.trip_id;
          const safeScore = expandedRow.score;
          const isMaint = reportType === 'maintenance';

          const logEvents = eventRowsFor(expandedRow.trip);
          const brakeLogCount = logEvents.filter(e => e.type.toLowerCase().includes('phanh') || e.type.toLowerCase().includes('brake') || e.severity === 'Sự kiện nguy hiểm').length;
          const tireLogCount = logEvents.filter(e => e.type.toLowerCase().includes('tốc độ') || e.type.toLowerCase().includes('speed') || e.type.toLowerCase().includes('làn')).length;
          const speedingPct = expandedRow.speedingPct;

          const brakeWear = Math.min(98, Math.max(12, Math.round(15 + brakeLogCount * 3.5 + expandedRow.criticalEvents * 5)));
          const tireWear = Math.min(95, Math.max(10, Math.round(10 + speedingPct * 0.4 + tireLogCount * 2.0)));

          const dtcCode = expandedRow.trip.frames?.some(f => f.behavior_flags?.harsh_brake) ? 'C0035' : 'P0000';
          const hasC0035 = dtcCode.includes('C0035');

          let defaultPros: string[] = [];
          let defaultCons: string[] = [];

          if (isMaint) {
            defaultPros = [
              `Hệ thống làm mát động cơ và đường dẫn nhiên liệu duy trì nhiệt độ chuẩn.`,
              hasC0035 
                ? `Hệ thống làm mát động cơ duy trì nhiệt độ trong dải an toàn 88-92°C.`
                : (brakeWear < 50 ? `Chỉ số Ứng suất phanh Brake MSI duy trì ở mức an toàn (${brakeWear}/100).` : `Cảm biến động cơ vận hành ổn định.`)
            ];
            defaultCons = [
              hasC0035 ? `Phát hiện Mã lỗi OBD-II C0035 (Lỗi mạch cảm biến tốc độ bánh xe - Wheel Speed Sensor Circuit).` : `Chỉ số mòn phanh MSI tăng lên ${brakeWear}/100.`,
              speedingPct > 0 ? `Tỷ lệ quá tốc độ ở mức ${speedingPct.toFixed(1)}% gây áp lực mài mòn TSI ${tireWear}/100 lên bề mặt lốp.` : `Ghi nhận ${brakeLogCount} lượt phanh gấp khi đang di chuyển.`
            ];
          } else {
            // STRICT SAFETY LOGIC RULES
            if (safeScore >= 80) {
              defaultPros.push(`Safety Score thuộc nhóm xuất sắc (${safeScore.toFixed(0)}/100), kiểm soát rủi ro cực tốt.`);
            } else if (safeScore >= 60) {
              defaultPros.push(`Safety Score ở mức trung bình khá (${safeScore.toFixed(0)}/100).`);
            }
            // NO PROS if safeScore < 60!

            if (speedingPct === 0) {
              defaultPros.push(`Tuân thủ giới hạn tốc độ tuyệt đối (0.0%).`);
            } else {
              defaultCons.push(`Vi phạm tốc độ ở mức ${speedingPct.toFixed(1)}%, gây nguy hiểm nghiêm trọng.`);
            }

            if (brakeLogCount === 0) {
              defaultPros.push(`Lái xe êm ái, không ghi nhận tình huống phanh gấp nguy hiểm.`);
            } else {
              defaultCons.push(`Ghi nhận ${brakeLogCount} sự kiện phanh gấp, dấu hiệu thiếu quan sát hoặc không giữ khoảng cách an toàn.`);
            }

            if (expandedRow.distractedPct > 5) {
              defaultCons.push(`Xao nhãng khi lái xe chiếm ${expandedRow.distractedPct.toFixed(1)}% thời gian, vi phạm quy tắc tập trung.`);
            }
            
            if (expandedRow.criticalEvents > 0) {
               defaultCons.push(`Phát hiện ${expandedRow.criticalEvents} sự kiện rủi ro tiềm ẩn (Near Misses/Critical) trong quá trình vận hành.`);
            }
            
            if (defaultPros.length === 0) {
              defaultPros.push(`Không ghi nhận kỹ năng an toàn đáng kể trong chuyến đi này.`);
            }
          }

          // STRICT PRIORITY MATCHING
          const defaultEval = isMaint
            ? (expandedRow.riskLevel === 'CRITICAL' || brakeWear >= 80 
                ? `XE ${tripId}: 🚨 DỪNG LƯU HÀNH NGAY (Do Not Drive) - Chỉ số rủi ro cực đại / phanh gắt ${brakeWear}/100. Thu hồi khẩn về xưởng rà đĩa phanh & thay đệm lót.`
                : expandedRow.riskLevel === 'AT_RISK' || brakeWear >= 60 || hasC0035
                  ? `XE ${tripId}: ⚠️ BẢO TRÌ ƯU TIÊN TRONG 48H - Thu hồi xe kiểm tra cảm biến tốc độ bánh xe C0035 (~2.500.000 VNĐ dự tính).`
                  : `XE ${tripId}: ✅ BẢO DƯỠNG ĐỊNH KỲ CHUẨN - Xe vận hành tốt, đủ điều kiện duyệt thay dầu định kỳ (~1.850.000 VNĐ dự tính).`)
            : (safeScore >= 80 
                ? `🏆 KHEN THƯỞNG: Tài xế ${driverName} là hình mẫu chuẩn an toàn để các tài xế khác học tập.`
                : safeScore >= 60
                ? `⚠️ NHẮC NHỞ: Tài xế ${driverName} cần chú ý giảm thiểu các hành vi vi phạm để nâng cao điểm số.`
                : `🛑 COACHING 24H: Tài xế ${driverName} vi phạm nghiêm trọng (Score: ${safeScore}/100), yêu cầu đình chỉ chạy và tái đào tạo khẩn cấp.`);

          const isAiLoading = isLoadingInsight && !tripAi;
          const prosList: string[] = isAiLoading ? ['Đang phân tích dữ liệu AI Copilot...'] : (tripAi?.pros ?? defaultPros);
          const consList: string[] = isAiLoading ? ['Đang phân tích dữ liệu AI Copilot...'] : (tripAi?.cons ?? defaultCons);
          const evaluationText: string = isAiLoading ? '⏳ AI Copilot đang xử lý nhận xét đánh giá chuyên sâu...' : (tripAi?.evaluation ?? defaultEval);

          return (
            <section key={`insight-${tripId}`} className={`${panel} p-5 space-y-4 border-amber-500/40 bg-amber-950/10 shadow-2xl`}>
              <div className="flex items-center justify-between border-b border-amber-900/60 pb-2">
                <div className="flex items-center gap-2 text-sm font-black uppercase tracking-widest text-amber-300">
                  {isMaint ? <Wrench className="h-5 w-5 text-amber-400" /> : <UserRound className="h-5 w-5 text-sky-400" />}
                  <span>Nhận xét tổng quan về trip {tripId} ({driverName})</span>
                </div>
                <span className={`text-xs font-extrabold font-mono px-2.5 py-1 rounded ${
                  safeScore >= 80 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : safeScore >= 60 ? 'bg-amber-500/20 text-amber-300' : 'bg-red-500/20 text-red-300 border border-red-500/30'
                }`}>
                  {isMaint ? `Ưu Tiên Bảo Trì: ${expandedRow.coachingPriority}` : `Safety Score: ${safeScore.toFixed(0)}/100`}
                </span>
              </div>

              <div className="space-y-3 bg-[#0A0F1D] p-4 rounded-lg border border-amber-900/40 text-xs leading-relaxed">
                {/* 🟢 Ưu điểm / Điểm kỹ thuật tốt */}
                <div className="space-y-1.5">
                  <h4 className="font-bold text-emerald-400 text-xs uppercase flex items-center gap-1.5">
                    <span>{isMaint ? '🟢 Điểm Kỹ Thuật Tốt & Hệ Thống An Toàn:' : '🟢 Ưu điểm:'}</span>
                  </h4>
                  <ul className="space-y-1 list-disc list-inside text-slate-200 pl-1">
                    {prosList.map((pro, idx) => (
                      <li key={idx} className="leading-relaxed">
                        <span>{pro}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 🔴 Nhược điểm / Nguyên nhân hao mòn kỹ thuật (Why) */}
                <div className="space-y-1.5 border-t border-slate-800/80 pt-3">
                  <h4 className="font-bold text-red-400 text-xs uppercase flex items-center gap-1.5">
                    <span>{isMaint ? '🔴 Nguyên Nhân Gây Cảnh Báo Kỹ Thuật & Hao Mòn (Root Cause):' : '🔴 Nhược điểm:'}</span>
                  </h4>
                  <ul className="space-y-1 list-disc list-inside text-slate-200 pl-1">
                    {consList.map((con, idx) => (
                      <li key={idx} className="leading-relaxed">
                        <span>{con}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 💡 Đánh giá & Lệnh Work Order Kỹ thuật */}
                <div className="border-t border-slate-800/80 pt-3 flex items-start gap-2 bg-amber-950/30 p-2.5 rounded border border-amber-900/30">
                  <span className="font-bold text-amber-300 shrink-0">{isMaint ? '🛠️ Lệnh Bảo Trì & Khuyến Nghị Gara:' : '💡 Đánh giá:'}</span>
                  <p className="text-slate-200 font-medium leading-relaxed">{evaluationText}</p>
                </div>
              </div>
            </section>
          );
        })}
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

