import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, AlertTriangle, Cpu, ExternalLink, Search,
  RefreshCw, CheckCircle2, ChevronRight, Activity, Building2,
  FileSearch, Scale, Info, Layers, ArrowUpRight
} from 'lucide-react';
import { api } from '../services/api';
import { CombinedInvestigationResponse, Case } from '../types';
import { TruthBadge } from './TruthBadge';
import { ErrorBoundary } from './ErrorBoundary';

interface InvestigationAnalysisProps {
  currentCase?: Case | null;
  initialWallet?: string;
  onSelectTx?: (txHash: string) => void;
}

const InvestigationAnalysisInner: React.FC<InvestigationAnalysisProps> = ({
  currentCase,
  initialWallet,
  onSelectTx
}) => {
  const [walletAddress, setWalletAddress] = useState(
    initialWallet || currentCase?.suspect_wallet || ''
  );
  const [maxHops, setMaxHops] = useState<number>(3);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<CombinedInvestigationResponse | null>(null);

  // Sync wallet address and automatically run analysis on mount
  useEffect(() => {
    const target = (initialWallet || currentCase?.suspect_wallet || walletAddress || '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97').trim();
    if (target) {
      setWalletAddress(target);
      runAnalysis(target);
    }
  }, [initialWallet, currentCase]);

  const runAnalysis = async (targetWallet?: string) => {
    const addr = (targetWallet || walletAddress).trim();
    if (!addr) {
      setError('Please provide a valid Ethereum wallet address.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await api.getWalletInvestigationAnalysis(
        addr,
        currentCase?.case_id,
        maxHops
      );
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || 'Investigation analysis failed. Ensure the wallet has synced transactions.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score?: number) => {
    const sc = Number(score || 0);
    if (sc >= 80) return 'text-red-700 bg-red-50 border-red-200';
    if (sc >= 60) return 'text-red-600 bg-red-50 border-red-200';
    if (sc >= 30) return 'text-amber-800 bg-amber-50 border-amber-200';
    return 'text-emerald-700 bg-emerald-50 border-emerald-200';
  };

  const getSeverityBadge = (sev?: string, points?: number) => {
    let s = (sev || '').toUpperCase();
    if (!s && typeof points === 'number') {
      if (points >= 25) s = 'CRITICAL';
      else if (points >= 15) s = 'HIGH';
      else if (points >= 10) s = 'MEDIUM';
      else s = 'LOW';
    }
    switch (s) {
      case 'CRITICAL':
        return 'bg-red-50 text-red-700 border border-red-200';
      case 'HIGH':
        return 'bg-red-50 text-red-600 border border-red-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-800 border border-amber-200';
      default:
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-bold text-[#1E293B] flex items-center gap-2">
              <FileSearch className="w-5 h-5 text-[#2563EB]" />
              Automated Forensic Intelligence & Risk Dossier
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Multi-hop pattern detection, explainable 0–100 risk quantification, and entity attribution
            </p>
          </div>
          <div className="flex items-center gap-2">
            <TruthBadge category="FORENSIC DOSSIER" size="sm" />
          </div>
        </div>

        {/* Input Bar */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div className="md:col-span-8">
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Target Wallet Address
            </label>
            <div className="relative">
              <input
                type="text"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder="0x..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-[#1E293B] font-mono focus:outline-none focus:bg-white focus:border-blue-500 pl-10 transition-colors"
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            </div>
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Max Hop Depth
            </label>
            <select
              value={maxHops}
              onChange={(e) => setMaxHops(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 text-xs text-slate-700 focus:outline-none focus:bg-white focus:border-blue-500"
            >
              <option value={1}>1 Hop (Direct)</option>
              <option value={2}>2 Hops</option>
              <option value={3}>3 Hops (Standard)</option>
              <option value={4}>4 Hops</option>
              <option value={5}>5 Hops (Deep)</option>
            </select>
          </div>

          <div className="md:col-span-2 flex items-end">
            <button
              onClick={() => runAnalysis()}
              disabled={loading}
              className="w-full bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl py-2.5 px-4 text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        </div>

        {/* Quick Sample Forensic Wallets */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-200">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Quick Sample Wallets:</span>
          {[
            { label: '🔴 Suspect Intake (Wallet A)', addr: '0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97' },
            { label: '🟡 Splitter (Wallet B)', addr: '0x1db3439a222c519ab44bb1144fc23cc742106cf2' },
            { label: '🟡 Mule (Wallet F)', addr: '0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852' },
            { label: '🟡 Consolidator (Wallet G)', addr: '0x7a250d5630b4cf539739df2c5dacb4c659f2488d' },
            { label: '🟢 Binance 14 VASP', addr: '0x28c6c06298d514db089934071355e5743bf21d60' }
          ].map((w) => (
            <button
              key={w.addr}
              type="button"
              onClick={() => {
                setWalletAddress(w.addr);
                runAnalysis(w.addr);
              }}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-mono border transition-all ${
                walletAddress.toLowerCase() === w.addr.toLowerCase()
                  ? 'bg-blue-50 border-blue-300 text-blue-700 font-bold shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 border-slate-200 text-slate-600'
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {analysis && (
        <div className="space-y-6">
          {/* Top Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Risk Gauge Card */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
              <div>
                <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Investigative Risk Score
                </span>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className={`text-4xl font-extrabold ${getScoreColor(analysis.risk_score).split(' ')[0]}`}>
                    {Math.round(analysis.risk_score)}
                  </span>
                  <span className="text-sm text-slate-400 font-medium">/ 100</span>
                </div>
              </div>

              <div className="mt-4">
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      analysis.risk_score >= 80
                        ? 'bg-red-600'
                        : analysis.risk_score >= 60
                        ? 'bg-red-500'
                        : analysis.risk_score >= 30
                        ? 'bg-amber-500'
                        : 'bg-emerald-600'
                    }`}
                    style={{ width: `${Math.min(analysis.risk_score, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between items-center mt-2">
                  <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${getSeverityBadge(analysis.risk_category)}`}>
                    {analysis.risk_category} RISK
                  </span>
                  <span className="text-[11px] text-slate-500">
                    Rule Score: {Math.round(analysis.rule_based_score)}
                  </span>
                </div>
              </div>
            </div>

            {/* Patterns Detected */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
              <div>
                <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Suspicious Patterns
                </span>
                <div className="mt-2 text-3xl font-extrabold text-[#1E293B]">
                  {(analysis.patterns || []).length}
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Identified behavioral topologies (rapid movement, splitting, consolidation, cycles)
              </p>
            </div>

            {/* Identified Entities */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
              <div>
                <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Attributed Entities / VASPs
                </span>
                <div className="mt-2 text-3xl font-extrabold text-[#1E293B]">
                  {(analysis.entities_identified || []).length}
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Exchanges, VASPs, or smart contracts reached in multi-hop flow paths
              </p>
            </div>

            {/* Evidence Links */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col justify-between shadow-sm">
              <div>
                <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
                  Evidence Transactions
                </span>
                <div className="mt-2 text-3xl font-extrabold text-[#1E293B]">
                  {(analysis.evidence_transactions || []).length}
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Direct on-chain transaction hashes anchoring observed behavioral patterns
              </p>
            </div>
          </div>

          {/* Verdict Summary Box */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Scale className="w-4 h-4 text-[#2563EB]" />
              <h3 className="text-xs font-bold text-[#1E293B] uppercase tracking-wider">
                Investigative Summary Verdict
              </h3>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed font-medium">
              {analysis.summary_verdict || 'Forensic analysis completed for target wallet.'}
            </p>
          </div>

          {/* Why This Risk? Factor Contributions */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-600" />
                <h3 className="text-sm font-bold text-[#1E293B]">
                  Explainable Risk Breakdown ("Why this risk?")
                </h3>
              </div>
              <span className="text-xs text-slate-500">
                Transparent factor contributions normalized 0–100
              </span>
            </div>

            {/* Plain English Bullet Explanations */}
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2">
              <h4 className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-[#2563EB]" />
                Key Investigative Findings:
              </h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-slate-600">
                {(analysis.why_this_risk || []).map((item, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Factor Contribution Table */}
            {(analysis.contributions || []).length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-700">
                  <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Risk Factor</th>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Score Contribution</th>
                      <th className="px-4 py-3">Evidence</th>
                      <th className="px-4 py-3">Forensic Rationale</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(analysis.contributions || []).map((c: any, idx: number) => {
                      const factorName = c.factor_name || (c.factor ? c.factor.replace(/_/g, ' ').toUpperCase() : `Factor ${idx + 1}`);
                      const severity = c.severity || (c.points >= 25 ? 'CRITICAL' : c.points >= 15 ? 'HIGH' : c.points >= 10 ? 'MEDIUM' : 'LOW');
                      const evidenceCount = c.evidence_count ?? c.supporting_transactions?.length ?? 0;
                      return (
                        <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                          <td className="px-4 py-3 font-semibold text-[#1E293B]">
                            {factorName}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getSeverityBadge(severity, c.points)}`}>
                              {severity}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono font-bold text-amber-700">
                            +{Math.round(c.points || 0)} pts
                          </td>
                          <td className="px-4 py-3 font-mono text-slate-500">
                            {evidenceCount} tx(s)
                          </td>
                          <td className="px-4 py-3 text-slate-600 max-w-md">
                            {c.explanation}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Detected Suspicious Patterns */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-[#2563EB]" />
                <h3 className="text-sm font-bold text-[#1E293B]">
                  Detected Suspicious Transaction Patterns ({(analysis.patterns || []).length})
                </h3>
              </div>
              <span className="text-xs text-slate-500">
                Evaluated against 9 forensic topology rules
              </span>
            </div>

            {(analysis.patterns || []).length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
                No anomalous or structuring patterns detected within the examined hop depth.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(analysis.patterns || []).map((pat, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-[#1E293B]">
                            {pat.pattern_name}
                          </span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getSeverityBadge(pat.severity)}`}>
                            {pat.severity}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-400">
                          ID: {pat.pattern_id} • Confidence: {Math.round(pat.confidence * 100)}%
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {pat.description}
                    </p>

                    {/* Related Hashes */}
                    {pat.related_transaction_hashes && pat.related_transaction_hashes.length > 0 && (
                      <div className="space-y-1 pt-1 border-t border-slate-200">
                        <span className="text-[10px] uppercase font-semibold text-slate-500">
                          Related Hashes:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {pat.related_transaction_hashes.slice(0, 4).map((h, hIdx) => (
                            <button
                              key={hIdx}
                              onClick={() => onSelectTx?.(h)}
                              className="px-2 py-0.5 bg-white hover:bg-slate-100 text-[#2563EB] border border-slate-200 rounded font-mono text-[10px] flex items-center gap-1 transition-colors shadow-xs"
                            >
                              {h.slice(0, 8)}...{h.slice(-6)}
                              <ArrowUpRight className="w-3 h-3" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Identified Entities & Gateways */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-emerald-600" />
                <h3 className="text-sm font-bold text-[#1E293B]">
                  Identified Entities & VASP Gateways ({(analysis.entities_identified || []).length})
                </h3>
              </div>
              <span className="text-xs text-slate-500">
                Addresses resolved against verified exchanges and VASPs
              </span>
            </div>

            {(analysis.entities_identified || []).length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
                No external exchanges or designated VASPs were identified in the traced paths. All endpoints remain UNKNOWN.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(analysis.entities_identified || []).map((ent, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-xs font-bold text-[#1E293B]">
                          {ent.entity_name || 'Unlabeled Entity'}
                        </span>
                        <div className="text-[11px] font-mono text-slate-500">
                          {ent.address ? `${ent.address.slice(0, 10)}...${ent.address.slice(-8)}` : 'N/A'}
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {ent.entity_type}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200">
                      <span>Confidence: {ent.confidence}</span>
                      <span className="flex items-center gap-1 text-emerald-700 font-semibold">
                        {ent.verified ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Verified
                          </>
                        ) : (
                          'Unverified'
                        )}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Machine Learning Insights & Feature Importance */}
          {analysis.ml_summary && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-purple-600" />
                  <h3 className="text-sm font-bold text-[#1E293B]">
                    Machine Learning Behavioral Baseline ({analysis.ml_summary.model_name})
                  </h3>
                </div>
                <span className="text-xs text-slate-500">
                  Model Version: {analysis.ml_summary.model_version}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 uppercase font-semibold">
                    ML Risk Probability
                  </span>
                  <div className="text-2xl font-bold text-purple-700 mt-1">
                    {Math.round((analysis.ml_summary.ml_risk_probability || 0) * 100)}%
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 uppercase font-semibold">
                    Behavioral Classification
                  </span>
                  <div className="text-lg font-bold text-[#1E293B] mt-1">
                    {analysis.ml_summary.prediction || 'ELEVATED_RISK'}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="text-xs text-slate-500 uppercase font-semibold">
                    Top Predictive Features
                  </span>
                  <div className="text-xs text-slate-600 mt-2 space-y-1">
                    {analysis.ml_summary.feature_importance && (
                      Array.isArray(analysis.ml_summary.feature_importance)
                        ? analysis.ml_summary.feature_importance.map((item: any, i: number) => {
                            const name = item.feature || item.name || `Feature ${i + 1}`;
                            const val = item.model_importance ?? item.importance ?? item.value ?? 0;
                            return (
                              <div key={i} className="flex justify-between font-mono text-[11px]">
                                <span className="text-slate-500">{name}:</span>
                                <span className="text-purple-700 font-semibold">{Math.round(Number(val) * 100)}%</span>
                              </div>
                            );
                          })
                        : Object.entries(analysis.ml_summary.feature_importance).map(([feat, imp]: any, i: number) => (
                            <div key={i} className="flex justify-between font-mono text-[11px]">
                              <span className="text-slate-500">{feat}:</span>
                              <span className="text-purple-700 font-semibold">
                                {typeof imp === 'number' ? `${Math.round(imp * 100)}%` : String(imp)}
                              </span>
                            </div>
                          ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Legal Notice / Non-Criminalization Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 leading-relaxed flex items-start gap-2.5">
            <Info className="w-4 h-4 shrink-0 text-slate-400 mt-0.5" />
            <div>
              <span className="font-semibold text-[#1E293B]">Forensic Notice: </span>
              {analysis.disclaimer}
            </div>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !analysis && (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-4 shadow-sm">
          <RefreshCw className="w-8 h-8 text-[#2563EB] animate-spin mx-auto" />
          <div>
            <p className="text-sm font-semibold text-[#1E293B]">Executing Multi-Hop Forensic Intelligence Pipeline...</p>
            <p className="text-xs text-slate-500 mt-1">
              Tracing flow paths across hops, quantifying rule and ML risk scores, and resolving VASP entities.
            </p>
          </div>
        </div>
      )}

      {/* Empty State / Initial Prompt */}
      {!loading && !analysis && (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-3 shadow-sm">
          <FileSearch className="w-10 h-10 text-slate-400 mx-auto" />
          <p className="text-sm font-semibold text-[#1E293B]">No Forensic Dossier Active</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Select a target wallet above and click "Run Analysis" or select one of the Quick Sample Wallets.
          </p>
          <button
            type="button"
            onClick={() => runAnalysis('0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97')}
            className="mt-2 px-4 py-2 bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold rounded-xl inline-flex items-center gap-2 shadow-sm transition-all cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Analyze Suspect Intake (Wallet A)
          </button>
        </div>
      )}
    </div>
  );
};

export const InvestigationAnalysis: React.FC<InvestigationAnalysisProps> = (props) => {
  return (
    <ErrorBoundary fallbackTitle="Automated Forensic Intelligence Dossier">
      <InvestigationAnalysisInner {...props} />
    </ErrorBoundary>
  );
};
