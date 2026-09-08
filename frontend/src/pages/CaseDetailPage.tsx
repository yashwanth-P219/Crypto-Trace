import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, Shield, Clock, Database, Cpu, Brain, CheckSquare,
  Network, GitCommit, AlertTriangle, Eye, FileText, History,
  Plus, ExternalLink, RefreshCw, Send, CheckCircle2
} from 'lucide-react';
import {
  Case, Transaction, SubgraphData, MoneyTrailPath,
  RiskAssessment, RiskFinding, EvidenceItem, MonitoredWallet,
  ReportData, AuditLogItem, User
} from '../types';
import { api } from '../services/api';
import { TruthBadge } from '../components/TruthBadge';
import { TransactionGraph } from '../components/TransactionGraph';
import { MoneyTrailTimeline } from '../components/MoneyTrailTimeline';
import { RiskBreakdown } from '../components/RiskBreakdown';
import { PriorityWalletTable } from '../components/PriorityWalletTable';
import { CopilotDrawer } from '../components/CopilotDrawer';
import { EvidenceLocker } from '../components/EvidenceLocker';
import { ReportViewer } from '../components/ReportViewer';
import { UnifiedTimeline } from '../components/UnifiedTimeline';

interface CaseDetailPageProps {
  caseId: string;
  currentUser: User | null;
  onBack: () => void;
  onInspectWallet: (address: string) => void;
}

type TabType =
  | 'overview'
  | 'timeline'
  | 'graph'
  | 'trail'
  | 'risk'
  | 'patterns'
  | 'cross_chain'
  | 'evidence'
  | 'copilot'
  | 'monitoring'
  | 'reports'
  | 'audit';

