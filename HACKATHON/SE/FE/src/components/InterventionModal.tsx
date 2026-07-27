import React, { useState } from 'react';
import { X, Volume2, ShieldAlert, CheckCircle2, PhoneCall, Radio } from 'lucide-react';
import { TripData } from '../types';

interface InterventionModalProps {
  vehicle: TripData | null;
  isOpen: boolean;
  onClose: () => void;
}

export const InterventionModal: React.FC<InterventionModalProps> = ({ vehicle, isOpen, onClose }) => {
  const [sentAlert, setSentAlert] = useState<string | null>(null);

  if (!isOpen || !vehicle) return null;

  const lastFrame = vehicle.frames?.[vehicle.frames.length - 1];

  const handleSendAction = (actionTitle: string) => {
    setSentAlert(actionTitle);
    setTimeout(() => {
      setSentAlert(null);
      onClose();
    }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-[#0B0F19] border border-red-500/60 rounded-2xl max-w-md w-full p-6 text-white space-y-5 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-white rounded-lg"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-red-950 border border-red-600 flex items-center justify-center text-red-500">
            <ShieldAlert className="w-5 h-5 animate-bounce" />
          </div>
          <div>
            <h2 className="text-base font-extrabold text-white">
              Lệnh Can Thiệp Khẩn Cấp — {vehicle.trip_id}
            </h2>
            <p className="text-xs text-slate-400">
              Trạng thái: <span className="uppercase text-red-300 font-bold">{lastFrame?.driver?.state || 'UNKNOWN'}</span> • Điểm tỉnh táo: {Math.round((lastFrame?.driver?.alertness_score || 0) * 100)}%
            </p>
            <div className="mt-2 bg-[#1A1114] border border-red-500/30 p-2 rounded text-[10px] font-mono text-slate-300">
              <span className="block text-red-400 font-bold mb-1">AI RISK REASONING (US-01):</span>
              Base Risk ({lastFrame?.risk?.base_risk || 0}) × Driver Factor ({lastFrame?.risk?.driver_factor || 1}) = Final Risk Score: <span className="font-bold text-red-400">{lastFrame?.risk?.final_risk_score || 0}</span>
            </div>
          </div>
        </div>

        {sentAlert ? (
          <div className="bg-emerald-950/80 border border-emerald-500/50 rounded-xl p-4 flex flex-col items-center justify-center text-center space-y-2 py-8">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 animate-bounce" />
            <h3 className="text-sm font-bold text-white">Đã gửi thành công!</h3>
            <p className="text-xs text-emerald-200">{sentAlert}</p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-xs text-slate-300 leading-relaxed">
              Chọn phương án can thiệp thích hợp cho phương tiện <span className="font-bold text-white">{vehicle.trip_id}</span> đang di chuyển ở vận tốc <span className="font-bold text-red-400">{lastFrame?.ego?.speed_kmh || 0} km/h</span>:
            </p>

            <button
              onClick={() => handleSendAction('Cảnh báo âm thanh cabin: "Phát hiện buồn ngủ! Hãy dừng xe nghỉ ngay!"')}
              className="w-full p-3 bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded-xl flex items-center justify-between transition-colors shadow-lg shadow-red-900/30"
            >
              <div className="flex items-center gap-2.5">
                <Volume2 className="w-4 h-4" />
                <span>Phát chuông báo động Cabin khẩn cấp</span>
              </div>
              <Radio className="w-4 h-4 text-amber-300 animate-pulse" />
            </button>

            <button
              onClick={() => handleSendAction('Yêu cầu dừng nghỉ 30 phút tại Trạm dừng tiếp theo')}
              className="w-full p-3 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] text-slate-200 font-bold text-xs rounded-xl flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <Radio className="w-4 h-4 text-sky-400" />
                <span>Gửi lệnh dừng xe nghỉ 30 phút</span>
              </div>
              <span className="text-[10px] text-sky-400 uppercase font-mono">Đề xuất</span>
            </button>

            <button
              onClick={() => handleSendAction('Cuộc gọi kết nối trực tiếp với Trung tâm Điều hành')}
              className="w-full p-3 bg-[#111827] hover:bg-[#1F2937] border border-[#1F2937] text-slate-200 font-bold text-xs rounded-xl flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <PhoneCall className="w-4 h-4 text-emerald-400" />
                <span>Gọi điện trực tiếp cho tài xế</span>
              </div>
              <span className="text-[10px] text-emerald-400 uppercase font-mono">Voice Call</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
