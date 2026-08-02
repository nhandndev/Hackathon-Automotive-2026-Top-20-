import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, ArrowRight, Lightbulb, Clock, ShieldAlert, Bot, User } from 'lucide-react';
import { ChatMessage } from '../types';

interface AICopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToTrip?: () => void;
  onSendBreakSchedule?: () => void;
}

export const AICopilotDrawer: React.FC<AICopilotDrawerProps> = ({
  isOpen,
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
        }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Copilot HTTP ${response.status}`);

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: data.reply || 'Đã nhận yêu cầu.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
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
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] md:w-[480px] bg-[#0A0E17] border-l border-[#1E293B] shadow-2xl flex flex-col text-white transition-all animate-in slide-in-from-right duration-300">
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
            <p className="text-[11px] text-slate-400">Đang phân tích dữ liệu đội xe của bạn</p>
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
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {messages.map((msg) => {
          if (msg.sender === 'user') {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-[85%] bg-sky-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 shadow-md">
                  <p className="text-xs leading-relaxed font-medium">{msg.text}</p>
                  <span className="text-[9px] text-sky-200 block text-right mt-1 opacity-80">{msg.timestamp}</span>
                </div>
              </div>
            );
          }

          // Assistant Message Cards
          return (
            <div key={msg.id} className="flex gap-2.5 items-start">
              <div className="w-7 h-7 rounded-full bg-indigo-950 border border-indigo-700/60 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>

              <div className="flex-1 space-y-3">
                {/* 1. Driver Risk Card */}
                {msg.cardType === 'DRI_RISK' && msg.cardData && (
                  <div className="bg-[#111A2E] border border-sky-900/60 rounded-xl p-4 space-y-3 shadow-lg">
                    <div className="flex items-center gap-1.5 text-sky-400 text-[10px] font-bold uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>FLEET COPILOT</span>
                    </div>

                    <h3 className="text-sm font-extrabold text-white leading-snug">
                      {msg.cardData.driverName} đang có rủi ro cao nhất — Safe Score <span className="text-amber-400 font-mono">{msg.cardData.score}/100</span>
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

                    <p className="text-slate-300 text-xs leading-relaxed">
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
                  <div className="bg-[#1A150B] border border-amber-600/40 rounded-xl p-4 space-y-3 shadow-lg">
                    <div className="flex items-center gap-1.5 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
                      <Lightbulb className="w-3.5 h-3.5" />
                      <span>KHUYẾN NGHỊ</span>
                    </div>

                    <p className="text-slate-200 text-xs leading-relaxed font-medium">
                      {msg.cardData.message}
                    </p>

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
          onClick={() => handleSendMessage('So sánh 2 tài xế')}
          className="px-2.5 py-1 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] rounded-full text-slate-300 whitespace-nowrap transition-colors"
        >
          So sánh 2 tài xế
        </button>
        <button
          onClick={() => handleSendMessage('Xe nào cần bảo trì?')}
          className="px-2.5 py-1 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] rounded-full text-slate-300 whitespace-nowrap transition-colors"
        >
          Xe nào cần bảo trì?
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
            placeholder="✨ Hỏi tiếp về đội xe của bạn..."
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
