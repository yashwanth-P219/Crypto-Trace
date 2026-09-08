import React from 'react';
import { ShieldAlert, Info, AlertTriangle, Cpu, ExternalLink } from 'lucide-react';
import { RiskAssessment } from '../types';
import { TruthBadge } from './TruthBadge';

interface RiskBreakdownProps {
  assessment: RiskAssessment | null;
  mlAssessment?: any;
  onSelectTx?: (txHash: string) => void;
}

export const RiskBreakdown: React.FC<RiskBreakdownProps> = ({
  assessment,
  mlAssessment,
  onSelectTx
}) => {
  if (!assessment) {
    return (
      <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-8 text-center">
        <ShieldAlert className="w-10 h-10 text-slate-400 mx-auto mb-3" />
        <h4 className="text-sm font-bold text-[#1E293B]">
          Risk Assessment Under Computation
        </h4>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          Heuristic behavioral scores and machine learning features are being evaluated for this case.
        </p>
      </div>
    );
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'HIGH':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'MEDIUM':
        return 'text-amber-700 bg-amber-50 border-amber-200';
      default:
        return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    }
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 80) return 'bg-[#DC2626]';
    if (score >= 60) return 'bg-[#DC2626]';
    if (score >= 30) return 'bg-[#F59E0B]';
    return 'bg-[#16A34A]';
  };

  return (
    <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
            Explainable Behavioral Risk Engine
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Rule-based forensic indicators and Random Forest anomaly scoring
          </p>
        </div>
        <div className="flex items-center gap-2">
          <TruthBadge category="AI ASSESSMENT" size="sm" />
        </div>
      </div>

      {/* Main Score Gauge */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Score Display */}
        <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 flex flex-col justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Investigation Risk Score
            </p>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-4xl font-black font-mono text-[#1E293B]">
                {assessment.score}
              </span>
              <span className="text-sm font-semibold text-slate-500">/ 100</span>
              <span className={`ml-auto px-2.5 py-1 text-xs font-bold rounded-lg border uppercase ${getLevelColor(assessment.level)}`}>
                {assessment.level}
              </span>
            </div>
          </div>

          <div className="mt-4">
            <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${getProgressBarColor(assessment.score)}`}
                style={{ width: `${Math.min(100, assessment.score)}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1 font-medium">
              <span>0 LOW</span>
              <span>30 MED</span>
              <span>60 HIGH</span>
              <span>80+ CRITICAL</span>
            </div>
          </div>
        </div>

        {/* Machine Learning Summary */}
        <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 md:col-span-2 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-600" />
              <p className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Machine Learning Anomaly Classifier
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-600 bg-white px-2 py-0.5 rounded border border-slate-200 font-medium">
              RandomForest (50 Estimators)
            </span>
          </div>

          {mlAssessment ? (
            <div className="mt-3 space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-700 font-medium">
                <span>Model Suspicion Probability:</span>
                <span className="font-mono font-bold text-[#1E293B]">
                  {Math.round(mlAssessment.ml_risk_probability * 100)}%
                </span>
              </div>
              <div>
                <p className="text-[11px] text-slate-500 mb-1">Key Contributing Features:</p>
                <div className="flex flex-wrap gap-1.5">
                  {mlAssessment.top_features?.slice(0, 4).map((f: any) => (
                    <span
                      key={f.feature}
                      className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-[10px] text-blue-700 font-mono"
                    >
                      {f.feature}: {f.value}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 mt-2">
              Standard heuristic engine active.
            </p>
          )}

          <p className="text-[10px] text-slate-500 mt-3 italic">
            *ML module provides statistical anomaly guidance only and does not prove illicit intent.
          </p>
        </div>
      </div>

      {/* Itemized Reasons List with Evidence Links */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Point Breakdown & Verified Evidence Links ({assessment.reasons.length} Factors)
        </h4>
        <div className="space-y-2">
          {assessment.reasons.map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-50/70 border border-slate-200 hover:border-slate-300 flex flex-wrap items-start justify-between gap-3 text-xs"
            >
              <div className="flex items-start gap-3">
                <span className="px-2 py-1 rounded bg-red-50 border border-red-200 text-red-700 font-mono font-bold text-xs mt-0.5">
                  +{item.delta}
                </span>
                <div>
                  <p className="font-bold text-[#1E293B]">
                    {item.type.replace(/_/g, ' ')}
                  </p>
                  <p className="text-slate-600 mt-0.5 text-xs">
                    {item.reason}
                  </p>
                  {item.evidence_txs && item.evidence_txs.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Evidence:</span>
                      {item.evidence_txs.map((tx) => (
                        <button
                          key={tx}
                          onClick={() => onSelectTx && onSelectTx(tx)}
                          className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white hover:bg-slate-100 border border-slate-200 text-blue-600 flex items-center gap-1 shadow-sm"
                        >
                          <span>{tx.slice(0, 10)}...</span>
                          <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Forensic Disclaimer */}
      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-3">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <p className="text-[11px] leading-relaxed">
          <strong>FORENSIC DISCLAIMER:</strong> {assessment.disclaimer}
        </p>
      </div>
    </div>
  );
};
