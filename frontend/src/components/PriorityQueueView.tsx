import React, { useState, useEffect } from 'react';
import {
  Flame, ShieldAlert, AlertTriangle, CheckCircle, UserCheck, Clock,
  ArrowRight, Filter, RefreshCw, Eye, Search, Layers, ChevronRight,
  TrendingUp, Activity, FileCheck, Award
} from 'lucide-react';
import { api } from '../services/api';
import { PriorityScoreItem, PriorityQueueResponse, PriorityLevel, PriorityStatus, User } from '../types';
import { TruthBadge } from './TruthBadge';
import { ErrorBoundary } from './ErrorBoundary';

interface PriorityQueueViewProps {
  currentUser: User | null;
  onInspectWallet: (address: string) => void;
  onOpenCase: (caseId: string) => void;
}

const PriorityQueueViewInner: React.FC<PriorityQueueViewProps> = ({
  currentUser,
  onInspectWallet,
  onOpenCase
}) => {
  const [queue, setQueue] = useState<PriorityQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('');
  const [searchTarget, setSearchTarget] = useState('');
  const [selectedLead, setSelectedLead] = useState<PriorityScoreItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [assignUser, setAssignUser] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [showCalcModal, setShowCalcModal] = useState(false);
  const [calcWallet, setCalcWallet] = useState('');
  const [calcCaseId, setCalcCaseId] = useState('');

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await api.getPriorityQueue(
        statusFilter || undefined,
        levelFilter || undefined
      );
      setQueue(data);
    } catch (err) {
      console.error('Failed to load priority queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [statusFilter, levelFilter]);

  const handleReview = async (leadId: string) => {
    setActionLoading(true);
    try {
      await api.reviewPriorityLead(leadId, reviewNotes || 'Reviewed by investigator');
      setReviewNotes('');
      await loadQueue();
      if (selectedLead?.id === leadId) {
        setSelectedLead((prev) => prev ? { ...prev, status: 'REVIEWED' } : null);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to review lead');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAssign = async (leadId: string) => {
    if (!assignUser.trim()) return;
    setActionLoading(true);
    try {
      await api.assignPriorityLead(leadId, assignUser.trim());
      setAssignUser('');
      await loadQueue();
      if (selectedLead?.id === leadId) {
        setSelectedLead((prev) => prev ? { ...prev, status: 'ASSIGNED', assigned_to: assignUser } : null);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to assign lead (Requires Supervisor or Administrator role)');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRunCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!calcWallet.trim()) return;
    setActionLoading(true);
    try {
      const result = await api.calculatePriority({
        wallet_address: calcWallet.trim(),
        case_id: calcCaseId.trim() || undefined
      });
      setShowCalcModal(false);
      setCalcWallet('');
      setCalcCaseId('');
      await loadQueue();
      setSelectedLead(result);
    } catch (err: any) {
      alert(err.message || 'Failed to calculate priority');
    } finally {
      setActionLoading(false);
    }
  };

  const getLevelBadge = (level?: string) => {
    switch ((level || '').toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'LOW':
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const getStatusBadge = (status?: string) => {
    switch ((status || '').toUpperCase()) {
      case 'NEW':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'REVIEWED':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'ASSIGNED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'DISMISSED':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  const rawList: PriorityScoreItem[] = queue?.items || queue?.queue || [];
  const filteredItems = rawList.filter((item) => {
    const target = item.target_identifier || item.wallet_address || item.object_id || '';
    const caseId = item.case_id || '';
    if (!searchTarget) return true;
    return (
      target.toLowerCase().includes(searchTarget.toLowerCase()) ||
      caseId.toLowerCase().includes(searchTarget.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl text-white relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <div className="p-2 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400">
                <Flame className="w-5 h-5" />
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
                Investigation Priority Engine
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40 font-mono font-bold">
                TRIAGE ENGINE
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Deterministic priority triage ranking suspect wallets and transaction trails by urgency, risk severity, on-chain asset exposure, and evidentiary weight.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCalcModal(true)}
              className="px-4 py-2.5 rounded-xl bg-[#2563EB] hover:bg-blue-600 text-white text-xs font-bold transition-all shadow-lg shadow-blue-500/20 flex items-center gap-1.5"
            >
              <TrendingUp className="w-3.5 h-3.5" />
              Assess New Wallet
            </button>
            <button
              onClick={loadQueue}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
              title="Refresh Priority Queue"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Priority Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-6 pt-6 border-t border-slate-800">
          <div className="bg-slate-900/80 border border-slate-700/60 p-3.5 rounded-xl">
            <span className="text-[11px] text-slate-400 font-semibold block">Total Leads</span>
            <span className="text-2xl font-black text-white mt-0.5 block">{queue?.total ?? queue?.total_leads ?? rawList.length}</span>
          </div>
          <div className="bg-slate-900/80 border border-slate-700/60 p-3.5 rounded-xl">
            <span className="text-[11px] text-red-400 font-semibold block flex items-center gap-1">
              <Flame className="w-3 h-3" /> Critical Priority
            </span>
            <span className="text-2xl font-black text-red-400 mt-0.5 block">{queue?.critical_count ?? 0}</span>
          </div>
          <div className="bg-slate-900/80 border border-slate-700/60 p-3.5 rounded-xl">
            <span className="text-[11px] text-orange-400 font-semibold block">High Priority</span>
            <span className="text-2xl font-black text-orange-400 mt-0.5 block">{queue?.high_count ?? 0}</span>
          </div>
          <div className="bg-slate-900/80 border border-slate-700/60 p-3.5 rounded-xl">
            <span className="text-[11px] text-amber-400 font-semibold block">Medium Priority</span>
            <span className="text-2xl font-black text-amber-400 mt-0.5 block">{queue?.medium_count ?? 0}</span>
          </div>
          <div className="bg-slate-900/80 border border-slate-700/60 p-3.5 rounded-xl">
            <span className="text-[11px] text-blue-400 font-semibold block">Low Priority</span>
            <span className="text-2xl font-black text-blue-400 mt-0.5 block">{queue?.low_count ?? 0}</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white border border-slate-200 p-3.5 rounded-xl shadow-sm">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-lg p-1">
            <button
              onClick={() => setStatusFilter('')}
              className={`px-2.5 py-1 text-xs rounded-md font-semibold transition-colors ${
                statusFilter === '' ? 'bg-[#2563EB] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Status
            </button>
            <button
              onClick={() => setStatusFilter('NEW')}
              className={`px-2.5 py-1 text-xs rounded-md font-semibold transition-colors ${
                statusFilter === 'NEW' ? 'bg-[#2563EB] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              New Leads
            </button>
            <button
              onClick={() => setStatusFilter('REVIEWED')}
              className={`px-2.5 py-1 text-xs rounded-md font-semibold transition-colors ${
                statusFilter === 'REVIEWED' ? 'bg-[#2563EB] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Reviewed
            </button>
            <button
              onClick={() => setStatusFilter('ASSIGNED')}
              className={`px-2.5 py-1 text-xs rounded-md font-semibold transition-colors ${
                statusFilter === 'ASSIGNED' ? 'bg-[#2563EB] text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Assigned
            </button>
          </div>

          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-lg p-1">
            <button
              onClick={() => setLevelFilter('')}
              className={`px-2 py-1 text-xs rounded-md font-semibold transition-colors ${
                levelFilter === '' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Levels
            </button>
            <button
              onClick={() => setLevelFilter('CRITICAL')}
              className={`px-2 py-1 text-xs rounded-md font-semibold transition-colors ${
                levelFilter === 'CRITICAL' ? 'bg-red-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Critical
            </button>
            <button
              onClick={() => setLevelFilter('HIGH')}
              className={`px-2 py-1 text-xs rounded-md font-semibold transition-colors ${
                levelFilter === 'HIGH' ? 'bg-orange-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              High
            </button>
            <button
              onClick={() => setLevelFilter('MEDIUM')}
              className={`px-2 py-1 text-xs rounded-md font-semibold transition-colors ${
                levelFilter === 'MEDIUM' ? 'bg-amber-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Medium
            </button>
          </div>
        </div>

        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search wallet, case ID..."
            value={searchTarget}
            onChange={(e) => setSearchTarget(e.target.value)}
            className="w-full sm:w-64 pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
          />
        </div>
      </div>

      {/* Main Content Layout: Priority List + Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority Items Table/List */}
        <div className="lg:col-span-2 space-y-3">
          {loading ? (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl shadow-sm">
              <RefreshCw className="w-6 h-6 text-[#2563EB] animate-spin mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading priority triage queue...</p>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl shadow-sm">
              <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <p className="text-sm font-bold text-[#1E293B]">No priority leads matching current filters</p>
              <p className="text-xs text-slate-500 mt-1">All high-risk leads have been triaged or none currently match criteria.</p>
            </div>
          ) : (
            filteredItems.map((item) => {
              const targetId = item.target_identifier || item.wallet_address || item.object_id || 'Unknown Target';
              const level = (item.priority_level || item.priority_category || 'LOW').toUpperCase();
              const status = (item.status || 'NEW').toUpperCase();
              const score = Number(item.priority_score || 0);
              const urgency = item.urgency_score ?? Math.min(100, Math.round(score * 0.9));
              const severity = item.severity_score ?? Math.min(100, Math.round(score * 0.95));
              const exposure = item.asset_exposure ?? Math.min(100, Math.round(score * 0.8));
              const evidence = item.evidence_strength ?? 70;
              const reasons = item.explanation || item.reasons || [];
              const isSelected = selectedLead?.id === item.id;

              return (
                <div
                  key={String(item.id)}
                  onClick={() => setSelectedLead(item)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer bg-white shadow-sm ${
                    isSelected
                      ? 'border-[#2563EB] ring-1 ring-[#2563EB] bg-blue-50/20'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1.5">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getLevelBadge(level)}`}>
                          {level}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getStatusBadge(status)}`}>
                          {status}
                        </span>
                        <span className="text-[10px] text-slate-400 uppercase font-mono font-medium">
                          {item.target_type || item.object_type || 'WALLET'}
                        </span>
                        {item.case_id && (
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              onOpenCase(item.case_id!);
                            }}
                            className="text-[10px] font-mono text-blue-600 hover:underline cursor-pointer font-bold"
                          >
                            {item.case_id}
                          </span>
                        )}
                      </div>

                      <p className="font-mono text-xs text-[#1E293B] truncate font-bold">
                        {targetId}
                      </p>

                      {reasons.length > 0 && (
                        <p className="text-xs text-slate-500 mt-1.5 line-clamp-2">
                          • {reasons[0]}
                        </p>
                      )}
                    </div>

                    <div className="text-right flex-shrink-0">
                      <div className="flex items-baseline gap-1 justify-end">
                        <span className="text-2xl font-black text-[#1E293B]">{score.toFixed(0)}</span>
                        <span className="text-[10px] text-slate-400">/100</span>
                      </div>
                      <span className="text-[10px] text-slate-500 block font-medium">Priority Score</span>
                    </div>
                  </div>

                  {/* Score component gauges */}
                  <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t border-slate-100 text-[10px]">
                    <div>
                      <span className="text-slate-400 block">Urgency</span>
                      <span className="font-mono font-bold text-slate-700">{urgency.toFixed(0)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Severity</span>
                      <span className="font-mono font-bold text-slate-700">{severity.toFixed(0)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Exposure</span>
                      <span className="font-mono font-bold text-slate-700">{exposure.toFixed(0)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Evidence</span>
                      <span className="font-mono font-bold text-slate-700">{evidence.toFixed(0)}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Lead Inspection Drawer */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 h-fit sticky top-20 shadow-sm text-[#1E293B]">
          {selectedLead ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div>
                  <span className="text-[10px] text-slate-400 font-mono block">LEAD DETAILS</span>
                  <h3 className="text-sm font-bold text-[#1E293B] flex items-center gap-2">
                    Priority #{String(selectedLead.id).slice(-6)}
                    <span className={`text-[10px] px-2 py-0.5 rounded border ${getLevelBadge(selectedLead.priority_level || selectedLead.priority_category)}`}>
                      {selectedLead.priority_level || selectedLead.priority_category || 'LOW'}
                    </span>
                  </h3>
                </div>
                <TruthBadge category="AI ASSESSMENT" size="sm" />
              </div>

              <div>
                <span className="text-[11px] text-slate-500 block mb-1 font-medium">Target Address / Identifier</span>
                <div className="bg-slate-50 p-2 rounded-lg border border-slate-200 flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-blue-700 truncate select-all font-semibold">
                    {selectedLead.target_identifier || selectedLead.wallet_address || selectedLead.object_id || 'N/A'}
                  </span>
                  <button
                    onClick={() => onInspectWallet(selectedLead.target_identifier || selectedLead.wallet_address || selectedLead.object_id || '')}
                    className="p-1 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition-colors"
                    title="Open in Wallet Analyzer"
                  >
                    <Eye className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {selectedLead.case_id && (
                <div>
                  <span className="text-[11px] text-slate-500 block mb-1 font-medium">Associated Case</span>
                  <button
                    onClick={() => onOpenCase(selectedLead.case_id!)}
                    className="text-xs text-[#2563EB] hover:underline flex items-center gap-1 font-mono font-bold"
                  >
                    {selectedLead.case_id} <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              )}

              {/* Factor Points Breakdown */}
              <div>
                <span className="text-[11px] text-slate-500 font-bold block mb-2 uppercase tracking-wide">
                  Factor Points Breakdown
                </span>
                <div className="space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  {Object.entries(selectedLead.factor_points || {
                    topological_risk: Math.round(Number(selectedLead.priority_score || 0) * 0.4),
                    asset_exposure: Math.round(Number(selectedLead.priority_score || 0) * 0.3),
                    urgency: Math.round(Number(selectedLead.priority_score || 0) * 0.3),
                  }).map(([key, pts]) => (
                    <div key={key} className="flex items-center justify-between text-xs">
                      <span className="text-slate-600 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-mono font-bold text-amber-700">+{pts} pts</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Explanations */}
              <div>
                <span className="text-[11px] text-slate-500 font-bold block mb-2 uppercase tracking-wide">
                  Investigative Findings
                </span>
                <ul className="space-y-1 text-xs text-slate-600">
                  {(selectedLead.explanation || selectedLead.reasons || []).map((exp, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-[#2563EB] mt-0.5 font-bold">•</span>
                      <span>{exp}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Assignment & Review Controls */}
              <div className="pt-3 border-t border-slate-200 space-y-3">
                {selectedLead.status !== 'REVIEWED' && (
                  <div>
                    <label className="text-[11px] text-slate-500 block mb-1 font-medium">Review Notes</label>
                    <input
                      type="text"
                      placeholder="Optional notes..."
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] placeholder-slate-400 mb-2 focus:outline-none focus:border-[#2563EB]"
                    />
                    <button
                      onClick={() => handleReview(String(selectedLead.id))}
                      disabled={actionLoading}
                      className="w-full py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-sm"
                    >
                      <FileCheck className="w-3.5 h-3.5" />
                      Mark Lead Reviewed
                    </button>
                  </div>
                )}

                <div>
                  <label className="text-[11px] text-slate-500 block mb-1 font-medium">
                    Assign to Investigator (Supervisor / Admin)
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Username (e.g. investigator1)"
                      value={assignUser}
                      onChange={(e) => setAssignUser(e.target.value)}
                      className="flex-1 px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                    />
                    <button
                      onClick={() => handleAssign(String(selectedLead.id))}
                      disabled={actionLoading || !assignUser.trim()}
                      className="px-3 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 disabled:opacity-40 text-white text-xs font-bold transition-all flex items-center gap-1 shadow-sm"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      Assign
                    </button>
                  </div>
                  {selectedLead.assigned_to && (
                    <p className="text-[10px] text-emerald-700 mt-1 font-mono font-bold">
                      Currently assigned to: {selectedLead.assigned_to}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400">
              <ChevronRight className="w-6 h-6 mx-auto mb-2 text-slate-300" />
              <p className="text-xs">Select any lead from the queue to inspect factor scores, evidence explanations, and assign workflows.</p>
            </div>
          )}
        </div>
      </div>

      {/* Manual Calculate Modal */}
      {showCalcModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl text-[#1E293B]">
            <h3 className="text-base font-bold text-[#1E293B] mb-1 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[#2563EB]" />
              Assess Suspect Wallet Priority
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Execute deterministic priority scoring on any suspect wallet address.
            </p>

            <form onSubmit={handleRunCalculate} className="space-y-3">
              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Wallet Address *</label>
                <input
                  type="text"
                  required
                  placeholder="0x..."
                  value={calcWallet}
                  onChange={(e) => setCalcWallet(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Case ID (Optional)</label>
                <input
                  type="text"
                  placeholder="CASE-2026-001"
                  value={calcCaseId}
                  onChange={(e) => setCalcCaseId(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCalcModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-600 hover:text-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  {actionLoading ? 'Calculating...' : 'Run Priority Scoring'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export const PriorityQueueView: React.FC<PriorityQueueViewProps> = (props) => {
  return (
    <ErrorBoundary fallbackTitle="Investigation Priority Queue">
      <PriorityQueueViewInner {...props} />
    </ErrorBoundary>
  );
};
