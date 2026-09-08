import React, { useState, useEffect } from 'react';
import {
  FolderLock, AlertTriangle, Eye, ShieldAlert,
  ArrowRight, Search, Activity, Sparkles, Building, Database
} from 'lucide-react';
import { Case, AlertItem } from '../types';
import { StatCard } from '../components/StatCard';
import { TruthBadge } from '../components/TruthBadge';
import { api } from '../services/api';

interface DashboardPageProps {
  onOpenCase: (caseId: string) => void;
  onNavigateToWallets: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onOpenCase,
  onNavigateToWallets
}) => {
  const [cases, setCases] = useState<Case[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [statusMeta, setStatusMeta] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [caseList, alertList, sys] = await Promise.all([
        api.getCases(),
        api.getAlerts(),
        api.getSystemStatus()
      ]);
      setCases(caseList);
      setAlerts(alertList);
      setStatusMeta(sys);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalCases = cases.length;
  const criticalCases = cases.filter((c) => c.priority === 'CRITICAL').length;
  const highCases = cases.filter((c) => c.priority === 'HIGH').length;
  const openCases = cases.filter((c) => c.status !== 'CLOSED').length;

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero - Deep Navy Blue */}
      <div className="p-6 rounded-2xl bg-[#0F172A] border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-md text-white">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-400">
              CYBERCRIME DEFENSE COMMAND ACTIVE
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-white mt-1">
            Real-Time Cryptocurrency Fraud Investigation Dashboard
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl">
            Automated multi-hop tracking, peeling chain pattern detection, and verified VASP liquidation identification for police & cyber units.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onOpenCase('CASE-SIH2026-001')}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-extrabold shadow-sm transition-all font-sans"
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>Launch Official Demo Case</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Registered Cases"
          value={totalCases}
          subtitle="Forensic investigations logged"
          icon={FolderLock}
          color="indigo"
        />
        <StatCard
          title="Active Investigations"
          value={openCases}
          subtitle="Under active multi-hop review"
          icon={Activity}
          color="cyan"
        />
        <StatCard
          title="Critical / High Priority"
          value={criticalCases + highCases}
          subtitle="High fraud exposure"
          icon={ShieldAlert}
          color="red"
          trend="Action Req."
        />
        <StatCard
          title="Monitored Watchlists"
          value={alerts.length + 3}
          subtitle="Real-time trigger alerts"
          icon={Eye}
          color="amber"
        />
      </div>

      {/* Main Grid: Active Cases & Monitored Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases List (2 Cols) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
                Recent Investigation Cases
              </h3>
              <p className="text-xs text-slate-500">
                Suspect wallet cases awaiting evidence review and supervisor approval
              </p>
            </div>
            <TruthBadge category="BLOCKCHAIN FACT" size="sm" />
          </div>

          <div className="space-y-3">
            {cases.map((c) => (
              <div
                key={c.case_id}
                onClick={() => onOpenCase(c.case_id)}
                className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 hover:border-blue-400 cursor-pointer transition-all hover:bg-white hover:shadow-sm flex flex-wrap items-center justify-between gap-4 group"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl border ${
                    c.priority === 'CRITICAL'
                      ? 'bg-red-50 border-red-200 text-[#DC2626]'
                      : 'bg-blue-50 border-blue-200 text-[#2563EB]'
                  }`}>
                    <FolderLock className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#1E293B] group-hover:text-blue-600 transition-colors">
                        {c.title || c.complaint_reference}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
                        {c.blockchain}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5 font-mono">
                      Suspect: {c.suspect_wallet ? `${c.suspect_wallet.slice(0, 14)}...${c.suspect_wallet.slice(-6)}` : 'Pending address'}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Victim: {c.victim_name || 'Anonymous Complainant'} • Reported Loss: {Number(c.amount_lost || 0).toLocaleString()} {c.currency || 'ETH'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className={`px-2.5 py-1 rounded text-[10px] font-bold border uppercase ${
                      c.status === 'CLOSED'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : c.status === 'SUPERVISOR_REVIEW'
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : 'bg-amber-50 text-amber-700 border-amber-200'
                    }`}>
                      {(c.status || 'NEW').replace(/_/g, ' ')}
                    </span>
                    <p className="text-[10px] text-slate-500 mt-1 font-mono">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'N/A'}
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Alerts Panel (1 Col) */}
        <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 space-y-4 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
                Real-Time Watchlist Alerts
              </h3>
              <p className="text-xs text-slate-500">
                Fresh activity on monitored addresses
              </p>
            </div>
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto max-h-[420px]">
            {alerts.length === 0 ? (
              <div className="text-center py-10 text-slate-400 text-xs">
                No active critical alerts recorded.
              </div>
            ) : (
              alerts.map((a) => (
                <div
                  key={a.id}
                  className="p-3 rounded-xl bg-red-50/60 border border-red-200 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-red-700 font-mono px-2 py-0.5 rounded bg-red-100 border border-red-200">
                      HIGH RISK ALERT
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {new Date(a.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-slate-700 text-[11px] leading-relaxed">
                    {a.reason}
                  </p>
                  {a.tx_hash && (
                    <p className="text-[10px] font-mono text-blue-600 truncate">
                      Tx: {a.tx_hash}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
