import React from 'react';
import { ArrowRight, ShieldCheck, ExternalLink, Building, Clock, AlertTriangle, Database } from 'lucide-react';
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
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
              Automated Forensic Money Trail
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-700 font-bold">
              {primaryPath.hops} HOPS TO VASP
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Verified step-by-step liquidation pathway terminating at <span className="text-amber-600 font-semibold">{primaryPath.destination_vasp}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <TruthBadge category="BLOCKCHAIN FACT" size="sm" />
        </div>
      </div>

      {/* Horizontal Step Flow Indicator */}
      <div className="overflow-x-auto pb-3">
        <div className="flex items-center min-w-max gap-2 py-2">
          {primaryPath.steps.map((step, idx) => (
            <React.Fragment key={step.transaction_hash + idx}>
              {/* Origin / Intermediary Node */}
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
                    {idx === 0 ? 'Step 1: Suspect Intake' : `Hop ${idx}: Intermediary`}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {step.from_address.slice(0, 6)}...
                  </span>
                </div>
                <p className="text-xs font-bold text-[#1E293B] truncate max-w-[130px]">
                  {step.from_label || 'Suspect Wallet'}
                </p>
              </div>

              {/* Edge arrow with amount */}
              <div
                onClick={() => onSelectTransaction && onSelectTransaction(step.transaction_hash)}
                className="flex flex-col items-center px-2 cursor-pointer group"
                title={`Click to view transaction ${step.transaction_hash}`}
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

              {/* Terminal VASP Node on last step */}
              {idx === primaryPath.steps.length - 1 && (
                <div
                  onClick={() => onSelectAddress && onSelectAddress(step.to_address)}
                  className="p-3 rounded-xl border border-amber-300 bg-amber-50 text-amber-800 cursor-pointer shadow-sm transition-all hover:scale-105"
                >
                  <div className="flex items-center justify-between gap-3 mb-1">
                    <span className="text-[10px] uppercase font-bold text-amber-700 flex items-center gap-1">
                      <Building className="w-3 h-3" />
                      Terminal VASP Exit
                    </span>
                    <span className="text-[10px] font-mono text-amber-600">
                      {step.to_address.slice(0, 6)}...
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

      {/* Step by Step Breakdown Cards */}
      <div className="space-y-3 pt-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Cryptographic Ledger Sequence ({primaryPath.steps.length} Verified Transactions)
        </h4>
        <div className="grid grid-cols-1 gap-2.5">
          {primaryPath.steps.map((step, idx) => (
            <div
              key={step.transaction_hash}
              className="p-3 rounded-xl bg-slate-50/70 border border-slate-200 hover:border-blue-400 hover:bg-white hover:shadow-sm transition-all flex flex-wrap items-center justify-between gap-3 text-xs"
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-white border border-slate-200 text-slate-700 font-bold flex items-center justify-center text-[11px] shadow-sm">
                  {idx + 1}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[#1E293B]">{step.from_label}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <span className={`font-semibold ${idx === primaryPath.steps.length - 1 ? 'text-amber-700 font-bold' : 'text-[#1E293B]'}`}>
                      {step.to_label}
                    </span>
                  </div>
                  <p className="text-[11px] font-mono text-slate-500 mt-0.5">
                    Tx: {step.transaction_hash}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 font-mono">
                <div className="text-right">
                  <p className="font-bold text-[#1E293B]">{step.amount} ETH</p>
                  <p className="text-[10px] text-slate-500 font-sans">
                    ${Math.round(step.amount * 3000).toLocaleString()} USD
                  </p>
                </div>
                <button
                  onClick={() => onSelectTransaction && onSelectTransaction(step.transaction_hash)}
                  className="p-1.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-600 shadow-sm"
                  title="Inspect transaction"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
