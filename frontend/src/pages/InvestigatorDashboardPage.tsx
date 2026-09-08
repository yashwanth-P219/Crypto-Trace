import React, { useState, useEffect } from 'react';
import { Shield, CheckCircle, Play, AlertCircle, Clock, FileText, ChevronRight, UserCheck, Activity, Eye, Download, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { Case, User, InvestigatorProfile, InvestigationRecommendation } from '../types';

interface InvestigatorDashboardPageProps {
  currentUser: User;
  onOpenCase: (caseId: string) => void;
}

export const InvestigatorDashboardPage: React.FC<InvestigatorDashboardPageProps> = ({
  currentUser,
  onOpenCase
}) => {
  const [profile, setProfile] = useState<InvestigatorProfile | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingAvailability, setUpdatingAvailability] = useState(false);

  // Recommendations modal
  const [selectedRecommendations, setSelectedRecommendations] = useState<{ caseId: string; recs: InvestigationRecommendation[] } | null>(null);
  const [loadingRecs, setLoadingRecs] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profData, casesData] = await Promise.all([
        api.getMyInvestigatorProfile().catch(() => null),
        api.getCases()
      ]);
      setProfile(profData);
      // Filter cases assigned to current user or all cases if supervisor
      const assignedCases = casesData.filter(c => c.assigned_investigator_id === currentUser.id || !c.assigned_investigator_id);
      setCases(assignedCases.length > 0 ? assignedCases : casesData);
    } catch (err) {
      console.error('Failed to load investigator dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAvailabilityChange = async (newStatus: 'AVAILABLE' | 'BUSY' | 'OFFLINE') => {
    setUpdatingAvailability(true);
    try {
      const updated = await api.updateInvestigatorAvailability(newStatus);
      setProfile(updated);
    } catch (err: any) {
      alert('Failed to update availability: ' + err.message);
    } finally {
      setUpdatingAvailability(false);
    }
  };

  const handleAcceptCase = async (caseId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.acceptCase(caseId);
      await loadData();
    } catch (err: any) {
      alert('Failed to accept case: ' + err.message);
    }
  };

  const handleStartInvestigation = async (caseId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.startInvestigation(caseId);
      await loadData();
      onOpenCase(caseId);
    } catch (err: any) {
      alert('Failed to start investigation: ' + err.message);
    }
  };

  const handleViewRecommendations = async (caseId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLoadingRecs(true);
    try {
      const res = await api.getCaseRecommendations(caseId);
      setSelectedRecommendations({ caseId, recs: res.recommendations });
    } catch (err: any) {
      alert('Failed to load recommendations: ' + err.message);
    } finally {
      setLoadingRecs(false);
    }
  };

  const pendingAcceptanceCases = cases.filter(c => c.status === 'ASSIGNED');
  const activeInvestigations = cases.filter(c => ['ACCEPTED', 'UNDER_INVESTIGATION', 'ANALYSIS_RUNNING', 'EVIDENCE_REVIEW'].includes(c.status));

  return (
    <div className="space-y-6">
      {/* Officer Profile & Readiness Bar */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-[#2563EB]">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-black text-[#1E293B]">
                Officer {currentUser.full_name || currentUser.username}
              </h2>
              {currentUser.badge_number && (
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  {currentUser.badge_number}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {profile?.organization || 'State Police Cyber Cell'} • {profile?.department || 'Cryptocurrency Forensics Unit'}
            </p>
          </div>
        </div>

        {/* Status Toggle & Refresh */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[11px] font-semibold text-slate-500 px-2">Readiness:</span>
            {(['AVAILABLE', 'BUSY', 'OFFLINE'] as const).map((status) => {
              const currentStatus = profile?.availability_status || 'AVAILABLE';
              const isSelected = currentStatus === status;
              return (
                <button
                  key={status}
                  disabled={updatingAvailability}
                  onClick={() => handleAvailabilityChange(status)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    isSelected
                      ? status === 'AVAILABLE'
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : status === 'BUSY'
                        ? 'bg-amber-600 text-white shadow-sm'
                        : 'bg-slate-700 text-white'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {status}
                </button>
              );
            })}
          </div>

          <button
            onClick={loadData}
            title="Refresh Caseload"
            className="p-2.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-500 hover:text-slate-800 transition-colors shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Pending Incoming Cases Notification Banner */}
      {pendingAcceptanceCases.length > 0 && (
        <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping" />
              <h3 className="text-sm font-bold text-amber-800">
                Incoming Assigned Complaints ({pendingAcceptanceCases.length})
              </h3>
            </div>
            <span className="text-xs text-amber-700 font-mono font-medium">Immediate Acceptance Required</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {pendingAcceptanceCases.map((c) => (
              <div
                key={c.case_id}
                onClick={() => onOpenCase(c.case_id)}
                className="p-4 rounded-xl bg-white border border-amber-200 hover:border-amber-400 transition-all cursor-pointer flex flex-col justify-between shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-mono text-xs font-bold text-amber-800">{c.case_number || c.case_id}</span>
                    <span className="text-xs font-bold text-[#1E293B]">₹{c.amount_lost.toLocaleString('en-IN')}</span>
                  </div>
                  <p className="text-xs font-semibold text-[#1E293B]">{c.title || `Victim: ${c.victim_name}`}</p>
                  <p className="text-[11px] text-slate-500 mt-1 truncate font-mono">
                    Suspect: {c.suspect_wallet || 'Pending Tx resolution'}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    onClick={(e) => handleAcceptCase(c.case_id, e)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    Accept Case
                  </button>
                  <button
                    onClick={(e) => handleStartInvestigation(c.case_id, e)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                  >
                    <Play className="w-3.5 h-3.5" />
                    Start Investigation
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Investigations Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-[#1E293B]">Active Case Investigations</h3>
            <p className="text-xs text-slate-500">Cases currently undergoing blockchain graph analysis & VASP identification</p>
          </div>
          <span className="text-xs font-mono font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200">{activeInvestigations.length} Cases Active</span>
        </div>

        {activeInvestigations.length === 0 ? (
          <div className="py-12 text-center bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <Activity className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-xs font-medium text-slate-700">No active cases under investigation</p>
            <p className="text-[11px] text-slate-500 mt-0.5">Accept pending incoming complaints above to begin forensic tracing</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeInvestigations.map((c) => (
              <div
                key={c.case_id}
                onClick={() => onOpenCase(c.case_id)}
                className="p-5 rounded-2xl bg-white hover:border-[#2563EB] border border-slate-200 transition-all cursor-pointer shadow-sm hover:shadow-md space-y-4 group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {c.case_number || c.case_id}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 uppercase">
                        {c.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-[#1E293B] group-hover:text-[#2563EB] transition-colors">
                      {c.title || `Victim: ${c.victim_name}`}
                    </h4>
                  </div>
                  <span className="font-mono text-xs font-black text-amber-700">
                    ₹{c.amount_lost.toLocaleString('en-IN')}
                  </span>
                </div>

                <div className="text-xs text-slate-500 space-y-1 font-mono text-[11px]">
                  <p>Complainant: <span className="text-slate-800 font-medium">{c.victim_name}</span></p>
                  <p className="truncate">Wallet: <span className="text-slate-800 font-medium">{c.suspect_wallet || 'Pending resolution'}</span></p>
                  <p>Network: <span className="text-slate-700">{c.blockchain}</span></p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                  <button
                    onClick={(e) => handleViewRecommendations(c.case_id, e)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 text-xs font-semibold transition-colors"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#2563EB]" />
                    AI Action Leads
                  </button>

                  <div className="flex items-center gap-1 text-xs font-bold text-blue-600 group-hover:text-blue-700">
                    <span>Open Workspace</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommendations Modal */}
      {selectedRecommendations && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl p-6 space-y-4 text-[#1E293B]">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#2563EB]" />
                <h3 className="text-base font-bold text-[#1E293B]">
                  Investigation Leads: {selectedRecommendations.caseId}
                </h3>
              </div>
              <button
                onClick={() => setSelectedRecommendations(null)}
                className="text-slate-400 hover:text-slate-700 text-xs font-bold p-1 rounded-lg"
              >
                ✕ Close
              </button>
            </div>

            <div className="space-y-3">
              {selectedRecommendations.recs.map((rec) => (
                <div key={rec.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                      rec.priority === 'CRITICAL'
                        ? 'bg-red-50 text-red-700 border border-red-200'
                        : rec.priority === 'HIGH'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-blue-50 text-blue-700 border border-blue-200'
                    }`}>
                      {rec.priority} PRIORITY
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">{rec.id}</span>
                  </div>

                  <h4 className="text-xs font-bold text-[#1E293B]">{rec.title}</h4>
                  <p className="text-xs text-slate-600">{rec.description}</p>

                  <div className="p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] text-blue-800">
                    <strong>Suggested Action:</strong> {rec.suggested_action}
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => {
                  const cId = selectedRecommendations.caseId;
                  setSelectedRecommendations(null);
                  onOpenCase(cId);
                }}
                className="px-4 py-2 bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm"
              >
                Open Investigation Workspace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
