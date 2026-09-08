import React from 'react';
import { Award, ArrowRight, Eye, ShieldAlert, Building, ExternalLink } from 'lucide-react';
import { PriorityWallet } from '../types';
import { TruthBadge } from './TruthBadge';

interface PriorityWalletTableProps {
  wallets: PriorityWallet[];
  onInspectWallet?: (address: string) => void;
  onMonitorWallet?: (address: string, label: string) => void;
}

export const PriorityWalletTable: React.FC<PriorityWalletTableProps> = ({
  wallets,
  onInspectWallet,
  onMonitorWallet
}) => {
  if (!wallets || wallets.length === 0) {
    return (
      <div className="p-6 bg-white border border-slate-200 rounded-2xl text-center text-slate-500 shadow-sm">
        No candidate wallets ranked for this query.
      </div>
    );
  }

  const getPriorityBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm text-[#1E293B]">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
              Investigation Priority Engine
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-bold">
              TOP TARGETS
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Ranked candidate wallets based on VASP liquidation proximity, throughput, and layering heuristics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <TruthBadge category="AI ASSESSMENT" size="sm" />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <th className="py-2.5 px-3">Rank</th>
              <th className="py-2.5 px-3">Address & Entity</th>
              <th className="py-2.5 px-3">Hops</th>
              <th className="py-2.5 px-3">Flow Volume</th>
              <th className="py-2.5 px-3">Priority Score</th>
              <th className="py-2.5 px-3">Forensic Rationale</th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {wallets.map((w) => (
              <tr key={w.address} className="hover:bg-slate-50 transition-colors">
                {/* Rank */}
                <td className="py-3 px-3">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-mono font-bold text-xs ${
                    w.priority_rank === 1
                      ? 'bg-amber-100 text-amber-800 border border-amber-300'
                      : w.priority_rank === 2
                      ? 'bg-slate-200 text-slate-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {w.priority_rank}
                  </span>
                </td>

                {/* Address & Entity */}
                <td className="py-3 px-3">
                  <div className="flex flex-col">
                    <span className="font-bold text-[#1E293B] flex items-center gap-1.5">
                      {w.entity_type === 'VASP' && <Building className="w-3.5 h-3.5 text-amber-600" />}
                      {w.label}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500">
                      {w.address.slice(0, 10)}...{w.address.slice(-6)}
                    </span>
                  </div>
                </td>

                {/* Hops */}
                <td className="py-3 px-3">
                  <span className="font-mono text-slate-600 font-medium">
                    {w.hops_from_source} hop{w.hops_from_source > 1 ? 's' : ''}
                  </span>
                </td>

                {/* Volume */}
                <td className="py-3 px-3 font-mono">
                  <div className="text-[#1E293B] font-bold">
                    +{w.total_incoming.toFixed(2)} ETH
                  </div>
                </td>

                {/* Priority Score */}
                <td className="py-3 px-3">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold border uppercase font-mono ${getPriorityBadge(w.priority_level)}`}>
                    {w.priority_score} {w.priority_level}
                  </span>
                </td>

                {/* Rationale */}
                <td className="py-3 px-3 max-w-xs">
                  <p className="text-slate-600 line-clamp-2">
                    {w.reasons.join('; ')}
                  </p>
                  <p className="text-[10px] text-blue-700 mt-1 font-semibold">
                    Action: {w.action_recommendation}
                  </p>
                </td>

                {/* Actions */}
                <td className="py-3 px-3 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {onMonitorWallet && (
                      <button
                        onClick={() => onMonitorWallet(w.address, w.label)}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600"
                        title="Add to Watchlist"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    )}
                    {onInspectWallet && (
                      <button
                        onClick={() => onInspectWallet(w.address)}
                        className="p-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white shadow-sm"
                        title="Deep Trace Wallet"
                      >
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
