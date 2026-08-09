import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, ArrowRight, Lightbulb, Bot, FileText, BarChart3, Wrench } from 'lucide-react';
import { ChatMessage, TripData } from '../types';

interface AICopilotDrawerProps {
  isOpen: boolean;
  vehicles: TripData[];
  onClose: () => void;
  onNavigateToTrip?: () => void;
  onSendBreakSchedule?: () => void;
}

type CopilotReportType = 'compare' | 'maintenance' | 'safety';

export const AICopilotDrawer: React.FC<AICopilotDrawerProps> = ({
  isOpen,
  vehicles,
  onClose,
  onNavigateToTrip,
  onSendBreakSchedule,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [isOpen, messages]);

  if (!isOpen) return null;

  const openCopilotReport = (type: CopilotReportType, tripIds?: string[]) => {
    const fallbackCount = type === 'compare' ? 2 : vehicles.length;
    const selectedTripIds = tripIds?.length
      ? tripIds
      : vehicles.slice(0, Math.max(1, fallbackCount)).map((vehicle) => vehicle.trip_id);
    const params = new URLSearchParams({
      view: 'copilot-report',
      type,
      trip_ids: selectedTripIds.join(','),
    });
    window.open(`${window.location.origin}${window.location.pathname}?${params.toString()}`, '_blank', 'noopener,noreferrer');
  };

  const copilotTripContext = vehicles
    .filter((vehicle) => vehicle.runtime_status === 'completed')
    .map((vehicle) => ({
      trip_id: vehicle.trip_id,
      runtime_status: vehicle.runtime_status,
      metadata: vehicle.metadata,
      driver_summary: vehicle.driver_summary,
      trip_aggregate: vehicle.trip_aggregate,
      frames: vehicle.frames,
    }));

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/copilot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          chatHistory: messages.map((m) => ({ sender: m.sender, text: m.text || m.cardData?.details || '' })),
          vehicles: copilotTripContext,
        }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Copilot HTTP ${response.status}`);

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: data.reply || '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        cardType: data.cardType,
        cardData: data.cardData,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Copilot request error:', err);
      const fallbackMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: 'Copilot Backend hiện không khả dụng. Không có dữ liệu giả lập được hiển thị.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] md:w-[480px] max-w-full bg-[#0A0E17] border-l border-[#1E293B] shadow-2xl flex flex-col text-white transition-all animate-in slide-in-from-right duration-300 overflow-x-hidden">
      {/* Drawer Header */}
      <div className="p-4 border-b border-[#1E293B] flex items-center justify-between bg-[#0F172A]/80 backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-600/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
            <Sparkles className="w-4 h-4 text-sky-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-1.5">
              Fleet AI Copilot
            </h2>
            <p className="text-[11px] text-slate-400">Đang phân tích dữ liệu trip của bạn</p>
          </div>
        </div>

        <button
          id="btn-close-copilot"
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4 font-sans text-xs">
        {messages.map((msg) => {
          if (msg.sender === 'user') {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-[85%] bg-sky-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 shadow-md break-words">
                  <p className="text-xs leading-relaxed font-medium break-words">{msg.text}</p>
                  <span className="text-[9px] text-sky-200 block text-right mt-1 opacity-80">{msg.timestamp}</span>
                </div>
              </div>
            );
          }

          // Assistant Message Cards
          return (
            <div key={msg.id} className="flex gap-2.5 items-start max-w-full overflow-hidden">
              <div className="w-7 h-7 rounded-full bg-indigo-950 border border-indigo-700/60 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>

              <div className="flex-1 min-w-0 space-y-3 overflow-hidden">
                {/* 1. Trip Risk Card */}
                {msg.cardType === 'DRI_RISK' && msg.cardData && (
                  <div className="bg-[#111A2E] border border-sky-900/60 rounded-xl p-4 space-y-3 shadow-lg break-words overflow-hidden">
                    <div className="flex items-center gap-1.5 text-sky-400 text-[10px] font-bold uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>FLEET COPILOT</span>
                    </div>

                    <h3 className="text-sm font-extrabold text-white leading-snug break-words">
                      {msg.cardData.trip_id || 'Trip đang chọn'} đang có rủi ro cao nhất — Ranking Score <span className="text-amber-400 font-mono">{msg.cardData.score}/100</span>
                    </h3>

                    <div className="flex flex-wrap gap-1.5">
                      <span className="px-2 py-0.5 rounded bg-red-950/80 border border-red-800/50 text-red-300 font-semibold text-[10px]">
                        {msg.cardData.microsleepCount} lần vi ngủ
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold text-[10px]">
                        TTC thấp nhất: {msg.cardData.lowestTtc}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold text-[10px]">
                        Khung giờ: {msg.cardData.timeSlot}
                      </span>
                    </div>

                    <p className="text-slate-300 text-xs leading-relaxed break-words">
                      {msg.cardData.details}
                    </p>

                    {onNavigateToTrip && (
                      <button
                        onClick={onNavigateToTrip}
                        className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-bold text-xs pt-1 transition-colors"
                      >
                        <span>View Full Trip</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                )}

                {/* 2. Recommendation Card */}
                {msg.cardType === 'RECOMMENDATION' && msg.cardData && (
                  <div className="bg-[#0B1528] border border-amber-900/60 rounded-xl p-4 space-y-3 shadow-lg break-words overflow-hidden">
                    <div className="flex items-center gap-1.5 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
                      <Lightbulb className="w-3.5 h-3.5" />
                      <span>ĐỀ XUẤT HÀNH ĐỘNG</span>
                    </div>
                    <h3 className="text-sm font-extrabold text-white leading-snug break-words">{msg.cardData.title}</h3>
                    <p className="text-slate-300 text-xs leading-relaxed break-words">{msg.cardData.details}</p>

                    {onSendBreakSchedule && (
                      <button
                        onClick={onSendBreakSchedule}
                        className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-lg transition-colors shadow-md text-center"
                      >
                        {msg.cardData.actionText || 'Gửi lịch nghỉ đề xuất'}
                      </button>
                    )}
                  </div>
                )}

                {/* 3. Copilot Report Card */}
                {msg.cardType === 'COMPARISON' && msg.cardData && (
                  <div className={`rounded-xl p-4 space-y-3 shadow-lg border break-words overflow-hidden ${
                    msg.cardData.reportType === 'maintenance' 
                      ? 'bg-[#1A110B] border-amber-600/50' 
                      : 'bg-[#0B1220] border-sky-900/60'
                  }`}>
                    <div className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider ${
                      msg.cardData.reportType === 'maintenance' ? 'text-amber-400' : 'text-sky-400'
                    }`}>
                      {msg.cardData.reportType === 'maintenance' ? <Wrench className="w-3.5 h-3.5" /> : <BarChart3 className="w-3.5 h-3.5" />}
                      <span>{msg.cardData.reportType === 'maintenance' ? 'BÁO CÁO ƯU TIÊN KIỂM TRA TRIP' : 'BẢNG XẾP HẠNG AN TOÀN TRIP'}</span>
                    </div>
                    <h3 className="text-sm font-extrabold text-white leading-snug break-words">{msg.cardData.title}</h3>
                    <p className="text-slate-300 text-xs leading-relaxed break-words">{msg.cardData.details}</p>

                    {/* Ranking list */}
                    {msg.cardData.rankedDrivers && msg.cardData.rankedDrivers.length > 0 && (
                      <div className="space-y-1.5 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 overflow-hidden">
                        <div className="flex items-center justify-between text-[10px] font-bold uppercase text-amber-400 border-b border-slate-900 pb-1.5 mb-1 gap-1">
                          <span className="truncate">{msg.cardData.sortRule || (msg.cardData.reportType === 'maintenance' ? 'Sắp xếp: Ưu tiên kiểm tra trip TỪ CAO ➔ THẤP' : 'Xếp hạng theo điểm an toàn Ranking Score TỪ CAO ➔ THẤP')}</span>
                          <span className="font-mono text-slate-400 shrink-0">({msg.cardData.rankedDrivers.length} trips)</span>
                        </div>
                        {msg.cardData.rankedDrivers.map((d: any, rankIdx: number) => (
                          <div 
                            key={d.trip_id}
                            onClick={() => openCopilotReport(msg.cardData.reportType, [d.trip_id])}
                            className="flex items-center justify-between text-xs p-2 rounded border border-slate-800/80 bg-slate-900/60 hover:bg-sky-950/40 hover:border-sky-500/50 cursor-pointer transition-all group gap-1 min-w-0"
                          >
                            <div className="flex items-center gap-2 truncate min-w-0">
                              <span className={`font-bold font-mono px-1.5 py-0.5 rounded text-[10px] shrink-0 ${
                                msg.cardData.reportType === 'maintenance'
                                  ? (d.maintenancePriority === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border border-red-500/40' : d.maintenancePriority === 'HIGH' ? 'bg-orange-500/20 text-orange-300' : 'bg-emerald-500/20 text-emerald-300')
                                  : (d.safeScore < 60 ? 'bg-red-500/20 text-red-300 border border-red-500/40' : d.safeScore < 80 ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300')
                              }`}>
                                #{rankIdx + 1}
                              </span>
                              <div className="truncate min-w-0">
                                <span className="font-bold text-slate-100 group-hover:text-sky-300 block truncate">{d.trip_id}</span>
                                <span className="text-[10px] font-mono text-slate-400 block truncate">
                                  {d.riskLevel || d.trip_id || 'N/A'}
                                  {typeof d.maxRisk === 'number' ? ` • Maximum Risk Score ${d.maxRisk}/100` : ''}
                                  {d.dtcCode && d.dtcCode !== 'N/A' ? ` • DTC ${d.dtcCode}` : ''}
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {msg.cardData.reportType === 'maintenance' ? (
                                <span className={`font-mono text-[10px] font-extrabold px-1.5 py-0.5 rounded ${
                                  d.maintenancePriority === 'INSPECT' ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-slate-800 text-slate-300'
                                }`}>
                                  {d.maintenancePriority || 'ROUTINE'}
                                </span>
                              ) : (
                                <span className={`font-mono font-extrabold ${
                                  d.safeScore >= 80 ? 'text-emerald-400' : d.safeScore >= 60 ? 'text-amber-400' : 'text-red-400'
                                }`}>
                                  {d.safeScore}/100
                                </span>
                              )}
                              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-sky-400 group-hover:translate-x-0.5 transition-all" />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <button
                      onClick={() => openCopilotReport(msg.cardData.reportType, msg.cardData.tripIds)}
                      className="flex w-full items-center justify-center gap-2 rounded-lg bg-sky-600 px-3 py-2 text-xs font-bold text-white hover:bg-sky-500 transition-all shadow-md active:scale-98"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Xem báo cáo tổng hợp toàn bộ ({msg.cardData.tripIds?.length ?? 0} trips)
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}

                {/* Plain Text Message Response */}
                {msg.text && (
                  <div className="bg-[#111827] border border-[#1F2937] text-slate-200 rounded-2xl rounded-tl-none p-3.5 leading-relaxed shadow-sm whitespace-pre-wrap">
                    {msg.text}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-2 text-slate-400 text-xs pl-9">
            <Sparkles className="w-4 h-4 text-sky-400 animate-spin" />
            <span>AI đang phân tích telemetry...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Suggestion Chips */}
      <div className="p-2 px-4 bg-[#0B0F19] border-t border-[#1E293B] flex items-center gap-2 overflow-x-auto text-[11px] no-scrollbar">
        <button
          onClick={() => handleSendMessage(`So sánh 2 trip ${vehicles.slice(0, 2).map((vehicle) => vehicle.trip_id).join(' và ')}`)}
          className="px-2.5 py-1 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] rounded-full text-slate-300 whitespace-nowrap transition-colors"
        >
          So sánh 2 trip
        </button>
        <button
          onClick={() => handleSendMessage('Trip nào cần kiểm tra?')}
          className="px-2.5 py-1 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] rounded-full text-slate-300 whitespace-nowrap transition-colors"
        >
          Báo cáo kiểm tra trip
        </button>
        <button
          onClick={() => handleSendMessage('Báo cáo an toàn tuần này')}
          className="px-2.5 py-1 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] rounded-full text-slate-300 whitespace-nowrap transition-colors"
        >
          Báo cáo an toàn
        </button>
      </div>

      {/* Message Input Form */}
      <div className="p-3 border-t border-[#1E293B] bg-[#0B0F19]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="relative flex items-center"
        >
          <input
            id="copilot-input-field"
            type="text"
            placeholder="✨ Hỏi tiếp về dữ liệu trip của bạn..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="w-full bg-[#111827] border border-[#1F2937] focus:border-sky-500 text-slate-200 text-xs rounded-xl pl-3 pr-10 py-2.5 outline-none transition-all placeholder-slate-500"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="absolute right-2 p-1.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white rounded-lg transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
