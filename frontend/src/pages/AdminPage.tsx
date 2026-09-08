import React, { useState, useEffect } from 'react';
import { Building, Plus, Shield, Check, Database, BadgeCheck, CheckCircle2, XCircle, AlertTriangle, RefreshCw, UserX, UserCheck } from 'lucide-react';
import { api } from '../services/api';
import { InvestigatorProfile } from '../types';

export const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'investigators' | 'vasp_directory'>('investigators');

  // Investigators state
  const [investigators, setInvestigators] = useState<InvestigatorProfile[]>([]);
  const [loadingInvs, setLoadingInvs] = useState(false);
  const [rejectingId, setRejectingId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Labels state
  const [labels, setLabels] = useState<any[]>([]);
  const [showAddLabel, setShowAddLabel] = useState(false);
  const [address, setAddress] = useState('');
  const [blockchain, setBlockchain] = useState('Ethereum');
  const [entityName, setEntityName] = useState('');
  const [entityType, setEntityType] = useState('VASP');
  const [confidence, setConfidence] = useState('HIGH');
  const [source, setSource] = useState('Official Exchange Disclosure');
  const [notes, setNotes] = useState('');
  const [savingLabel, setSavingLabel] = useState(false);

  const loadInvestigators = async () => {
    setLoadingInvs(true);
    try {
      const list = await api.getAdminInvestigatorList();
      setInvestigators(list);
    } catch (err) {
      console.error('Failed to load investigator applications', err);
    } finally {
      setLoadingInvs(false);
    }
  };

  const loadLabels = async () => {
    try {
      const data = await api.getLabels();
      setLabels(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadInvestigators();
    loadLabels();
  }, []);

  const handleApprove = async (userId: number) => {
    try {
      await api.approveInvestigator(userId, 'Verified against official LEA cyber roster');
      loadInvestigators();
    } catch (err: any) {
      alert('Approval failed: ' + err.message);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingId) return;
    try {
      await api.rejectInvestigator(rejectingId, rejectReason || 'Incomplete credential verification');
      setRejectingId(null);
      setRejectReason('');
      loadInvestigators();
    } catch (err: any) {
      alert('Rejection failed: ' + err.message);
    }
  };

  const handleSuspend = async (userId: number) => {
    if (!confirm('Are you sure you want to suspend this investigator account?')) return;
    try {
      await api.suspendInvestigator(userId, 'Administrative suspension');
      loadInvestigators();
    } catch (err: any) {
      alert('Suspension failed: ' + err.message);
    }
  };

  const handleReactivate = async (userId: number) => {
    try {
      await api.reactivateInvestigator(userId);
      loadInvestigators();
    } catch (err: any) {
      alert('Reactivation failed: ' + err.message);
    }
  };

  const handleSaveLabel = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingLabel(true);
    try {
      await api.saveLabel({
        address: address.trim(),
        blockchain,
        entity_name: entityName.trim(),
        entity_type: entityType,
        confidence,
        source,
        notes
      });
      setShowAddLabel(false);
      setAddress('');
      setEntityName('');
      loadLabels();
    } catch (err: any) {
      alert(err.message || 'Failed to save label');
    } finally {
      setSavingLabel(false);
    }
  };

  const pendingInvestigators = investigators.filter(i => i.approval_status === 'PENDING');
  const activeInvestigators = investigators.filter(i => i.approval_status !== 'PENDING');

  return (
    <div className="space-y-6">
      {/* Header & Sub-Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-black text-[#1E293B] tracking-wide">
            Platform Administration & Cyber Intel
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage LEA investigator authorizations, VASP entity intelligence, and system-wide controls
          </p>
        </div>

        <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200 rounded-xl">
          <button
            onClick={() => setActiveTab('investigators')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'investigators'
                ? 'bg-[#2563EB] text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BadgeCheck className="w-3.5 h-3.5" />
            Investigator Approvals
            {pendingInvestigators.length > 0 && (
              <span className="px-1.5 py-0.2 bg-amber-500 text-white font-black rounded-full text-[10px]">
                {pendingInvestigators.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('vasp_directory')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'vasp_directory'
                ? 'bg-[#2563EB] text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Building className="w-3.5 h-3.5" />
            VASP Directory ({labels.length})
          </button>
        </div>
      </div>

      {/* TAB 1: INVESTIGATOR APPROVALS */}
      {activeTab === 'investigators' && (
        <div className="space-y-6">
          {/* Pending Applications Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#1E293B] flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                Pending Verification Queue ({pendingInvestigators.length})
              </h3>
              <button
                onClick={loadInvestigators}
                className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-medium"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingInvs ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>

            {loadingInvs ? (
              <div className="p-8 text-center text-slate-500 text-xs font-medium">Loading queue...</div>
            ) : pendingInvestigators.length === 0 ? (
              <div className="p-6 rounded-xl bg-white border border-slate-200 text-center text-xs text-slate-600 shadow-sm">
                ✓ No pending investigator applications requiring verification.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {pendingInvestigators.map((inv) => (
                  <div key={inv.id} className="p-4 rounded-xl bg-white border border-amber-200 space-y-3 shadow-sm">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-[#1E293B] text-xs">{inv.user?.full_name || `Officer #${inv.user_id}`}</h4>
                          {inv.badge_id && (
                            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                              {inv.badge_id}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {inv.organization || 'Police Cyber Branch'} • {inv.department || 'Forensics'}
                        </p>
                      </div>
                      <span className="text-[9px] px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-bold">
                        PENDING
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200 space-y-0.5">
                      <p>Specialization: <span className="text-slate-800 font-medium">{inv.specialization || 'Crypto Forensics'}</span></p>
                      <p>Experience: <span className="text-slate-800 font-medium">{inv.experience_years} Years</span></p>
                      <p>Email: <span className="text-slate-800 font-mono">{inv.user?.email}</span></p>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-100">
                      <button
                        onClick={() => setRejectingId(inv.user_id)}
                        className="px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 border border-red-200 text-red-700 text-xs font-semibold transition-colors"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => handleApprove(inv.user_id)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors shadow-sm"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Approve & Authorize
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Approved Roster Section */}
          <div className="space-y-3 pt-4 border-t border-slate-200">
            <h3 className="text-sm font-bold text-[#1E293B]">Registered Investigator Roster ({activeInvestigators.length})</h3>
            <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto shadow-sm">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[10px]">
                    <th className="py-2.5 px-4">Officer Name</th>
                    <th className="py-2.5 px-4">Badge / ID</th>
                    <th className="py-2.5 px-4">Agency / Unit</th>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Caseload</th>
                    <th className="py-2.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {activeInvestigators.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 font-bold text-[#1E293B]">
                        {inv.user?.full_name || `Officer #${inv.user_id}`}
                      </td>
                      <td className="py-3 px-4 font-mono text-blue-700 font-semibold">
                        {inv.badge_id || 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {inv.organization} • {inv.department}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                          inv.approval_status === 'APPROVED'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : inv.approval_status === 'SUSPENDED'
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}>
                          {inv.approval_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-600 font-medium">
                        {inv.active_cases_count} active cases
                      </td>
                      <td className="py-3 px-4 text-right">
                        {inv.approval_status === 'APPROVED' ? (
                          <button
                            onClick={() => handleSuspend(inv.user_id)}
                            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-red-50 text-slate-700 hover:text-red-700 text-[11px] font-semibold border border-slate-200 transition-colors"
                          >
                            Suspend
                          </button>
                        ) : (
                          <button
                            onClick={() => handleReactivate(inv.user_id)}
                            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-emerald-50 text-slate-700 hover:text-emerald-700 text-[11px] font-semibold border border-slate-200 transition-colors"
                          >
                            Reactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Rejection Reason Modal */}
          {rejectingId && (
            <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
              <form onSubmit={handleReject} className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-[#1E293B]">
                <h3 className="text-base font-bold text-[#1E293B]">Reject Application</h3>
                <p className="text-xs text-slate-500">
                  Please provide a reason for rejecting this investigator verification request.
                </p>
                <textarea
                  rows={3}
                  required
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="e.g. Badge ID could not be validated against state cybercrime registry..."
                  className="w-full bg-white border border-slate-200 rounded-xl p-3 text-xs text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setRejectingId(null)}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all shadow-sm"
                  >
                    Confirm Rejection
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: VASP DIRECTORY */}
      {activeTab === 'vasp_directory' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#1E293B]">VASP Entities & Gateway Directory</h3>
            <button
              onClick={() => setShowAddLabel(!showAddLabel)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Verified Entity Label</span>
            </button>
          </div>

          {showAddLabel && (
            <form onSubmit={handleSaveLabel} className="p-5 rounded-2xl bg-white border border-slate-200 space-y-4 text-xs shadow-sm text-[#1E293B]">
              <h4 className="text-sm font-bold text-[#1E293B]">Add / Update Entity Label</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Contract / Wallet Address</label>
                  <input
                    type="text"
                    required
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="0x..."
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Entity Name</label>
                  <input
                    type="text"
                    required
                    value={entityName}
                    onChange={(e) => setEntityName(e.target.value)}
                    placeholder="e.g. Binance 14 (Hot Wallet)"
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Entity Classification</label>
                  <select
                    value={entityType}
                    onChange={(e) => setEntityType(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  >
                    <option value="VASP">VASP (Exchange Custody)</option>
                    <option value="EXCHANGE">EXCHANGE</option>
                    <option value="BRIDGE">BRIDGE</option>
                    <option value="DEX">DEX</option>
                    <option value="MIXER">MIXER (Sanctioned)</option>
                    <option value="SCAM">SCAM</option>
                    <option value="KNOWN_SERVICE">KNOWN_SERVICE</option>
                    <option value="UNKNOWN">UNKNOWN</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Blockchain</label>
                  <select
                    value={blockchain}
                    onChange={(e) => setBlockchain(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  >
                    <option value="Ethereum">Ethereum</option>
                    <option value="Polygon">Polygon</option>
                    <option value="BNB Smart Chain">BNB Smart Chain</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Confidence</label>
                  <select
                    value={confidence}
                    onChange={(e) => setConfidence(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  >
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Forensic Intelligence Notes</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Source details, court order references, etc."
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddLabel(false)}
                  className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingLabel}
                  className="px-5 py-1.5 bg-[#2563EB] hover:bg-blue-700 text-white font-bold rounded-xl shadow-sm transition-all"
                >
                  {savingLabel ? 'Saving...' : 'Register Entity'}
                </button>
              </div>
            </form>
          )}

          {/* Labels Table */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 overflow-x-auto shadow-sm text-[#1E293B]">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[10px]">
                  <th className="py-2.5 px-3">Entity Name</th>
                  <th className="py-2.5 px-3">Classification</th>
                  <th className="py-2.5 px-3">Address</th>
                  <th className="py-2.5 px-3">Chain</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Intelligence Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {labels.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-3 font-bold text-[#1E293B] flex items-center gap-2">
                      <Building className="w-3.5 h-3.5 text-amber-600" />
                      {l.entity_name}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                        l.entity_type === 'VASP'
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : l.entity_type === 'MIXER'
                          ? 'bg-purple-50 text-purple-700 border-purple-200'
                          : 'bg-slate-100 text-slate-700 border-slate-200'
                      }`}>
                        {l.entity_type}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600">
                      {l.address}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-500">
                      {l.blockchain}
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-emerald-700 font-semibold">{l.confidence}</span>
                    </td>
                    <td className="py-3 px-3 text-slate-500 italic">
                      {l.source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
