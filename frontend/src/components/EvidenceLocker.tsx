import React, { useState } from 'react';
import { ShieldCheck, Plus, Tag, FileText, Hash, Check, Copy } from 'lucide-react';
import { EvidenceItem } from '../types';
import { TruthBadge } from './TruthBadge';
import { api } from '../services/api';

interface EvidenceLockerProps {
  caseId: string;
  evidence: EvidenceItem[];
  onRefresh: () => void;
}

export const EvidenceLocker: React.FC<EvidenceLockerProps> = ({
  caseId,
  evidence,
  onRefresh
}) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [txHash, setTxHash] = useState('');
  const [wallet, setWallet] = useState('');
  const [fromAddr, setFromAddr] = useState('');
  const [toAddr, setToAddr] = useState('');
  const [amount, setAmount] = useState('1.15');
  const [tag, setTag] = useState('PRIMARY_FLOW');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const handleCopy = (h: string) => {
    navigator.clipboard.writeText(h);
    setCopiedHash(h);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.saveEvidence({
        case_id: caseId,
        blockchain: 'Ethereum',
        wallet: wallet || fromAddr,
        transaction_hash: txHash,
        from_address: fromAddr,
        to_address: toAddr,
        amount: parseFloat(amount) || 0,
        tag,
        investigator_notes: notes,
        importance: 'HIGH'
      });
      setShowAddModal(false);
      setTxHash('');
      setNotes('');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to preserve evidence');
    } finally {
      setSaving(false);
    }
  };

  const getTagBadge = (t: string) => {
    switch (t) {
      case 'PRIMARY_FLOW':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'VASP':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'HIGH_PRIORITY':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm text-[#1E293B]">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
              Cryptographic Evidence Locker
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
              SHA-256 VERIFIED
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Tamper-evident chain of custody records with cryptographic hash provenance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <TruthBadge category="INVESTIGATOR DECISION" size="sm" />
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Preserve Evidence</span>
          </button>
        </div>
      </div>

      {/* Evidence Table */}
      {evidence.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-xs">
          No evidence items preserved yet for this case. Click "Preserve Evidence" to record key transactions.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Evidence ID</th>
                <th className="py-2.5 px-3">Transaction Flow</th>
                <th className="py-2.5 px-3">Tag & Classification</th>
                <th className="py-2.5 px-3">Cryptographic Hash (SHA-256)</th>
                <th className="py-2.5 px-3">Investigator Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {evidence.map((item) => (
                <tr key={item.evidence_id} className="hover:bg-slate-50 transition-colors">
                  {/* ID */}
                  <td className="py-3 px-3">
                    <span className="font-mono font-bold text-blue-700">
                      {item.evidence_id}
                    </span>
                    <p className="text-[10px] text-slate-400 font-sans">
                      {new Date(item.retrieved_at).toLocaleDateString()}
                    </p>
                  </td>

                  {/* Flow */}
                  <td className="py-3 px-3">
                    <div className="font-mono text-[#1E293B] font-bold">
                      {item.amount} ETH
                    </div>
                    <p className="text-[10px] text-slate-500 font-mono">
                      Tx: {item.transaction_hash.slice(0, 10)}...{item.transaction_hash.slice(-6)}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      {item.from_address.slice(0, 6)}... → {item.to_address.slice(0, 6)}...
                    </p>
                  </td>

                  {/* Tag */}
                  <td className="py-3 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getTagBadge(item.tag)}`}>
                      {item.tag.replace(/_/g, ' ')}
                    </span>
                  </td>

                  {/* Integrity Hash */}
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-1.5 font-mono text-[10px] text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg w-fit">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>{item.integrity_hash.slice(0, 14)}...</span>
                      <button
                        onClick={() => handleCopy(item.integrity_hash)}
                        className="hover:text-emerald-950 ml-1 text-slate-400"
                        title="Copy SHA-256 Hash"
                      >
                        {copiedHash === item.integrity_hash ? (
                          <Check className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </td>

                  {/* Notes */}
                  <td className="py-3 px-3 max-w-xs text-slate-600 italic">
                    {item.investigator_notes || 'No notes added.'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Evidence Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl text-[#1E293B]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h4 className="text-sm font-bold text-[#1E293B]">Preserve Forensic Evidence</h4>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-700 text-xs font-bold"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSave} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-700 font-semibold block mb-1">Transaction Hash</label>
                <input
                  type="text"
                  required
                  value={txHash}
                  onChange={(e) => setTxHash(e.target.value)}
                  placeholder="0x..."
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">From Address</label>
                  <input
                    type="text"
                    required
                    value={fromAddr}
                    onChange={(e) => setFromAddr(e.target.value)}
                    placeholder="0x..."
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">To Address</label>
                  <input
                    type="text"
                    required
                    value={toAddr}
                    onChange={(e) => setToAddr(e.target.value)}
                    placeholder="0x..."
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Amount (ETH)</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
                <div>
                  <label className="text-slate-700 font-semibold block mb-1">Tag</label>
                  <select
                    value={tag}
                    onChange={(e) => setTag(e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  >
                    <option value="PRIMARY_FLOW">PRIMARY_FLOW</option>
                    <option value="SUSPICIOUS">SUSPICIOUS</option>
                    <option value="VASP">VASP</option>
                    <option value="CROSS_CHAIN">CROSS_CHAIN</option>
                    <option value="HIGH_PRIORITY">HIGH_PRIORITY</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-slate-700 font-semibold block mb-1">Investigator Forensic Notes</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Record investigative rationale, KYC subpoena target, etc."
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white font-bold shadow-sm transition-all"
                >
                  {saving ? 'Computing Hash...' : 'Sign & Preserve'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
