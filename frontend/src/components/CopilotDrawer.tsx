import React, { useState } from 'react';
import { Bot, Send, Sparkles, AlertCircle, Database, Cpu, Brain, Check, Copy } from 'lucide-react';
import { api } from '../services/api';
import { CopilotResponse } from '../types';
import { TruthBadge } from './TruthBadge';

interface CopilotDrawerProps {
  caseId: string;
}

interface ChatMessage {
  sender: 'user' | 'copilot';
  text: string;
  category?: string;
  evidence?: any[];
  timestamp: string;
}

export const CopilotDrawer: React.FC<CopilotDrawerProps> = ({ caseId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'copilot',
      text: "Hello, Inspector. I am your Investigation Copilot for this case. Ask me any question regarding the suspect flow, detected patterns, liquidation destinations, or priority targets. My conclusions are grounded strictly on verified case transactions.",
      category: 'SYSTEM INFERENCE',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const suggestedQuestions = [
    "Where did the victim's money go?",
    "Which wallet should I investigate first?",
    "What suspicious patterns were detected?",
    "Did the funds reach a known VASP?",
    "Show the largest transaction."
  ];

  const handleSend = async (qText?: string) => {
    const query = qText || inputQuery;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessage = {
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!qText) setInputQuery('');
    setLoading(true);

    try {
      const resp: CopilotResponse = await api.queryCopilot(caseId, query);
      const copilotMsg: ChatMessage = {
        sender: 'copilot',
        text: resp.answer,
        category: resp.category,
        evidence: resp.grounded_evidence,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'copilot',
          text: "I was unable to analyze the case ledger at this moment. Please verify the case ID and backend connection.",
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl flex flex-col h-[580px] overflow-hidden shadow-sm">
      {/* Copilot Header */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-[#2563EB]">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-[#1E293B] flex items-center gap-1.5">
              Forensic Copilot
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </h4>
            <p className="text-[11px] text-slate-500">
              Grounded Evidence Reasoning Engine
            </p>
          </div>
        </div>
        <TruthBadge category="AI ASSESSMENT" size="sm" />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="p-3 bg-slate-50/70 border-b border-slate-200 flex flex-wrap gap-1.5 overflow-x-auto">
        {suggestedQuestions.map((q) => (
          <button
            key={q}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="text-[11px] px-2.5 py-1 rounded-full bg-white hover:bg-blue-50 text-blue-700 border border-blue-200 hover:border-blue-300 transition-all text-left truncate max-w-xs shadow-xs"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-xs ${
                m.sender === 'user'
                  ? 'bg-[#2563EB] text-white rounded-br-none'
                  : 'bg-slate-50 border border-slate-200 text-[#1E293B] rounded-bl-none'
              }`}
            >
              {m.category && (
                <div className="mb-2">
                  <TruthBadge category={m.category} size="sm" />
                </div>
              )}
              <div className="whitespace-pre-line">{m.text}</div>
            </div>
            <span className="text-[10px] text-slate-400 mt-1 px-1">
              {m.timestamp}
            </span>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-[#2563EB] bg-blue-50 p-3 rounded-xl max-w-xs border border-blue-200">
            <Sparkles className="w-3.5 h-3.5 animate-spin text-[#2563EB]" />
            <span>Analyzing indexed transactions & topology...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="p-3 border-t border-slate-200 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask Copilot about fund flow, priority wallets, or VASP..."
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || loading}
            className="p-2 bg-[#2563EB] hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl transition-all shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
