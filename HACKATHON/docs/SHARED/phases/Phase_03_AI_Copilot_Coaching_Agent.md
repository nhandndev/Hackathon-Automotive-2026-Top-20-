# PHASE 3: AI FLEET COPILOT AGENT & GENAI COACHING (TRỢ LÝ THÔNG MINH)

---

## 1. MỤC TIÊU VÀ BÀI TOÁN GIAO THỰC CỦA PHASE 3

### 1.1 Mục tiêu của Phase 3 (Cho User & AI)
- **Cho User (Fleet Manager)**: Sở hữu một Trợ lý AI Copilot giao tiếp bằng Tiếng Việt tự nhiên. Thay vì tốn hàng giờ tra cứu báo cáo Excel hay soi video, Manager chỉ cần hỏi *"Tài xế nào nguy hiểm nhất hôm nay?"* để nhận ngay câu trả lời phân tích chuyên sâu kèm khuyến nghị hành động.
- **Cho AI (Coding Assistant / Developer)**: Cung cấp kiến trúc LLM Gateway Router (FastAPI) tích hợp với dữ liệu Challenge 1, 2, 3 và mã nguồn UI Chatbot Box để xây dựng widget giao tiếp phản hồi trong 3 giây.

### 1.2 Bài toán thực tế Phase 3 giải quyết
Bài toán "Data Rich, Insight Poor" (Bội bội dữ liệu nhưng thiếu thông tin chi tiết). Phase 3 sử dụng GenAI để **chuyển đổi dữ liệu số kỹ thuật thô thành thông tin diễn giải tự nhiên (Risk Reasoning)** và đề xuất bài học đào tạo tài xế dựa trên bằng chứng (Evidence-Based Coaching).

---

## 2. KIẾN TRÚC TƯƠNG TÁC AI COPILOT & GENAI REASONING

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    USER QUERY (Tiếng Việt Tự Nhiên)                    │
│      "Tài xế nào đang có rủi ro cao nhất hôm nay và tôi nên làm gì?"    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               AI COPILOT AGENT ENGINE (FastAPI Gateway)                 │
│  - NL2Query Router / GenAI Prompt Fusion                                │
│  - Trích xuất dữ liệu Challenge 1 (DMS) + Challenge 2 (Telemetry/TTC)   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    COPILOT RESPONSE & ACTION BUTTONS                    │
│  - Text Answer: "Tài xế A (VH-04) rủi ro cao nhất: Safe Score 42/100..." │
│  - Action Buttons: [Gửi lịch nghỉ đề xuất] [Xem Radar Chart So Sánh]    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CODE IMPLEMENTATION SPEC (DÀNH CHO AI / DEVELOPER)

### 3.1 Backend LLM Agent Router (`backend/app/modules/coaching/copilot_router.py`)

```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ChatQueryPayload(BaseModel):
    query: str
    trip_id: Optional[str] = "T01d"

class ChatResponsePayload(BaseModel):
    answer: str
    recommended_action: str
    action_type: str  # SCHEDULE_REST, VIEW_TRIP, COMPARE_DRIVERS

@router.post("/api/v1/copilot/chat", response_model=ChatResponsePayload)
async def copilot_chat_endpoint(payload: ChatQueryPayload):
    query_text = payload.query.lower()
    
    # Engine Xử lý Truy vấn NL2Query & GenAI Reasoning Rule-base Fallback
    if any(k in query_text for k in ["rủi ro", "nguy hiểm", "tài xế nào"]):
        return ChatResponsePayload(
            answer="Tài xế A (Xe VH-04) đang có rủi ro cao nhất hôm nay với Safe Score 42/100. Lý do: Có 2 khoảnh khắc vi ngủ (microsleep) trong khung giờ 2h-4h sáng và TTC va chạm phanh gấp thấp nhất 1.2s.",
            recommended_action="Gửi lịch nghỉ đề xuất cho Tài xế A",
            action_type="SCHEDULE_REST"
        )
    elif any(k in query_text for k in ["so sánh", "ai lái tốt hơn"]):
        return ChatResponsePayload(
            answer="So sánh Tài xế A vs Tài xế B: Tài xế A có tần suất vi phạm phanh gấp và vi ngủ cao gấp 3 lần. Tài xế B vận hành an toàn hơn với TTC trung bình 2.9s.",
            recommended_action="Xem Radar Chart Telemetry Comparison",
            action_type="COMPARE_DRIVERS"
        )
    else:
        return ChatResponsePayload(
            answer="Đội xe hiện có 12 phương tiện đang hoạt động. Hệ thống ghi nhận 1 xe rơi vào vùng rủi ro (Risk Zone). Bạn có muốn kiểm tra danh sách vi phạm?",
            recommended_action="Xem Chi tiết Fleet Risk Zone",
            action_type="VIEW_TRIP"
        )
```

### 3.2 Frontend Floating Chatbot Widget (`frontend/src/features/insurance-report/CoachingChatbotBox.jsx`)

```jsx
import React, { useState } from 'react';

export const CoachingChatbotBox = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Xin chào! Tôi là Fleet AI Copilot. Bạn cần hỗ trợ phân tích dữ liệu đội xe nào hôm nay?' }
  ]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    const userText = input;
    setMessages(prev => [...prev, { sender: 'user', text: userText }]);
    setInput('');

    try {
      const res = await fetch('/api/v1/copilot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userText })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { 
        sender: 'bot', 
        text: data.answer,
        action: data.recommended_action 
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { sender: 'bot', text: 'Không thể kết nối tới server AI Copilot.' }]);
    }
  };

  if (!isOpen) return (
    <button onClick={() => setIsOpen(true)} className="fixed bottom-6 right-6 p-4 bg-blue-600 text-white rounded-full shadow-2xl font-bold">
      🤖 AI Copilot
    </button>
  );

  return (
    <div className="fixed bottom-6 right-6 w-96 glass-panel rounded-2xl p-4 shadow-2xl z-50 border border-blue-500/40">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
        <span className="text-sm font-bold text-white flex items-center gap-2">🤖 Fleet AI Copilot</span>
        <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">✕</button>
      </div>
      <div className="h-64 overflow-y-auto space-y-2 mb-3 pr-1 text-xs">
        {messages.map((m, i) => (
          <div key={i} className={`p-2.5 rounded-xl ${m.sender === 'user' ? 'bg-blue-600 text-white ml-8' : 'bg-slate-800 text-slate-200 mr-8 border border-slate-700'}`}>
            {m.text}
            {m.action && (
              <button className="mt-2 w-full py-1.5 bg-blue-500/20 text-blue-400 rounded-lg font-bold border border-blue-500/30 hover:bg-blue-500/40">
                {m.action}
              </button>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input 
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Hỏi về đội xe..." 
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white"
        />
        <button onClick={handleSend} className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg text-xs font-bold">Gửi</button>
      </div>
    </div>
  );
};
```

---

## 4. TIÊU CHÍ REVIEW & NGHIỆM THU PHASE 3 (CHECKLIST FOR USER)

- [ ] **Review Copilot Answer**: User đặt câu hỏi tiếng Việt (*"Tài xế nào có rủi ro cao nhất?"*) và nhận câu trả lời phân tích chính xác kèm nút hành động.
- [ ] **Review AI Risk Reasoning Card**: Khối chữ giải thích nguyên nhân hiển thị rõ ràng trên màn hình Trip Detail mà không có thuật ngữ quá phức tạp.
- [ ] **Nghiệm thu Code**: AI/Developer kiểm tra API Endpoint `/api/v1/copilot/chat` phản hồi dưới 1 giây.
