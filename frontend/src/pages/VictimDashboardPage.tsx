import React, { useState, useEffect } from 'react';
import { Shield, Plus, FileText, Download, UserCheck, ChevronRight, Search } from 'lucide-react';
import { api } from '../services/api';
import { Case, User } from '../types';

interface VictimDashboardPageProps {
  currentUser: User;
  onOpenCase: (caseId: string) => void;
  onCreateNewCase: () => void;
}

export const VictimDashboardPage: React.FC<VictimDashboardPageProps> = ({
  currentUser,
  onOpenCase,
  onCreateNewCase
}) => {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const loadCases = async () => {
    setLoading(true);
    try {
      const data = await api.getCases();
      // In case backend returns all cases, filter to victim's cases if applicable
      const myCases = data.filter(c => !c.victim_id || c.victim_id === currentUser.id || c.victim_name?.toLowerCase().includes(currentUser.full_name?.toLowerCase() || ''));
      setCases(myCases.length > 0 ? myCases : data);
    } catch (err) {
      console.error('Failed to load victim cases', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleDownloadNcrp = async (caseId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const ncrpData = await api.exportCaseNcrp(caseId);
      const blob = new Blob([JSON.stringify(ncrpData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `NCRP_${caseId}_Dossier.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert('Failed to export NCRP dossier: ' + err.message);
    }
  };

  const filteredCases = cases.filter(c =>
    (c.case_number || c.case_id).toLowerCase().includes(search.toLowerCase()) ||
    (c.title || '').toLowerCase().includes(search.toLowerCase()) ||
    (c.suspect_wallet || '').toLowerCase().includes(search.toLowerCase())
  );

  const totalLost = cases.reduce((acc, c) => acc + (c.amount_lost || 0), 0);

  return (
    <div className="space-y-6">
      {/* Hero Welcome Header */}
      <div className="relative overflow-hidden rounded-2xl bg-[#0F172A] p-6 sm:p-8 border border-slate-800 shadow-xl text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 uppercase tracking-wide">
                Citizen Victim Portal
              </span>
              <span className="text-[11px] text-slate-400 font-mono">NCRP / I4C Interoperable</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Welcome, {currentUser.full_name || currentUser.username}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Track real-time blockchain tracing progress, inspect exchange destination leads, and coordinate directly with your assigned Cybercrime Law Enforcement Officer.
            </p>
          </div>

          <button
            onClick={onCreateNewCase}
            className="self-start md:self-center flex items-center gap-2 px-5 py-2.5 bg-[#2563EB] hover:bg-blue-600 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            File New Complaint
          </button>
        </div>

        {/* Quick Stats in Hero */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800">
          <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/60">
            <p className="text-[11px] text-slate-400 font-medium">Total Complaints</p>
            <p className="text-xl font-black text-white mt-0.5">{cases.length}</p>
          </div>
          <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/60">
            <p className="text-[11px] text-slate-400 font-medium">Active Investigations</p>
            <p className="text-xl font-black text-blue-400 mt-0.5">
              {cases.filter(c => ['ASSIGNED', 'ACCEPTED', 'UNDER_INVESTIGATION'].includes(c.status)).length}
            </p>
          </div>
          <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/60">
            <p className="text-[11px] text-slate-400 font-medium">Reported Loss</p>
            <p className="text-xl font-black text-amber-400 mt-0.5">
              ₹{totalLost.toLocaleString('en-IN')}
            </p>
          </div>
          <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/60">
            <p className="text-[11px] text-slate-400 font-medium">Resolved Cases</p>
            <p className="text-xl font-black text-emerald-400 mt-0.5">
              {cases.filter(c => c.status === 'RESOLVED').length}
            </p>
          </div>
        </div>
      </div>

      {/* Search and List Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by case number or wallet..."
            className="w-full pl-10 pr-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs text-[#1E293B] placeholder-slate-400 shadow-sm focus:outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
          />
        </div>

        <div className="text-xs text-slate-500 font-medium">
          Showing <span className="text-[#1E293B] font-bold">{filteredCases.length}</span> registered complaints
        </div>
      </div>

      {/* Complaints List */}
      {loading ? (
        <div className="py-16 text-center text-slate-500 text-xs font-medium animate-pulse">
          Loading your registered complaints...
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="py-16 text-center bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-[#1E293B]">No Complaints Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {search ? 'No cases match your search query.' : 'You have not submitted any cybercrime complaints yet.'}
          </p>
          {!search && (
            <button
              onClick={onCreateNewCase}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
            >
              <Plus className="w-4 h-4" />
              File Your First Complaint
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredCases.map((c) => {
            return (
              <div
                key={c.case_id}
                onClick={() => onOpenCase(c.case_id)}
                className="bg-white hover:border-[#2563EB] border border-slate-200 rounded-2xl p-5 transition-all cursor-pointer shadow-sm hover:shadow-md group relative"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left: Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        {c.case_number || c.case_id}
                      </span>
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded uppercase border ${
                        c.status === 'UNDER_INVESTIGATION'
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : c.status === 'ACCEPTED'
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : c.status === 'RESOLVED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {c.status.replace(/_/g, ' ')}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(c.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-[#1E293B] group-hover:text-[#2563EB] transition-colors truncate">
                      {c.title || `Investigation: ${c.complaint_reference}`}
                    </h3>

                    <div className="mt-2.5 flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500">
                      <div>
                        Loss: <span className="font-bold text-[#1E293B]">₹{c.amount_lost.toLocaleString('en-IN')}</span>
                      </div>
                      {c.suspect_wallet ? (
                        <div className="font-mono text-[11px] truncate max-w-xs">
                          Suspect: <span className="text-slate-700 font-semibold">{c.suspect_wallet.slice(0, 8)}...{c.suspect_wallet.slice(-6)}</span>
                        </div>
                      ) : (
                        <div className="text-[11px] text-amber-600 font-mono font-medium">
                          Suspect: [Tx Hash Provided • Wallet Resolving]
                        </div>
                      )}
                      {c.assigned_investigator && (
                        <div className="flex items-center gap-1 text-slate-600">
                          <UserCheck className="w-3.5 h-3.5 text-blue-600" />
                          <span>Officer: <strong>{c.assigned_investigator.full_name}</strong></span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center gap-2 self-end lg:self-center">
                    <button
                      onClick={(e) => handleDownloadNcrp(c.case_id, e)}
                      title="Download NCRP Standardized Dossier"
                      className="p-2 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-600 hover:text-blue-700 transition-colors flex items-center gap-1.5 text-xs font-semibold"
                    >
                      <Download className="w-3.5 h-3.5 text-slate-500" />
                      <span className="hidden sm:inline">NCRP Dossier</span>
                    </button>

                    <div className="flex items-center gap-1 px-3 py-2 rounded-xl bg-blue-50 group-hover:bg-[#2563EB] text-[#2563EB] group-hover:text-white transition-all text-xs font-bold">
                      <span>Track Case</span>
                      <ChevronRight className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                {/* Progress Stepper Bar */}
                <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-4 gap-2 text-center text-[10px] font-medium">
                  <div className={`p-1.5 rounded-lg border ${['ASSIGNED', 'ACCEPTED', 'UNDER_INVESTIGATION', 'RESOLVED', 'CLOSED'].includes(c.status) ? 'bg-blue-50 text-blue-700 border-blue-200 font-bold' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                    1. Registered
                  </div>
                  <div className={`p-1.5 rounded-lg border ${['ACCEPTED', 'UNDER_INVESTIGATION', 'RESOLVED', 'CLOSED'].includes(c.status) ? 'bg-blue-50 text-blue-700 border-blue-200 font-bold' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                    2. Accepted by Officer
                  </div>
                  <div className={`p-1.5 rounded-lg border ${['UNDER_INVESTIGATION', 'RESOLVED', 'CLOSED'].includes(c.status) ? 'bg-blue-50 text-blue-700 border-blue-200 font-bold' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                    3. Blockchain Tracing
                  </div>
                  <div className={`p-1.5 rounded-lg border ${['RESOLVED', 'CLOSED'].includes(c.status) ? 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                    4. Legal Recovery
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Educational info card */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200 text-xs text-slate-600 shadow-sm space-y-2">
        <h4 className="font-bold text-[#1E293B] flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-[#2563EB]" />
          How the CryptoTrace Cyber Defense System Protects Your Complaint
        </h4>
        <p className="leading-relaxed">
          Once submitted, your complaint is automatically indexed into our multi-hop graph exploration engine. Algorithms identify destination cryptocurrency exchanges (such as Binance, WazirX, CoinDCX, Kraken) within seconds. Evidence packages are sealed with cryptographic SHA-256 integrity hashes to support Section 91 CrPC freeze orders under Indian jurisdiction.
        </p>
      </div>
    </div>
  );
};
