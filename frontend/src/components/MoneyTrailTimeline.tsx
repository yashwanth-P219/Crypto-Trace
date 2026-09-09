import React, { useState } from 'react';
import {
  ArrowRight,
  ShieldCheck,
  ExternalLink,
  Building,
  Clock,
  AlertTriangle,
  Copy,
  Check,
  Layers,
  Hash,
  Wallet
} from 'lucide-react';
import { MoneyTrailPath } from '../types';
import { TruthBadge } from './TruthBadge';

interface MoneyTrailTimelineProps {
  paths: MoneyTrailPath[];
  statusMessage?: string;
  onSelectTransaction?: (txHash: string) => void;
  onSelectAddress?: (address: string) => void;
}

export const MoneyTrailTimeline: React.FC<MoneyTrailTimelineProps> = ({
  paths,
  statusMessage,
  onSelectTransaction,
  onSelectAddress
}) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (!paths || paths.length === 0) {
    return (
      <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-8 text-center">
        <AlertTriangle className="w-10 h-10 text-amber-500/80 mx-auto mb-3" />
        <h4 className="text-sm font-bold text-[#1E293B]">
          No Verified Liquidation Path Found
        </h4>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          {statusMessage || "No verified path was found in the currently indexed data. Funds may still reside in intermediate non-custodial wallets or bridged cross-chain."}
        </p>
      </div>
    );
  }

  const primaryPath = paths[0];

  return (
    <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-6">
      {/* Top Header Summary */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
              Automated Forensic Money Trail
            </h3>
            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800 font-bold flex items-center gap-1">
              <Layers className="w-3 h-3" />
              {primaryPath.hops} {primaryPath.hops === 1 ? 'HOP' : 'HOPS'} TOTAL
            </span>
            {primaryPath.is_known_vasp ? (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center gap-1">
                <Building className="w-3 h-3 text-emerald-600" />
                TERMINAL VASP: {primaryPath.destination_vasp}
              </span>
            ) : (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700">
                TERMINAL SINK: {primaryPath.destination_vasp}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Reconstructed cryptographic transfer sequence tracing fund disbursement from origin target through intermediary hops to liquidation destination.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <TruthBadge category="BLOCKCHAIN FACT" size="sm" />
        </div>
      </div>

      {/* Horizontal Multi-Hop Flow Banner */}
      <div className="overflow-x-auto pb-2">
        <div className="flex items-center min-w-max gap-2 py-1">
          {primaryPath.steps.map((step, idx) => (
            <React.Fragment key={step.transaction_hash + idx}>
              {/* Node Card */}
              <div
                onClick={() => onSelectAddress && onSelectAddress(step.from_address)}
                className={`p-3 rounded-xl border cursor-pointer transition-all hover:scale-105 shadow-sm ${
                  idx === 0
                    ? 'bg-red-50 border-red-200 text-red-700'
                    : 'bg-blue-50 border-blue-200 text-blue-700'
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500">
                    {idx === 0 ? 'Origin Target' : `Hop ${idx}: Intermediary`}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {step.from_address.slice(0, 6)}...{step.from_address.slice(-4)}
                  </span>
                </div>
                <p className="text-xs font-bold text-[#1E293B] truncate max-w-[140px]">
                  {step.from_label || 'Suspect Wallet'}
                </p>
              </div>

              {/* Edge Arrow With Amount */}
              <div
                onClick={() => onSelectTransaction && onSelectTransaction(step.transaction_hash)}
                className="flex flex-col items-center px-2 cursor-pointer group"
                title={`Click to inspect tx ${step.transaction_hash}`}
              >
                <span className="text-[11px] font-mono font-bold text-blue-700 group-hover:text-blue-800 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded-full mb-1 shadow-sm">
                  {step.amount} ETH
                </span>
                <div className="flex items-center text-slate-400 group-hover:text-blue-600">
                  <span className="w-6 h-0.5 bg-slate-300 group-hover:bg-blue-600" />
                  <ArrowRight className="w-4 h-4 -ml-1 text-blue-600" />
                </div>
                <span className="text-[9px] font-mono text-slate-400 group-hover:text-slate-600 mt-1">
                  {step.transaction_hash.slice(0, 8)}...
                </span>
              </div>

              {/* Terminal Destination Node on last step */}
              {idx === primaryPath.steps.length - 1 && (
                <div
                  onClick={() => onSelectAddress && onSelectAddress(step.to_address)}
                  className={`p-3 rounded-xl border cursor-pointer shadow-sm transition-all hover:scale-105 ${
                    step.is_destination_vasp || primaryPath.is_known_vasp
                      ? 'border-amber-300 bg-amber-50 text-amber-800'
                      : 'border-slate-300 bg-slate-50 text-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 mb-1">
                    <span className="text-[10px] uppercase font-bold text-amber-700 flex items-center gap-1">
                      <Building className="w-3 h-3" />
                      {step.is_destination_vasp || primaryPath.is_known_vasp ? 'Terminal VASP Exit' : 'Terminal Destination Sink'}
                    </span>
                    <span className="text-[10px] font-mono text-amber-700">
                      {step.to_address.slice(0, 6)}...{step.to_address.slice(-4)}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-[#1E293B] truncate max-w-[150px]">
                    {step.to_label || primaryPath.destination_vasp}
                  </p>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Comprehensive Detailed Sequence Breakdown Cards */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            Verified Cryptographic Transfer Sequence ({primaryPath.steps.length} Hops)
          </h4>
          <span className="text-[11px] text-slate-500 font-mono">
            Total Flow: <strong className="text-[#1E293B]">{primaryPath.flow_amount} ETH</strong>
          </span>
        </div>

        <div className="space-y-3">
          {primaryPath.steps.map((step, idx) => {
            const hopNumber = step.hop_number || (idx + 1);
            const totalHops = step.total_hops || primaryPath.hops;
            const isVasp = step.is_destination_vasp || (idx === primaryPath.steps.length - 1 && primaryPath.is_known_vasp);

            return (
              <div
                key={step.transaction_hash + idx}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:border-blue-400 hover:shadow-md transition-all space-y-3"
              >
                {/* 1. Card Header: Hop Index, Timestamp, Block, VASP Status */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-lg bg-blue-600 text-white font-mono font-bold text-[11px] shadow-sm flex items-center gap-1">
                      <Layers className="w-3 h-3" />
                      Hop {hopNumber} of {totalHops}
                    </span>

                    {/* Whether Destination is a Known VASP / Exchange */}
                    {isVasp ? (
                      <span className="px-2.5 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold flex items-center gap-1">
                        <Building className="w-3.5 h-3.5 text-emerald-600" />
                        Known VASP / Exchange ({step.to_label})
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-medium flex items-center gap-1">
                        <Wallet className="w-3.5 h-3.5 text-slate-500" />
                        Intermediary / Unhosted Wallet
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono">
                    {step.block_number && (
                      <span className="flex items-center gap-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                        <Hash className="w-3 h-3 text-slate-400" />
                        Block #{step.block_number}
                      </span>
                    )}
                    {step.timestamp && (
                      <span className="flex items-center gap-1 text-slate-600">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {new Date(step.timestamp).toLocaleDateString()} {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>

                {/* 2. From Wallet -> To Wallet & Amount Grid */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                  {/* From Wallet */}
                  <div className="md:col-span-5 p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
                      <span>From Wallet</span>
                      <span className="text-blue-600 font-semibold">{step.from_label}</span>
                    </p>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-[#1E293B] truncate" title={step.from_address}>
                        {step.from_address}
                      </span>
                      <button
                        onClick={() => handleCopy(step.from_address, `from-${idx}`)}
                        className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
                        title="Copy wallet address"
                      >
                        {copiedKey === `from-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* Flow Amount & Direction */}
                  <div className="md:col-span-2 flex flex-col items-center justify-center text-center py-1">
                    <span className="text-xs font-black text-blue-700 font-mono bg-blue-50 border border-blue-200 px-3 py-1 rounded-full shadow-sm">
                      {step.amount} ETH
                    </span>
                    <span className="text-[10px] text-slate-500 mt-0.5 font-sans font-medium">
                      ≈ ${Math.round(step.amount * 3000).toLocaleString()} USD
                    </span>
                    <ArrowRight className="w-4 h-4 text-blue-600 mt-1" />
                  </div>

                  {/* To Wallet */}
                  <div className={`md:col-span-5 p-3 rounded-xl border space-y-1 ${
                    isVasp ? 'bg-amber-50/70 border-amber-200' : 'bg-slate-50 border-slate-200'
                  }`}>
                    <p className="text-[10px] uppercase font-bold text-slate-500 flex items-center justify-between">
                      <span>To Wallet</span>
                      <span className={isVasp ? 'text-amber-800 font-bold' : 'text-[#1E293B] font-semibold'}>
                        {step.to_label}
                      </span>
                    </p>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-[#1E293B] truncate" title={step.to_address}>
                        {step.to_address}
                      </span>
                      <button
                        onClick={() => handleCopy(step.to_address, `to-${idx}`)}
                        className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
                        title="Copy wallet address"
                      >
                        {copiedKey === `to-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* 3. Transaction Hash & Inspection Action */}
                <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-50/60 p-2.5 rounded-xl border border-slate-100 text-[11px]">
                  <div className="flex items-center gap-2 min-w-0 max-w-full">
                    <span className="text-slate-500 font-bold uppercase text-[10px] shrink-0">Transaction Hash:</span>
                    <span className="font-mono text-[#1E293B] truncate max-w-md" title={step.transaction_hash}>
                      {step.transaction_hash}
                    </span>
                    <button
                      onClick={() => handleCopy(step.transaction_hash, `tx-${idx}`)}
                      className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors shrink-0"
                      title="Copy transaction hash"
                    >
                      {copiedKey === `tx-${idx}` ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>

                  <button
                    onClick={() => onSelectTransaction && onSelectTransaction(step.transaction_hash)}
                    className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 hover:underline shrink-0"
                  >
                    <span>Inspect Ledger Details</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>

                {/* 4. Suspicious Indicator (If Applicable) */}
                {step.suspicious_indicator ? (
                  <div className="flex items-center gap-2 p-2 rounded-xl bg-amber-50/90 border border-amber-200 text-amber-900 text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>
                      <strong className="font-bold">Suspicious Indicator:</strong> {step.suspicious_indicator}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-slate-400 text-[11px] px-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Standard ledger movement — no high-velocity layering anomaly flagged on this step.</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