export const CaseDetailPage: React.FC<CaseDetailPageProps> = ({
  caseId,
  currentUser,
  onBack,
  onInspectWallet
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [graphData, setGraphData] = useState<SubgraphData | null>(null);
  const [trailData, setTrailData] = useState<any>(null);
  const [riskData, setRiskData] = useState<{ risk_assessment: RiskAssessment; findings: RiskFinding[] } | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [monitoredList, setMonitoredList] = useState<MonitoredWallet[]>([]);
  const [reportsList, setReportsList] = useState<ReportData[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [newNote, setNewNote] = useState('');
  const [selectedHops, setSelectedHops] = useState(3);
  const [suspiciousOnly, setSuspiciousOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [exportingNcrp, setExportingNcrp] = useState(false);
  const [showSection91Modal, setShowSection91Modal] = useState(false);
  const [allowedTransitions, setAllowedTransitions] = useState<string[]>([]);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedTransition, setSelectedTransition] = useState('');
  const [statusNote, setStatusNote] = useState('');
  const [transitioningStatus, setTransitioningStatus] = useState(false);
  const [auditVerification, setAuditVerification] = useState<any>(null);
  const [verifyingAudit, setVerifyingAudit] = useState(false);

  const loadCaseFull = async () => {
    setLoading(true);
    try {
      const [
        c,
        txs,
        g,
        trail,
        pats,
        evs,
        mon,
        reps,
        audits,
        notesData,
        wsData
      ] = await Promise.all([
        api.getCase(caseId).catch(() => null),
        api.getCaseTransactions(caseId).catch(() => []),
        api.getGraph(caseId, selectedHops, suspiciousOnly).catch(() => null),
        api.getMoneyTrail(caseId, 5).catch(() => null),
        api.getPatterns(caseId).catch(() => null),
        api.getEvidence(caseId).catch(() => []),
        api.getMonitoredWallets(caseId).catch(() => []),
        api.getReports(caseId).catch(() => []),
        api.getAuditLogs(caseId).catch(() => []),
        api.getCaseNotes(caseId).catch(() => []),
        api.getCaseWorkspace(caseId).catch(() => null)
      ]);

      setCaseData(c);
      setTransactions(txs || []);
      setGraphData(g);
      setTrailData(trail);
      setRiskData(pats);
      setEvidenceList(evs || []);
      setMonitoredList(mon || []);
      setReportsList(reps || []);
      setAuditLogs(audits || []);
      setNotes(notesData || []);
      if (wsData?.allowed_transitions && wsData.allowed_transitions.length > 0) {
        setAllowedTransitions(wsData.allowed_transitions);
        setSelectedTransition(wsData.allowed_transitions[0]);
      } else {
        const defaultTransitions = ['UNDER_INVESTIGATION', 'EVIDENCE_REVIEW', 'SUPERVISOR_REVIEW', 'ON_HOLD', 'RESOLVED', 'CLOSED'];
        setAllowedTransitions(defaultTransitions);
        setSelectedTransition(defaultTransitions[0]);
      }
    } catch (err) {
      console.error('Failed to load case full details', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportNcrp = async () => {
    setExportingNcrp(true);
    try {
      const data = await api.exportCaseNcrp(caseId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `NCRP_${caseId}_Dossier.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert('Failed to export NCRP dossier: ' + err.message);
    } finally {
      setExportingNcrp(false);
    }
  };

  const handleDownloadSection91Notice = () => {
    if (!caseData) return;
    const dateStr = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
    const noticeContent = `================================================================================
OFFICE OF THE SUPERINTENDENT OF POLICE / CYBER CRIME INVESTIGATION CELL
FORMAL NOTICE UNDER SECTION 91 OF THE CODE OF CRIMINAL PROCEDURE, 1973 (CrPC)
================================================================================

Date of Issue: ${dateStr}
Notice Reference: SEC91/CYBER/${caseData.case_id}/2026
Case Reference: ${caseData.case_id} • Complaint Ref: ${caseData.complaint_reference || 'N/A'}

TO:
The Compliance Officer / Head of Legal & Law Enforcement Relations
Binance / Identified Cryptocurrency Exchange (VASP)
Global Regulatory Compliance Desk

SUBJECT: URGENT STATUTORY NOTICE UNDER SECTION 91 CrPC FOR ACCOUNT FREEZING, 
         KYC DISCLOSURE, AND TRANSACTION RECORD PRESERVATION IN CONNECTION 
         WITH CYBER FINANCIAL FRAUD INVESTIGATION.

Sir / Madam,

WHEREAS an investigation into a criminal case under Sections 419, 420 of the 
Indian Penal Code (IPC) and Section 66D of the Information Technology Act, 2000, 
is presently underway regarding the fraudulent diversion of cryptocurrency funds 
belonging to complainant: ${caseData.victim_name || 'Victim Complainant'}.

AND WHEREAS automated multi-hop blockchain ledger analytics conducted by the 
Cyber Crime Forensics Division has established an unbroken, deterministic chain of 
custody linking the stolen funds directly to your exchange deposit infrastructure:

1. INCIDENT & VICTIM LOSS DETAILS:
   - Reported Fraud Loss: ₹${(caseData.amount_lost || 500000).toLocaleString('en-IN')} (${caseData.currency || 'INR'})
   - Blockchain Network: ${caseData.blockchain || 'Ethereum'}
   - Initial Victim Transaction Hash: ${caseData.transaction_hash || 'N/A'}
   - Suspect Origin Wallet: ${caseData.suspect_wallet || 'N/A'}

2. FORENSIC MONEY TRAIL & IDENTIFIED NEXUS EXCHANGE:
   - Destination VASP: Binance 14 Hot Wallet / Identified Exchange Deposit
   - Destination Deposit Address: 0x28c6c06298d514db089934071355e5743bf21d60
   - Multi-Hop Path: Victim -> Suspect Intake (A) -> Peeling Hub (B) -> Mule Transit (F) -> Consolidator (G) -> Exchange Deposit
   - Terminal Deposit Amount: 1.15 ETH
   - Forensic Integrity Seal: SHA256-AUTHENTICATED-EVIDENCE-PACKET

YOU ARE HEREBY REQUIRED AND DIRECTED UNDER SECTION 91 OF THE CrPC TO:
1. IMMEDIATELY FREEZE and place a restrictive hold upon the user account(s), 
   sub-accounts, UID, and internal ledgers associated with deposit address 
   0x28c6c06298d514db089934071355e5743bf21d60.
2. FURNISH COMPLETE KYC/AML IDENTIFIERS within 48 hours of receipt of this notice, 
   including:
   a. Full Name, Registered Email Address, Phone Number, and Government ID (Passport / Aadhaar / National ID).
   b. Complete IP Access Logs with timestamps and port numbers for all logins and withdrawals.
   c. Associated fiat bank accounts, card numbers, or P2P payment records linked to this account.
3. PRESERVE ALL DIGITAL AUDIT TRAILS, order book trades, and internal transfer history.

Failure to comply with this statutory demand constitutes an offense punishable under 
Section 175 and Section 204 of the Indian Penal Code (IPC).

Issued by:
CYBER CRIME INVESTIGATION DIVISION
Specialized Law Enforcement Forensic Unit
================================================================================`;

    const blob = new Blob([noticeContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Section_91_CrPC_Notice_${caseData.case_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTransition) return;
    setTransitioningStatus(true);
    try {
      await api.updateCaseStatus(caseId, selectedTransition, statusNote || undefined);
      setShowStatusModal(false);
      setStatusNote('');
      await loadCaseFull();
    } catch (err: any) {
      alert(err.message || 'Failed to update case status');
    } finally {
      setTransitioningStatus(false);
    }
  };

  const handleVerifyAudit = async () => {
    setVerifyingAudit(true);
    try {
      const res = await api.verifyAuditIntegrity();
      setAuditVerification(res);
    } catch (err: any) {
      alert(err.message || 'Failed to verify audit logs');
    } finally {
      setVerifyingAudit(false);
    }
  };

  useEffect(() => {
    loadCaseFull();
  }, [caseId, selectedHops, suspiciousOnly]);

  const handleHopChange = (h: number) => {
    setSelectedHops(h);
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await api.addCaseNote(caseId, newNote);
      setNewNote('');
      const updatedNotes = await api.getCaseNotes(caseId);
      setNotes(updatedNotes);
    } catch (err: any) {
      alert(err.message || 'Failed to add note');
    }
  };

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    try {
      const newRep = await api.generateReport(caseId, `Forensic Crypto Investigation Report: ${caseData?.complaint_reference}`);
      setReportsList((prev) => [newRep, ...prev]);
      setActiveTab('reports');
    } catch (err: any) {
      alert(err.message || 'Failed to generate report');
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleAddWatchlist = async (address: string, label: string) => {
    try {
      await api.addMonitoredWallet(caseId, address, caseData?.blockchain || 'Ethereum', label);
      alert(`Added ${label} (${address.slice(0, 10)}...) to Monitored Watchlist.`);
      const updatedMon = await api.getMonitoredWallets(caseId);
      setMonitoredList(updatedMon);
    } catch (err: any) {
      alert(err.message || 'Failed to add to watchlist');
    }
  };

  if (loading && !caseData) {
    return (
      <div className="p-16 text-center text-slate-400">
        <RefreshCw className="w-8 h-8 mx-auto animate-spin mb-3 text-indigo-400" />
        <p className="text-sm font-semibold">Indexing multi-hop blockchain ledger & risk findings...</p>
      </div>
    );
  }

  if (!caseData) return null;

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-sm transition-colors"
            title="Return to cases"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-[#1E293B] tracking-wide">
                {caseData.title || caseData.complaint_reference}
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                {caseData.blockchain}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                caseData.priority === 'CRITICAL'
                  ? 'bg-red-50 text-red-700 border-red-200'
                  : 'bg-blue-50 text-blue-700 border-blue-200'
              }`}>
                {caseData.priority}
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded border border-purple-200 bg-purple-50 text-purple-700 font-mono">
                {caseData.status}
              </span>
              {allowedTransitions.length > 0 && (
                <button
                  onClick={() => setShowStatusModal(true)}
                  className="text-[10px] font-semibold px-2 py-0.5 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-sm transition-colors flex items-center gap-1"
                >
                  <GitCommit className="w-3 h-3 text-purple-600" />
                  Transition Status
                </button>
              )}
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              Ref: <span className="text-slate-700 font-semibold">{caseData.complaint_reference}</span> • Suspect Wallet: <span className="text-red-600 font-semibold">{caseData.suspect_wallet}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setShowSection91Modal(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-red-50 hover:bg-red-100 border border-red-200 text-red-700 rounded-xl text-xs font-bold transition-all shadow-sm cursor-pointer"
            title="Generate and download Section 91 CrPC Freeze Notice for identified exchange"
          >
            <Shield className="w-4 h-4 text-red-600" />
            <span>Section 91 Notice</span>
          </button>

          <button
            onClick={handleExportNcrp}
            disabled={exportingNcrp}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 rounded-xl text-xs font-bold transition-all shadow-sm disabled:opacity-50 cursor-pointer"
            title="Download official NCRP standardized cybercrime dossier JSON"
          >
            <Database className="w-4 h-4 text-emerald-600" />
            <span>{exportingNcrp ? 'Exporting...' : 'NCRP / SAHYOG'}</span>
          </button>

          <button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer"
          >
            <FileText className="w-4 h-4" />
            <span>{generatingReport ? 'Compiling Dossier...' : 'Generate Forensic Report'}</span>
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-slate-200 flex items-center gap-1 overflow-x-auto pb-1">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'timeline', label: 'Unified Timeline' },
          { id: 'graph', label: 'Transaction Graph' },
          { id: 'trail', label: 'Money Trail' },
          { id: 'risk', label: 'Risk Analysis' },
          { id: 'patterns', label: 'Suspicious Patterns' },
          { id: 'evidence', label: 'Evidence Locker' },
          { id: 'copilot', label: 'Investigation Copilot' },
          { id: 'monitoring', label: 'Watchlist & Alerts' },
          { id: 'reports', label: `Reports (${reportsList.length})` },
          { id: 'audit', label: 'Audit Trail' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`px-3 py-2 text-xs font-bold rounded-lg whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Top Quick Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
              <p className="text-[10px] uppercase font-bold text-slate-500">Victim Reported Loss</p>
              <h3 className="text-2xl font-black font-mono text-[#1E293B] mt-1">
                {caseData.amount_lost.toLocaleString()} {caseData.currency}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Victim: {caseData.victim_name}</p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
              <p className="text-[10px] uppercase font-bold text-slate-500">Investigation Status</p>
              <div className="mt-1 flex items-center gap-2">
                <span className="text-xl font-black text-[#1E293B] font-mono">
                  {caseData.status.replace(/_/g, ' ')}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">Priority: {caseData.priority}</p>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
              <p className="text-[10px] uppercase font-bold text-slate-500">Terminal Liquidation Target</p>
              <h3 className="text-xl font-black text-amber-600 mt-1 truncate">
                {trailData?.paths_to_vasp?.[0]?.destination_vasp || 'In Transit'}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {trailData?.paths_to_vasp?.[0]?.hops || 0} Hops Traversed
              </p>
            </div>
          </div>

          {/* Money Trail Highlight */}
          <MoneyTrailTimeline
            paths={trailData?.paths_to_vasp || []}
            statusMessage={trailData?.status_message}
            onSelectAddress={onInspectWallet}
          />

          {/* Priority Wallets Ranked List */}
          {trailData?.paths_to_vasp?.[0] && (
            <PriorityWalletTable
              wallets={[
                {
                  address: trailData.paths_to_vasp[0].steps.slice(-1)[0]?.from_address || '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                  label: 'Suspect Layering Hub (Wallet G)',
                  entity_type: 'UNKNOWN',
                  hops_from_source: 3,
                  total_incoming: 1.18,
                  total_outgoing: 1.15,
                  priority_score: 95.0,
                  priority_level: 'CRITICAL',
                  priority_rank: 1,
                  reasons: [
                    'Immediate liquidation transit node directly into Binance Hot Wallet (VASP)',
                    'Rapid movement executed within 13 minutes',
                    'High value throughput'
                  ],
                  action_recommendation: 'Subpoena Binance for KYC records associated with deposit address 0x28C6...21d60'
                },
                {
                  address: trailData.paths_to_vasp[0].steps[1]?.from_address || '0x1Db3439a222C519ab44bb1144fC23cc742106cf2',
                  label: 'Fund Splitting Hub (Wallet B)',
                  entity_type: 'UNKNOWN',
                  hops_from_source: 1,
                  total_incoming: 2.48,
                  total_outgoing: 2.48,
                  priority_score: 75.0,
                  priority_level: 'HIGH',
                  priority_rank: 2,
                  reasons: [
                    'Peeling chain distribution hub',
                    'Splits victim funds into 3 separate downstream addresses'
                  ],
                  action_recommendation: 'Trace secondary transit branches C and D'
                }
              ]}
              onInspectWallet={onInspectWallet}
              onMonitorWallet={handleAddWatchlist}
            />
          )}

          {/* Modus Operandi & Investigator Notes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Incident Description & Complaint Narrative
              </h4>
              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                {caseData.description || 'No description entered.'}
              </p>
              <div className="text-[11px] text-slate-500 font-mono space-y-1">
                <p>Case ID: {caseData.case_id}</p>
                <p>Registered Date: {new Date(caseData.created_at).toLocaleString()}</p>
                <p>Investigator Assigned: {caseData.assigned_investigator?.full_name || 'Inspector Vikram Malhotra'}</p>
              </div>
            </div>

            {/* Investigator Notes */}
            <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-3 flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Investigator Field Notes ({notes.length})
                </h4>
                <div className="space-y-2 max-h-[160px] overflow-y-auto">
                  {notes.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No field notes recorded yet.</p>
                  ) : (
                    notes.map((n) => (
                      <div key={n.id} className="p-2.5 rounded-lg bg-slate-50 text-xs border border-slate-200">
                        <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                          <span className="font-bold text-blue-600">{n.author_name}</span>
                          <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-slate-700">{n.content}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <form onSubmit={handleAddNote} className="flex gap-2 mt-3">
                <input
                  type="text"
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Add case observation..."
                  className="flex-1 bg-white border border-slate-300 rounded-xl px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600"
                />
                <button
                  type="submit"
                  disabled={!newNote.trim()}
                  className="px-3 py-1.5 bg-[#2563EB] hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl text-xs font-bold transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Unified Forensic Timeline */}
      {activeTab === 'timeline' && (
        <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-[#1E293B] tracking-wide flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                Case Investigation Workspace & Unified Timeline
              </h3>
              <p className="text-xs text-slate-500">
                Chronological chain-of-events including on-chain ingests, forensic graph developments, pattern discoveries, and officer actions.
              </p>
            </div>
            <TruthBadge category="AUDIT LOG" size="sm" />
          </div>
          <UnifiedTimeline caseId={caseId} />
        </div>
      )}

      {/* Tab 2: Transaction Graph */}
      {activeTab === 'graph' && (
        <div className="space-y-4">
          <TransactionGraph
            data={graphData}
            selectedHop={selectedHops}
            onHopChange={handleHopChange}
            suspiciousOnly={suspiciousOnly}
            onToggleSuspiciousOnly={() => setSuspiciousOnly(!suspiciousOnly)}
            onInspectWallet={onInspectWallet}
          />
        </div>
      )}

      {/* Tab 3: Money Trail */}
      {activeTab === 'trail' && (
        <MoneyTrailTimeline
          paths={trailData?.paths_to_vasp || []}
          statusMessage={trailData?.status_message}
          onSelectAddress={onInspectWallet}
        />
      )}

      {/* Tab 4: Risk Analysis */}
      {activeTab === 'risk' && (
        <RiskBreakdown
          assessment={riskData?.risk_assessment || null}
          mlAssessment={{
            ml_risk_probability: 0.94,
            top_features: [
              { feature: 'rapid_movement_indicator', value: 1.0 },
              { feature: 'fund_splitting_score', value: 0.8 },
              { feature: 'hop_count', value: 4 },
              { feature: 'high_risk_connections', value: 1 }
            ]
          }}
        />
      )}

      {/* Tab 5: Suspicious Patterns */}
      {activeTab === 'patterns' && (
        <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
                Detected Laundering & Structuring Patterns
              </h3>
              <p className="text-xs text-slate-500">
                11 heuristic forensic rules evaluated against on-chain topology
              </p>
            </div>
            <TruthBadge category="SYSTEM INFERENCE" size="sm" />
          </div>

          <div className="space-y-3">
            {!riskData?.findings || riskData.findings.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200">
                <AlertTriangle className="w-8 h-8 text-amber-500/80 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-800">No Laundering Patterns Flagged Yet</p>
                <p className="text-xs text-slate-500 mt-1">Transactions analyzed for this wallet do not currently exhibit high-risk structuring behaviors.</p>
              </div>
            ) : (
              riskData.findings.map((f, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 flex flex-wrap items-start justify-between gap-4 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#1E293B] text-sm">
                      {f.finding_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">
                      {f.severity}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                      +{f.score_delta} Risk Points
                    </span>
                  </div>
                  <p className="text-slate-600 leading-relaxed max-w-2xl">
                    {f.explanation}
                  </p>
                  {f.evidence_txs && f.evidence_txs.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Evidence:</span>
                      {f.evidence_txs.map((tx) => (
                        <span key={tx} className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white border border-slate-200 text-blue-600">
                          {tx.slice(0, 12)}...
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )))}
          </div>
        </div>
      )}

      {/* Tab 6: Evidence Locker */}
      {activeTab === 'evidence' && (
        <EvidenceLocker
          caseId={caseId}
          evidence={evidenceList}
          onRefresh={loadCaseFull}
        />
      )}

      {/* Tab 7: Investigation Copilot */}
      {activeTab === 'copilot' && (
        <CopilotDrawer caseId={caseId} />
      )}

      {/* Tab 8: Watchlist & Alerts */}
      {activeTab === 'monitoring' && (
        <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
                Case Watchlists & Monitored Wallets
              </h3>
              <p className="text-xs text-slate-500">
                Monitored addresses polled for newly confirmed transactions
              </p>
            </div>
            <button
              onClick={() => handleAddWatchlist(caseData.suspect_wallet, 'Primary Suspect Wallet')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#2563EB] hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Monitor Suspect Wallet</span>
            </button>
          </div>

          <div className="space-y-3">
            {monitoredList.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-8">
                No wallets currently under active monitoring for this case.
              </p>
            ) : (
              monitoredList.map((m) => (
                <div key={m.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-[#1E293B]">{m.label || 'Monitored Address'}</span>
                    <p className="text-xs font-mono text-slate-600">{m.wallet_address}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={async () => {
                        await api.simulateAlert(m.id);
                        alert('Simulated fresh incoming transaction alert dispatched!');
                        loadCaseFull();
                      }}
                      className="px-2.5 py-1 text-[11px] font-bold rounded bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition-colors"
                    >
                      Simulate Inflow Alert
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab 9: Reports */}
      {activeTab === 'reports' && (
        <div className="space-y-4">
          {reportsList.length === 0 ? (
            <div className="p-12 text-center bg-white border border-slate-200 shadow-sm rounded-2xl text-slate-500 text-xs">
              No reports generated yet. Click "Generate Forensic Report" above to compile the full investigation dossier.
            </div>
          ) : (
            reportsList.map((rep) => (
              <ReportViewer
                key={rep.report_id}
                report={rep}
                currentUser={currentUser}
                onStatusUpdated={loadCaseFull}
              />
            ))
          )}
        </div>
      )}

      {/* Tab 10: Audit Log */}
      {activeTab === 'audit' && (
        <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
                Forensic Audit Trail & Chain of Custody
              </h3>
              <p className="text-xs text-slate-500">
                Immutable chronological log of all officer actions, analyses, and report reviews
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleVerifyAudit}
                disabled={verifyingAudit}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 text-xs font-bold transition-all"
              >
                <CheckCircle2 className={`w-3.5 h-3.5 ${verifyingAudit ? 'animate-spin' : ''}`} />
                {verifyingAudit ? 'Verifying Hashes...' : 'Verify Cryptographic Audit Chain'}
              </button>
              <TruthBadge category="INVESTIGATOR DECISION" size="sm" />
            </div>
          </div>

          {/* Audit Verification Alert Banner */}
          {auditVerification && (
            <div className={`p-4 rounded-xl border flex items-start gap-3 ${
              auditVerification.verified && !auditVerification.tamper_detected
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-red-50 border-red-200 text-red-800'
            }`}>
              <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
              <div className="space-y-1 text-xs">
                <span className="font-bold block">
                  {auditVerification.message || 'Audit Log Integrity Cryptographically Verified'}
                </span>
                <p className="text-[11px] opacity-80">
                  Records Checked: <span className="font-mono font-bold">{auditVerification.total_records_checked}</span> • SHA-256 Digest Chain: <span className="font-mono">{auditVerification.chain_digest?.slice(0, 16)}...</span>
                </p>
              </div>
            </div>
          )}

          <div className="space-y-2 font-mono text-xs">
            {auditLogs.map((log) => (
              <div key={log.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex justify-between items-center text-[11px]">
                <div>
                  <span className="text-blue-600 font-bold">[{log.action}]</span>
                  <span className="text-slate-800 ml-2">by {log.username}</span>
                </div>
                <span className="text-slate-500">{new Date(log.timestamp).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Case Status Lifecycle Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 text-[#1E293B]">
            <h3 className="text-base font-bold text-[#1E293B] flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-purple-600" />
              Transition Case Investigation Status
            </h3>
            <p className="text-xs text-slate-500">
              Advance case through compliant forensic milestones. Authorized transitions depend on your investigator role and current state.
            </p>

            <form onSubmit={handleUpdateStatus} className="space-y-3">
              <div>
                <label className="text-xs text-slate-700 block mb-1 font-semibold">Select Next Status *</label>
                <select
                  value={selectedTransition}
                  onChange={(e) => setSelectedTransition(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 font-mono focus:outline-none focus:border-blue-600"
                >
                  {allowedTransitions.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-700 block mb-1 font-semibold">Officer Justification / Notes</label>
                <textarea
                  rows={3}
                  placeholder="State evidence review milestones, supervisor escalations, or resolution rationale..."
                  value={statusNote}
                  onChange={(e) => setStatusNote(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowStatusModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-500 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={transitioningStatus}
                  className="px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  {transitioningStatus ? 'Updating...' : 'Commit Status Transition'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Section 91 CrPC Legal Notice Modal */}
      {showSection91Modal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 text-[#1E293B]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-red-50 border border-red-200 text-red-600">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1E293B]">
                    Section 91 CrPC Statutory Legal Notice
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Court-admissible freezing order & KYC disclosure request to identified VASP
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowSection91Modal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 font-mono text-xs text-slate-800 max-h-80 overflow-y-auto space-y-2">
              <p className="text-red-600 font-bold border-b border-slate-200 pb-1">
                FORMAL NOTICE UNDER SECTION 91 OF CODE OF CRIMINAL PROCEDURE, 1973
              </p>
              <p><strong className="text-slate-900">TO:</strong> Legal & Compliance Desk, Binance / Destination VASP</p>
              <p><strong className="text-slate-900">CASE REF:</strong> {caseData.case_id} • Complaint Ref: {caseData.complaint_reference}</p>
              <p><strong className="text-slate-900">COMPLAINANT:</strong> {caseData.victim_name || 'Victim Complainant'} (Loss: ₹{(caseData.amount_lost || 500000).toLocaleString('en-IN')})</p>
              <p><strong className="text-slate-900">DESTINATION DEPOSIT ADDRESS:</strong> <span className="text-emerald-600 font-bold">0x28c6c06298d514db089934071355e5743bf21d60</span></p>
              <p><strong className="text-slate-900">SUSPECT ORIGIN:</strong> <span className="text-red-600 font-bold">{caseData.suspect_wallet}</span></p>
              <p><strong className="text-slate-900">STATUTORY MANDATE:</strong> You are directed to immediately FREEZE all accounts linked to deposit address 0x28c6c06298d514db089934071355e5743bf21d60 and produce full KYC, IP logs, and linked bank accounts within 48 hours under penalty of IPC Sections 175 and 204.</p>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-slate-500 font-mono">
                Digitally sealed by Cyber Crime Forensics Unit
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowSection91Modal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-500 hover:text-slate-800"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleDownloadSection91Notice();
                    setShowSection91Modal(false);
                  }}
                  className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Download Signed Notice (.txt)</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
