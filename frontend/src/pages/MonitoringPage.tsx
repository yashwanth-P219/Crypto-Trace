import React, { useState, useEffect } from 'react';
import {
  Eye, Bell, ShieldAlert, Plus, RefreshCw, CheckCircle2,
  Trash2, Filter, AlertTriangle, Layers, Sliders, Check
} from 'lucide-react';
import { AlertItem, AlertRuleItem, CreateAlertRulePayload } from '../types';
import { api } from '../services/api';
import { TruthBadge } from '../components/TruthBadge';

export const MonitoringPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [rules, setRules] = useState<AlertRuleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // New Rule Form
  const [ruleForm, setRuleForm] = useState<CreateAlertRulePayload>({
    rule_name: '',
    rule_type: 'HIGH_VALUE_TRANSFER',
    wallet_address: '',
    case_id: '',
    threshold_value: 5.0
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [alertList, ruleList] = await Promise.all([
        api.getAlerts(),
        api.getAlertRules()
      ]);
      setAlerts(alertList);
      setRules(ruleList);
    } catch (err) {
      console.error('Failed to load monitoring data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      );
    } catch (err: any) {
      alert(err.message || 'Failed to acknowledge alert');
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleForm.rule_name.trim()) return;
    setActionLoading(true);
    try {
      await api.createAlertRule({
        ...ruleForm,
        threshold_value: ruleForm.threshold_value ? Number(ruleForm.threshold_value) : undefined,
        wallet_address: ruleForm.wallet_address?.trim() || undefined,
        case_id: ruleForm.case_id?.trim() || undefined
      });
      setShowRuleModal(false);
      setRuleForm({
        rule_name: '',
        rule_type: 'HIGH_VALUE_TRANSFER',
        wallet_address: '',
        case_id: '',
        threshold_value: 5.0
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create alert rule');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to deactivate and remove this alert rule?')) return;
    try {
      await api.deleteAlertRule(ruleId);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    } catch (err: any) {
      alert(err.message || 'Failed to delete alert rule');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-[#1E293B] tracking-wide">
              Real-Time Watchlist & Alert Monitoring
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 font-mono font-bold">
              AUTOMATION
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Surveillance policies, automated triggers, and instant triage for suspect blockchain flows
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowRuleModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#2563EB] hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Alert Rule</span>
          </button>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh All</span>
          </button>
        </div>
      </div>

      {/* Alert Rules Section */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm text-[#1E293B]">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-sm font-bold text-[#1E293B] tracking-wide">
              Configured Alert Policy Rules ({rules.length})
            </h3>
          </div>
          <TruthBadge category="SYSTEM INFERENCE" size="sm" />
        </div>

        {rules.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs bg-slate-50 rounded-xl border border-slate-200">
            No custom surveillance rules configured. Click "Add Alert Rule" to monitor specific thresholds or patterns.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {rules.map((r) => (
              <div
                key={r.id}
                className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between gap-2 shadow-sm"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-bold text-xs text-[#1E293B]">{r.rule_name}</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                      {r.rule_type}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 space-y-0.5 font-mono">
                    {r.threshold_value !== null && r.threshold_value !== undefined && (
                      <p>Threshold: <span className="text-amber-700 font-bold">{r.threshold_value} ETH</span></p>
                    )}
                    {r.wallet_address && (
                      <p className="truncate">Wallet: {r.wallet_address.slice(0, 14)}...</p>
                    )}
                    {r.case_id && (
                      <p>Case: {r.case_id}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                  <span className="text-[10px] text-emerald-700 flex items-center gap-1 font-mono font-semibold">
                    <Check className="w-3 h-3" /> Active Policy
                  </span>
                  <button
                    onClick={() => handleDeleteRule(r.id)}
                    className="p-1 rounded hover:bg-slate-200 text-slate-400 hover:text-red-600 transition-colors"
                    title="Deactivate Rule"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Live Alert Event Feed */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm text-[#1E293B]">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-[#1E293B] tracking-wide">
              Live Alert Event Feed ({alerts.length})
            </h3>
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
          </div>
          <TruthBadge category="SYSTEM INFERENCE" size="sm" />
        </div>

        {alerts.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No active alerts triggered on monitored wallets.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((a) => (
              <div
                key={a.id}
                className={`p-4 rounded-xl border flex flex-wrap items-start justify-between gap-4 text-xs transition-all ${
                  a.is_read
                    ? 'bg-slate-50 border-slate-200 opacity-70'
                    : 'bg-red-50/40 border-red-200'
                }`}
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200 font-mono">
                      {a.risk_level} ALERT
                    </span>
                    <span className="text-[11px] font-mono text-slate-600 truncate">
                      Wallet: {a.wallet_address}
                    </span>
                    {a.is_read && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-mono font-medium">
                        ACKNOWLEDGED
                      </span>
                    )}
                  </div>
                  <p className="text-[#1E293B] leading-relaxed font-semibold">
                    {a.reason}
                  </p>
                  {a.tx_hash && (
                    <p className="text-[10px] font-mono text-blue-700 truncate font-medium">
                      Confirmed Transaction: {a.tx_hash}
                    </p>
                  )}
                </div>

                <div className="flex flex-col items-end gap-2">
                  <span className="text-slate-400 text-[10px] font-mono">
                    {new Date(a.timestamp).toLocaleString()}
                  </span>
                  {!a.is_read && (
                    <button
                      onClick={() => handleAcknowledge(a.id)}
                      className="px-2.5 py-1 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white font-bold text-[10px] transition-colors flex items-center gap-1 shadow-sm"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Alert Rule Modal */}
      {showRuleModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl text-[#1E293B]">
            <h3 className="text-base font-bold text-[#1E293B] mb-1 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#2563EB]" />
              Create Surveillance Alert Policy
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Set automated trigger parameters for rapid flow alerts and threshold violations.
            </p>

            <form onSubmit={handleCreateRule} className="space-y-3">
              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Rule Policy Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Immediate High Value Drain"
                  value={ruleForm.rule_name}
                  onChange={(e) => setRuleForm({ ...ruleForm, rule_name: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Trigger Type *</label>
                <select
                  value={ruleForm.rule_type}
                  onChange={(e) => setRuleForm({ ...ruleForm, rule_type: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                >
                  <option value="HIGH_VALUE_TRANSFER">High Value Transfer (&gt; Threshold)</option>
                  <option value="RAPID_DRAIN">Rapid Drain (&lt; 15 mins)</option>
                  <option value="MIXER_INTERACTION">Mixer Interaction</option>
                  <option value="VASP_DEPOSIT">VASP Deposit Activity</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Value Threshold (ETH)</label>
                <input
                  type="number"
                  step="0.1"
                  value={ruleForm.threshold_value || 0}
                  onChange={(e) => setRuleForm({ ...ruleForm, threshold_value: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Target Wallet Address (Optional)</label>
                <input
                  type="text"
                  placeholder="Leave empty for all watched wallets"
                  value={ruleForm.wallet_address || ''}
                  onChange={(e) => setRuleForm({ ...ruleForm, wallet_address: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-600 hover:text-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  {actionLoading ? 'Saving...' : 'Deploy Policy'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
