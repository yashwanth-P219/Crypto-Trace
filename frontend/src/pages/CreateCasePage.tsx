import React, { useState, useEffect } from 'react';
import { ArrowLeft, PlusCircle, Shield, AlertCircle, Wallet, Hash, Layers, HelpCircle, UserCheck, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { User, CasePriority, AvailableInvestigator } from '../types';

interface CreateCasePageProps {
  currentUser: User | null;
  onCaseCreated: (caseId: string) => void;
  onCancel: () => void;
}

export const CreateCasePage: React.FC<CreateCasePageProps> = ({
  currentUser,
  onCaseCreated,
  onCancel
}) => {
  // 4 Evidence Types: 'wallet' | 'tx_hash' | 'both' | 'none'
  const [evidenceType, setEvidenceType] = useState<'wallet' | 'tx_hash' | 'both' | 'none'>('wallet');

  const [victimName, setVictimName] = useState(currentUser?.full_name || '');
  const [complaintRef, setComplaintRef] = useState(`CR-${new Date().getFullYear()}-CYBER-${Math.floor(1000 + Math.random() * 9000)}`);
  const [amountLost, setAmountLost] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [incidentDate, setIncidentDate] = useState(new Date().toISOString().slice(0, 10));
  const [suspectWallet, setSuspectWallet] = useState('');
  const [txHash, setTxHash] = useState('');
  const [blockchain, setBlockchain] = useState('Ethereum');
  const [priority, setPriority] = useState<CasePriority>('HIGH');
  const [description, setDescription] = useState('');

  // Investigator assignment
  const [availableInvestigators, setAvailableInvestigators] = useState<AvailableInvestigator[]>([]);
  const [selectedInvestigatorId, setSelectedInvestigatorId] = useState<number | ''>('');
  const [loadingInvestigators, setLoadingInvestigators] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInvestigators = async () => {
      setLoadingInvestigators(true);
      try {
        const invs = await api.getAvailableInvestigators();
        setAvailableInvestigators(invs);
        if (invs.length > 0 && !selectedInvestigatorId) {
          setSelectedInvestigatorId(invs[0].id);
        }
      } catch (err) {
        console.error('Failed to load available investigators', err);
      } finally {
        setLoadingInvestigators(false);
      }
    };
    fetchInvestigators();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // Validation
    if (evidenceType === 'wallet' && !suspectWallet.trim()) {
      setError('Please enter the suspect wallet address.');
      setSubmitting(false);
      return;
    }
    if (evidenceType === 'tx_hash' && !txHash.trim()) {
      setError('Please enter the blockchain transaction hash.');
      setSubmitting(false);
      return;
    }
    if (evidenceType === 'both' && (!suspectWallet.trim() || !txHash.trim())) {
      setError('Please provide both the suspect wallet address and the transaction hash.');
      setSubmitting(false);
      return;
    }

    try {
      const payload: any = {
        title: `Complaint: ${victimName || 'Victim'} (${amountLost} ${currency})`,
        victim_name: victimName || currentUser?.full_name || 'Complainant',
        complaint_reference: complaintRef,
        amount_lost: parseFloat(amountLost) || 0,
        currency,
        incident_date: new Date(incidentDate).toISOString(),
        description: description || `Reported ${evidenceType} evidence scam on ${blockchain}`,
        blockchain,
        priority,
        evidence_type: evidenceType
      };

      if (evidenceType === 'wallet' || evidenceType === 'both') {
        payload.suspect_wallet = suspectWallet.trim();
      }
      if (evidenceType === 'tx_hash' || evidenceType === 'both') {
        payload.transaction_hash = txHash.trim();
      }
      if (selectedInvestigatorId) {
        payload.investigator_id = Number(selectedInvestigatorId);
        payload.preferred_investigator_id = Number(selectedInvestigatorId);
      }

      const newCase = await api.createCase(payload);
      onCaseCreated(newCase.case_id);
    } catch (err: any) {
      setError(err.message || 'Failed to register cybercrime complaint');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button
        onClick={onCancel}
        className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Complaints</span>
      </button>

      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-6">
        <div className="border-b border-slate-200 pb-4">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 uppercase tracking-wide">
              Official Fraud Reporting
            </span>
            <span className="text-[10px] font-mono text-slate-500">NCR-FORMAT COMPLIANT</span>
          </div>
          <h2 className="text-xl font-black text-[#1E293B]">
            Register Cryptocurrency Fraud Incident
          </h2>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Report fraudulent transactions, assign to an approved Cybercrime Officer, and trigger automated on-chain multi-hop tracing.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5 text-xs">
          {/* Step 1: Select Evidence Type */}
          <div>
            <label className="text-[#1E293B] font-bold block mb-2 text-xs">
              What Information Do You Have About the Fraud? <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <button
                type="button"
                onClick={() => setEvidenceType('wallet')}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                  evidenceType === 'wallet'
                    ? 'bg-blue-50 border-blue-500 text-blue-800 shadow-sm'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <Wallet className={`w-5 h-5 mb-2 ${evidenceType === 'wallet' ? 'text-[#2563EB]' : 'text-slate-400'}`} />
                <div>
                  <p className="font-bold text-xs">Suspect Wallet</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">I have the fraudster's crypto address</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setEvidenceType('tx_hash')}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                  evidenceType === 'tx_hash'
                    ? 'bg-blue-50 border-blue-500 text-blue-800 shadow-sm'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <Hash className={`w-5 h-5 mb-2 ${evidenceType === 'tx_hash' ? 'text-[#2563EB]' : 'text-slate-400'}`} />
                <div>
                  <p className="font-bold text-xs">Transaction Hash</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">I only have the transaction receipt / hash</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setEvidenceType('both')}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                  evidenceType === 'both'
                    ? 'bg-blue-50 border-blue-500 text-blue-800 shadow-sm'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <Layers className={`w-5 h-5 mb-2 ${evidenceType === 'both' ? 'text-[#2563EB]' : 'text-slate-400'}`} />
                <div>
                  <p className="font-bold text-xs">Both Details</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">I have wallet and transaction hash</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setEvidenceType('none')}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                  evidenceType === 'none'
                    ? 'bg-blue-50 border-blue-500 text-blue-800 shadow-sm'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                <HelpCircle className={`w-5 h-5 mb-2 ${evidenceType === 'none' ? 'text-[#2563EB]' : 'text-slate-400'}`} />
                <div>
                  <p className="font-bold text-xs">Fiat Only / Neither</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">Only UPI / bank memo or screenshot</p>
                </div>
              </button>
            </div>
          </div>

          {/* Complainant Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Complainant / Victim Name <span className="text-red-500">*</span></label>
              <input
                type="text"
                required
                value={victimName}
                onChange={(e) => setVictimName(e.target.value)}
                placeholder="Your full legal name"
                className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
              />
            </div>
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Complaint Reference (Auto-Generated)</label>
              <input
                type="text"
                readOnly
                value={complaintRef}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-500 font-mono"
              />
            </div>
          </div>

          {/* Loss Details */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Amount Lost <span className="text-red-500">*</span></label>
              <input
                type="number"
                step="any"
                required
                value={amountLost}
                onChange={(e) => setAmountLost(e.target.value)}
                placeholder="e.g. 50000"
                className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
              />
            </div>
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
              >
                <option value="INR">INR (₹)</option>
                <option value="ETH">ETH</option>
                <option value="USD">USD ($)</option>
                <option value="USDT">USDT</option>
              </select>
            </div>
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Incident Date</label>
              <input
                type="date"
                required
                value={incidentDate}
                onChange={(e) => setIncidentDate(e.target.value)}
                className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
              />
            </div>
          </div>

          {/* Evidence inputs based on selection */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
            <p className="text-xs font-bold text-[#1E293B]">Cryptographic Identifiers</p>

            {(evidenceType === 'wallet' || evidenceType === 'both') && (
              <div>
                <label className="text-slate-700 font-semibold block mb-1">
                  Suspect Wallet Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required={evidenceType === 'wallet' || evidenceType === 'both'}
                  value={suspectWallet}
                  onChange={(e) => setSuspectWallet(e.target.value.trim())}
                  placeholder="0x..."
                  className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-red-600 font-mono focus:outline-none focus:border-red-500"
                />
              </div>
            )}

            {(evidenceType === 'tx_hash' || evidenceType === 'both') && (
              <div>
                <label className="text-slate-700 font-semibold block mb-1">
                  Blockchain Transaction Hash (TxID) <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required={evidenceType === 'tx_hash' || evidenceType === 'both'}
                  value={txHash}
                  onChange={(e) => setTxHash(e.target.value.trim())}
                  placeholder="0x..."
                  className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-blue-700 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>
            )}

            {evidenceType === 'none' && (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px] leading-relaxed">
                <strong>No on-chain hashes available:</strong> Provide your bank transaction memo, UPI UTR, or exchange purchase order details in the notes below. Your assigned Cybercrime Investigator will extract and resolve the blockchain addresses.
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="text-slate-700 font-semibold block mb-1">Blockchain Network</label>
                <select
                  value={blockchain}
                  onChange={(e) => setBlockchain(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                >
                  <option value="Ethereum">Ethereum (Sepolia / Mainnet)</option>
                  <option value="Polygon">Polygon PoS</option>
                  <option value="BNB Smart Chain">BNB Smart Chain</option>
                </select>
              </div>

              <div>
                <label className="text-slate-700 font-semibold block mb-1">Priority Level</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as CasePriority)}
                  className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                >
                  <option value="CRITICAL">CRITICAL (Recent transaction within 24h)</option>
                  <option value="HIGH">HIGH (Funds active in destination exchange)</option>
                  <option value="MEDIUM">MEDIUM (Standard cyber investigation)</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>
            </div>
          </div>

          {/* Assigned Investigator Selection */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[#1E293B] font-bold block text-xs flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-[#2563EB]" />
                Select Approved Cybercrime Investigator <span className="text-red-500">*</span>
              </label>
              <span className="text-[10px] text-emerald-700 font-mono font-medium">
                {availableInvestigators.length} Verified Officers Available
              </span>
            </div>

            {loadingInvestigators ? (
              <p className="text-[11px] text-slate-500 py-2">Loading approved investigators...</p>
            ) : availableInvestigators.length === 0 ? (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px]">
                No approved investigators are currently online. Your case will be placed in the Central Cyber Queue and automatically assigned upon officer login.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                {availableInvestigators.map((inv) => {
                  const isSelected = selectedInvestigatorId === inv.id;
                  return (
                    <div
                      key={inv.id}
                      onClick={() => setSelectedInvestigatorId(inv.id)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all flex items-start justify-between ${
                        isSelected
                          ? 'bg-blue-50 border-blue-500 shadow-sm'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div>
                        <div className="flex items-center gap-1.5">
                          <p className="font-bold text-[#1E293B] text-xs">{inv.full_name}</p>
                          {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-[#2563EB]" />}
                        </div>
                        <p className="text-[10px] text-slate-500">{inv.department || inv.organization || 'Cyber Crime Branch'}</p>
                        <p className="text-[10px] text-blue-700 font-mono mt-1 font-medium">
                          {inv.specialization || 'Crypto Forensics'} • {inv.active_cases_count} active cases
                        </p>
                      </div>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                        AVAILABLE
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Description / Modus Operandi */}
          <div>
            <label className="text-slate-700 font-semibold block mb-1">
              Incident Modus Operandi / Victim Statement
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe how the fraud occurred (e.g. fake telegram trading group, impersonation, phishing link, fraudulent exchange deposit)..."
              className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-[#1E293B] placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
            />
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 font-bold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2563EB] hover:bg-blue-700 text-white font-bold shadow-sm transition-all active:scale-[0.98]"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{submitting ? 'Submitting & Indexing...' : 'Register Complaint & Notify Officer'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
