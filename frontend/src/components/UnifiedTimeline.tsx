import React, { useState, useEffect } from 'react';
import {
  Clock, Shield, ArrowRight, GitCommit, FileText, CheckCircle2,
  AlertTriangle, RefreshCw, Filter, UserCheck, Search, Tag, Database
} from 'lucide-react';
import { api } from '../services/api';
import { TimelineEvent } from '../types';

interface UnifiedTimelineProps {
  caseId: string;
  initialEvents?: TimelineEvent[];
  onEvidenceClick?: (evidenceId: string) => void;
}

export const UnifiedTimeline: React.FC<UnifiedTimelineProps> = ({
  caseId,
  initialEvents,
  onEvidenceClick
}) => {
  const [events, setEvents] = useState<TimelineEvent[]>(initialEvents || []);
  const [loading, setLoading] = useState(!initialEvents);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const loadTimeline = async () => {
    setLoading(true);
    try {
      const data = await api.getCaseTimeline(caseId);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load timeline', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialEvents) {
      loadTimeline();
    } else {
      setEvents(initialEvents);
    }
  }, [caseId, initialEvents]);

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'CASE_CREATED':
        return <Shield className="w-4 h-4 text-[#2563EB]" />;
      case 'TRANSACTION_INGESTED':
        return <Database className="w-4 h-4 text-blue-600" />;
      case 'PATTERN_DETECTED':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case 'EVIDENCE_ADDED':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case 'STATUS_CHANGED':
        return <GitCommit className="w-4 h-4 text-purple-600" />;
      case 'REPORT_GENERATED':
        return <FileText className="w-4 h-4 text-blue-600" />;
      default:
        return <Clock className="w-4 h-4 text-slate-500" />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'CASE_CREATED':
        return 'border-blue-200 bg-blue-50/50 shadow-sm';
      case 'TRANSACTION_INGESTED':
        return 'border-slate-200 bg-white shadow-sm';
      case 'PATTERN_DETECTED':
        return 'border-amber-200 bg-amber-50/60 shadow-sm';
      case 'EVIDENCE_ADDED':
        return 'border-emerald-200 bg-emerald-50/60 shadow-sm';
      case 'STATUS_CHANGED':
        return 'border-purple-200 bg-purple-50/50 shadow-sm';
      case 'REPORT_GENERATED':
        return 'border-blue-200 bg-blue-50/50 shadow-sm';
      default:
        return 'border-slate-200 bg-white shadow-sm';
    }
  };

  const filteredEvents = events.filter((ev) => {
    if (selectedType !== 'ALL' && ev.event_type !== selectedType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        ev.title.toLowerCase().includes(q) ||
        ev.description.toLowerCase().includes(q) ||
        (ev.actor_username && ev.actor_username.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const eventTypes = ['ALL', 'CASE_CREATED', 'TRANSACTION_INGESTED', 'PATTERN_DETECTED', 'EVIDENCE_ADDED', 'STATUS_CHANGED', 'REPORT_GENERATED'];

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto">
          {eventTypes.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                selectedType === t
                  ? 'bg-[#2563EB] text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
              }`}
            >
              {t === 'ALL' ? 'All Events' : t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-48">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search timeline..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 transition-colors"
            />
          </div>
          <button
            onClick={loadTimeline}
            className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
            title="Reload Timeline"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Timeline Stream */}
      {loading ? (
        <div className="p-8 text-center bg-white border border-slate-200 rounded-xl shadow-sm">
          <RefreshCw className="w-5 h-5 text-[#2563EB] animate-spin mx-auto mb-2" />
          <p className="text-xs text-slate-500">Loading forensic audit timeline...</p>
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="p-8 text-center bg-white border border-slate-200 rounded-xl text-slate-500 text-xs shadow-sm">
          No timeline events recorded matching the current filter.
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
          {filteredEvents.map((ev) => (
            <div key={ev.id} className="relative group">
              {/* Event Dot Icon */}
              <div className="absolute -left-6 top-1.5 w-6 h-6 rounded-full bg-white border border-slate-300 flex items-center justify-center shadow-sm">
                {getEventIcon(ev.event_type)}
              </div>

              {/* Event Card */}
              <div className={`p-3.5 rounded-xl border transition-all ${getEventColor(ev.event_type)}`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#1E293B] tracking-wide">
                      {ev.title}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-mono uppercase bg-slate-100 text-slate-600 border border-slate-200">
                      {ev.event_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
                    {ev.actor_username && (
                      <span className="flex items-center gap-1 text-slate-700 font-semibold">
                        <UserCheck className="w-3 h-3 text-[#2563EB]" />
                        {ev.actor_username}
                      </span>
                    )}
                    <span>{new Date(ev.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-600 mt-1">
                  {ev.description}
                </p>

                {/* Evidence link & metadata pills */}
                <div className="flex flex-wrap items-center gap-2 mt-2 pt-2 border-t border-slate-200/80">
                  {ev.evidence_id && (
                    <button
                      onClick={() => onEvidenceClick && onEvidenceClick(ev.evidence_id!)}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 hover:bg-emerald-100 flex items-center gap-1 font-semibold transition-colors"
                    >
                      <Tag className="w-2.5 h-2.5" />
                      Evidence: {ev.evidence_id}
                    </button>
                  )}

                  {ev.metadata && Object.entries(ev.metadata).map(([k, v]) => (
                    <span
                      key={k}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200"
                    >
                      {k}: {String(v)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
