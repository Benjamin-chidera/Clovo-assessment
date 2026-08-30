'use client';

import React, { useEffect, useState } from 'react';
import {
  MessageSquare,
  ShieldAlert,
  Bot,
  User,
  Sparkles,
  ExternalLink,
  Lock,
  Clock,
  Eye,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';
import { TopNavbar } from '../../components/TopNavbar';
import { useAuditStore } from '../../stores/useAuditStore';

const SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ConversationItem {
  conversation_id: string;
  patient_id: number;
  patient_name: string;
  procedure: string;
  has_open_alert: boolean;
  risk_level: string | null;
  last_message: string;
  last_message_sender: string | null;
  updated_at: string | null;
}

interface MessageItem {
  id: string;
  role: 'user' | 'coach' | 'assistant';
  content: string;
  created_at: string | null;
}

interface ConversationDetail {
  conversation_id: string;
  patient_id: number;
  patient_name: string;
  procedure: string;
  messages: MessageItem[];
  safety_events: Array<{
    id: string;
    risk_level: string;
    trigger: string;
    action: string;
    status: string;
    created_at: string;
  }>;
}

export default function ConversationsPage() {
  const { openAccessModal } = useAuditStore();
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [convDetail, setConvDetail] = useState<ConversationDetail | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [maskPii, setMaskPii] = useState(true);
  const [accessReasonGranted, setAccessReasonGranted] = useState<string | null>(null);

  // Fetch escalated conversations list
  useEffect(() => {
    const fetchEscalated = async () => {
      try {
        const res = await fetch(`${SERVER_URL}/api/admin/conversations/escalated`);
        if (res.ok) {
          const data: ConversationItem[] = await res.json();
          setConversations(data);
          if (data.length > 0) {
            handleSelectConversation(data[0].conversation_id, data[0].patient_name);
          }
        }
      } catch (err) {
        console.error('Failed to load conversations:', err);
      } finally {
        setIsLoadingList(false);
      }
    };

    fetchEscalated();
  }, []);

  const loadMessages = async (convId: string, reason: string) => {
    setIsLoadingMessages(true);
    try {
      const res = await fetch(
        `${SERVER_URL}/api/admin/conversations/${convId}/messages?access_reason=${encodeURIComponent(
          reason
        )}`
      );
      if (res.ok) {
        const detail = await res.json();
        setConvDetail(detail);
        setSelectedConvId(convId);
        setAccessReasonGranted(reason);
      }
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const handleSelectConversation = (convId: string, patientName: string) => {
    // Check if selecting same
    if (convId === selectedConvId && convDetail) return;

    // Trigger HIPAA / GDPR Access Justification Gate
    openAccessModal(convId, patientName, (reason) => {
      loadMessages(convId, reason);
    });
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <TopNavbar
        title="Escalated Cases & Conversation Inspector"
        subtitle="Need-to-Know access gating, AI decision transparency, and Langfuse trace auditing"
      />

      <div className="flex-1 flex min-h-0">
        {/* Left List: Escalated Patient Cases */}
        <div className="w-80 border-r border-slate-200 bg-white flex flex-col shrink-0 overflow-y-auto">
          <div className="p-4 border-b border-slate-100 bg-slate-50/50">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-indigo-600" />
              Escalated Cases ({conversations.length})
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">Need-to-Know filtered queue</p>
          </div>

          <div className="divide-y divide-slate-100">
            {isLoadingList ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading cases...</div>
            ) : conversations.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">No active cases</div>
            ) : (
              conversations.map((c) => {
                const isSelected = c.conversation_id === selectedConvId;
                return (
                  <div
                    key={c.conversation_id}
                    onClick={() => handleSelectConversation(c.conversation_id, c.patient_name)}
                    className={`p-4 cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-indigo-50/70 border-l-4 border-indigo-600'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between pb-1">
                      <span className="text-xs font-bold text-slate-900">{c.patient_name}</span>
                      {c.risk_level && (
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            c.risk_level === 'critical'
                              ? 'bg-red-100 text-red-800'
                              : c.risk_level === 'high'
                              ? 'bg-orange-100 text-orange-800'
                              : c.risk_level === 'medium'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {c.risk_level}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 font-medium">{c.procedure}</p>
                    <p className="text-xs text-slate-600 mt-1.5 line-clamp-1 italic font-medium">
                      "{c.last_message}"
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Content: Audited Thread & Decision Metrics */}
        <div className="flex-1 bg-slate-50/50 flex flex-col min-w-0 overflow-hidden">
          {convDetail ? (
            <div className="flex-1 flex flex-col h-full overflow-hidden">
              {/* Context Bar */}
              <div className="p-4 bg-white border-b border-slate-200 flex items-center justify-between shadow-2xs">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 font-bold text-xs">
                    <User className="w-4 h-4 text-slate-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <span>{convDetail.patient_name}</span>
                      <span className="text-xs font-normal text-slate-500">· {convDetail.procedure}</span>
                    </h3>
                    <p className="text-[11px] text-slate-500 flex items-center gap-1">
                      <Lock className="w-3 h-3 text-emerald-600" />
                      <span>Access Reason: <strong className="text-slate-700">{accessReasonGranted}</strong></span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {/* PII Mask Toggle */}
                  <button
                    onClick={() => setMaskPii(!maskPii)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors"
                  >
                    {maskPii ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                    <span>{maskPii ? 'Unmask PII (Audited)' : 'Mask PII'}</span>
                  </button>

                  {/* Langfuse Deep Link */}
                  <a
                    href="http://localhost:3000"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Langfuse Trace</span>
                    <ExternalLink className="w-3 h-3 ml-0.5" />
                  </a>
                </div>
              </div>

              {/* Messages Scroll Area */}
              <div className="flex-1 p-6 overflow-y-auto space-y-4">
                {isLoadingMessages ? (
                  <div className="p-12 text-center text-xs text-slate-400">Loading conversation history...</div>
                ) : (
                  convDetail.messages.map((m) => {
                    const isCoach = m.role === 'coach' || m.role === 'assistant';

                    return (
                      <div
                        key={m.id}
                        className={`flex gap-3 max-w-2xl ${isCoach ? 'mr-auto' : 'ml-auto flex-row-reverse'}`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                            isCoach
                              ? 'bg-indigo-600 text-white shadow-xs'
                              : 'bg-slate-300 text-slate-700'
                          }`}
                        >
                          {isCoach ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                        </div>

                        <div
                          className={`p-4 rounded-2xl border text-xs leading-relaxed space-y-1.5 shadow-2xs ${
                            isCoach
                              ? 'bg-white border-slate-200 text-slate-800'
                              : 'bg-indigo-600 border-indigo-700 text-white'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-4">
                            <span className={`font-bold ${isCoach ? 'text-indigo-700' : 'text-indigo-100'}`}>
                              {isCoach ? 'Amy Recovery Coach' : convDetail.patient_name}
                            </span>
                            <span className={`text-[10px] ${isCoach ? 'text-slate-400' : 'text-indigo-200'}`}>
                              {m.created_at
                                ? new Date(m.created_at).toLocaleTimeString([], {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })
                                : ''}
                            </span>
                          </div>

                          <p className="whitespace-pre-wrap">{m.content}</p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center p-8 text-center text-slate-400">
              <div className="space-y-2">
                <MessageSquare className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-sm font-semibold text-slate-600">Select an Escalated Case</p>
                <p className="text-xs text-slate-400">Click any case on the left to audit the full interaction.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
