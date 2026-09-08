import React, { useState, useEffect } from 'react';
import {
  Network, ArrowRight, Layers, ExternalLink, Shield, Plus,
  RefreshCw, CheckCircle2, AlertCircle, GitMerge, Search, Send
} from 'lucide-react';
import { api } from '../services/api';
import {
  BlockchainNetworkInfo,
  MultichainWalletSummary,
  CrossChainLinkItem,
  RecordCrossChainLinkPayload,
  User
} from '../types';
import { TruthBadge } from './TruthBadge';

interface MultiChainExplorerProps {
  currentUser: User | null;
  onInspectWallet: (address: string) => void;
}

export const MultiChainExplorer: React.FC<MultiChainExplorerProps> = ({
  currentUser,
  onInspectWallet
}) => {
  const [chains, setChains] = useState<BlockchainNetworkInfo[]>([]);
  const [bridges, setBridges] = useState<any[]>([]);
  const [links, setLinks] = useState<CrossChainLinkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [walletLookup, setWalletLookup] = useState('');
  const [walletSummary, setWalletSummary] = useState<MultichainWalletSummary | null>(null);
  const [walletLoading, setWalletLoading] = useState(false);
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [recordLoading, setRecordLoading] = useState(false);

  // Form state
  const [formData, setFormData] = useState<RecordCrossChainLinkPayload>({
    source_chain_id: 11155111,
    target_chain_id: 1,
    source_tx_hash: '',
    target_tx_hash: '',
    bridge_protocol: 'Stargate Finance',
    wallet_address: '',
    amount_transferred: 1.5
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [ch, br, lk] = await Promise.all([
        api.getChains(),
        api.getCrossChainBridges(),
        api.getCrossChainLinks()
      ]);
      setChains(ch);
      setBridges(br);
      setLinks(lk);
    } catch (err) {
      console.error('Failed to load multi-chain data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleWalletLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!walletLookup.trim()) return;
    setWalletLoading(true);
    try {
      const data = await api.getMultichainWallet(walletLookup.trim());
      setWalletSummary(data);
    } catch (err: any) {
      alert(err.message || 'Failed to inspect multi-chain wallet');
    } finally {
      setWalletLoading(false);
    }
  };

  const handleRecordLink = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.source_tx_hash.trim() || !formData.wallet_address.trim()) return;
    setRecordLoading(true);
    try {
      await api.recordCrossChainLink(formData);
      setShowRecordModal(false);
      setFormData({
        source_chain_id: 11155111,
        target_chain_id: 1,
        source_tx_hash: '',
        target_tx_hash: '',
        bridge_protocol: 'Stargate Finance',
        wallet_address: '',
        amount_transferred: 1.0
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to record cross-chain link');
    } finally {
      setRecordLoading(false);
    }
  };

  const getChainName = (chainId: number) => {
    const found = chains.find((c) => c.chain_id === chainId);
    return found ? found.network_name : `Chain #${chainId}`;
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#0F172A] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl text-white relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <div className="p-2 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-400">
                <Network className="w-5 h-5" />
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
                Multi-Chain Architecture & Cross-Chain Bridges
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 font-mono font-bold">
                CROSS-CHAIN
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              Cross-network forensic abstraction supporting EVM-compatible networks, liquidity bridge tracing, and cross-chain fund hopping detection.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowRecordModal(true)}
              className="px-4 py-2.5 rounded-xl bg-[#2563EB] hover:bg-blue-600 text-white text-xs font-bold transition-all shadow-lg shadow-blue-500/20 flex items-center gap-1.5"
            >
              <GitMerge className="w-3.5 h-3.5" />
              Record Bridge Hop
            </button>
            <button
              onClick={loadData}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
              title="Refresh Chains & Links"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Registered Blockchain Networks Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800">
          {chains.map((chain) => (
            <div
              key={chain.chain_id}
              className={`p-4 rounded-xl border transition-all ${
                chain.rpc_configured
                  ? 'bg-slate-900/90 border-blue-500/50 shadow-sm'
                  : 'bg-slate-900/50 border-slate-700/60'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="font-bold text-xs text-white tracking-wide">
                  {chain.network_name}
                </span>
                <span
                  className={`text-[9px] px-2 py-0.5 rounded font-mono font-bold border ${
                    chain.rpc_configured
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-500/50'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {chain.rpc_configured ? 'RPC ACTIVE' : 'REGISTERED'}
                </span>
              </div>

              <div className="space-y-1 text-[11px] text-slate-400 font-mono">
                <div className="flex justify-between">
                  <span>Chain ID:</span>
                  <span className="text-slate-200 font-semibold">{chain.chain_id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Currency:</span>
                  <span className="text-slate-200 font-semibold">{chain.native_currency}</span>
                </div>
                <div className="flex justify-between">
                  <span>Type:</span>
                  <span className="text-slate-200 font-semibold">{chain.is_evm ? 'EVM Compatible' : 'Non-EVM'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Multi-Chain Wallet Lookup */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm text-[#1E293B]">
        <h3 className="text-sm font-bold text-[#1E293B] mb-1 flex items-center gap-2">
          <Search className="w-4 h-4 text-[#2563EB]" />
          Multi-Chain Wallet Inspector
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Query suspect wallet balances and active presence across all configured blockchain networks simultaneously.
        </p>

        <form onSubmit={handleWalletLookup} className="flex gap-2 max-w-2xl mb-4">
          <input
            type="text"
            required
            placeholder="Enter EVM wallet address (0x...)"
            value={walletLookup}
            onChange={(e) => setWalletLookup(e.target.value)}
            className="flex-1 px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs text-[#1E293B] font-mono placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
          />
          <button
            type="submit"
            disabled={walletLoading}
            className="px-4 py-2 rounded-xl bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${walletLoading ? 'animate-spin' : ''}`} />
            Inspect All Chains
          </button>
        </form>

        {walletSummary && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-blue-700 font-bold select-all">
                {walletSummary.wallet_address}
              </span>
              <button
                onClick={() => onInspectWallet(walletSummary.wallet_address)}
                className="text-[11px] text-[#2563EB] hover:underline flex items-center gap-1 font-semibold"
              >
                Detailed Analysis <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {walletSummary.chains.map((c) => (
                <div key={c.chain_id} className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-slate-700">{c.network_name}</span>
                    <span className="text-[10px] font-mono text-slate-400">#{c.chain_id}</span>
                  </div>
                  <div className="text-sm font-mono font-bold text-[#1E293B]">
                    {c.balance_native !== undefined ? `${c.balance_native.toFixed(4)} ${c.native_currency}` : 'N/A'}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Transactions: <span className="font-mono text-slate-800 font-semibold">{c.transaction_count ?? 0}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Cross-Chain Bridges & Recorded Links Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Supported Cross-Chain Bridges */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm text-[#1E293B]">
          <h3 className="text-sm font-bold text-[#1E293B] mb-1 flex items-center gap-2">
            <GitMerge className="w-4 h-4 text-[#2563EB]" />
            Monitored Bridge Protocols
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Cross-chain liquidity bridge routers monitored for illicit hops.
          </p>

          <div className="space-y-3">
            {bridges.map((b, idx) => (
              <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-[#1E293B]">{b.name}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                    {b.supported_chains?.length || 0} Chains
                  </span>
                </div>
                <p className="text-[11px] text-slate-600">{b.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recorded Cross-Chain Links */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 text-[#1E293B]">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#1E293B] flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-600" />
                Cross-Chain Forensic Link Ledger
              </h3>
              <p className="text-xs text-slate-500">
                Verified and correlated cross-chain fund movements between networks.
              </p>
            </div>
            <TruthBadge category="CROSS-CHAIN LEDGER" size="sm" />
          </div>

          {links.length === 0 ? (
            <div className="p-10 text-center text-slate-500 text-xs bg-slate-50 rounded-xl border border-slate-200">
              No cross-chain movement links recorded yet. Click "Record Bridge Hop" to register an inter-chain transfer.
            </div>
          ) : (
            <div className="space-y-3">
              {links.map((lk) => (
                <div
                  key={lk.id}
                  className="p-4 bg-white border border-slate-200 rounded-xl space-y-2 hover:border-slate-300 transition-colors shadow-sm"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-blue-700 font-mono">
                        {getChainName(lk.source_chain_id)}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-purple-600" />
                      <span className="text-xs font-bold text-purple-700 font-mono">
                        {getChainName(lk.target_chain_id)}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium">
                        {lk.bridge_protocol}
                      </span>
                    </div>

                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {lk.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Wallet Address</span>
                      <span
                        onClick={() => onInspectWallet(lk.wallet_address)}
                        className="font-mono text-slate-700 hover:text-[#2563EB] hover:underline cursor-pointer truncate block font-medium"
                      >
                        {lk.wallet_address}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Source Tx Hash</span>
                      <span className="font-mono text-slate-700 truncate block font-medium">
                        {lk.source_tx_hash}
                      </span>
                    </div>
                  </div>

                  {lk.amount_transferred !== null && lk.amount_transferred !== undefined && (
                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span className="text-slate-500">Transferred Volume:</span>
                      <span className="font-mono font-bold text-[#1E293B]">
                        {lk.amount_transferred} ETH / Tokens
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Record Bridge Hop Modal */}
      {showRecordModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl text-[#1E293B]">
            <h3 className="text-base font-bold text-[#1E293B] mb-1 flex items-center gap-2">
              <GitMerge className="w-4 h-4 text-[#2563EB]" />
              Record Cross-Chain Hop Link
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Correlate a suspect transaction jumping across chains via a bridge router.
            </p>

            <form onSubmit={handleRecordLink} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-700 font-semibold block mb-1">Source Chain</label>
                  <select
                    value={formData.source_chain_id}
                    onChange={(e) => setFormData({ ...formData, source_chain_id: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  >
                    {chains.map((c) => (
                      <option key={c.chain_id} value={c.chain_id}>
                        {c.network_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-700 font-semibold block mb-1">Target Chain</label>
                  <select
                    value={formData.target_chain_id}
                    onChange={(e) => setFormData({ ...formData, target_chain_id: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                  >
                    {chains.map((c) => (
                      <option key={c.chain_id} value={c.chain_id}>
                        {c.network_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Bridge Protocol *</label>
                <select
                  value={formData.bridge_protocol}
                  onChange={(e) => setFormData({ ...formData, bridge_protocol: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] focus:outline-none focus:border-[#2563EB]"
                >
                  <option value="Stargate Finance">Stargate Finance</option>
                  <option value="Across Protocol">Across Protocol</option>
                  <option value="Hop Protocol">Hop Protocol</option>
                  <option value="Synapse Network">Synapse Network</option>
                  <option value="Celer cBridge">Celer cBridge</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Wallet Address *</label>
                <input
                  type="text"
                  required
                  placeholder="0x..."
                  value={formData.wallet_address}
                  onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Source Tx Hash *</label>
                <input
                  type="text"
                  required
                  placeholder="0x..."
                  value={formData.source_tx_hash}
                  onChange={(e) => setFormData({ ...formData, source_tx_hash: e.target.value })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono placeholder-slate-400 focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div>
                <label className="text-xs text-slate-700 font-semibold block mb-1">Transferred Amount (Native)</label>
                <input
                  type="number"
                  step="0.001"
                  value={formData.amount_transferred || 0}
                  onChange={(e) => setFormData({ ...formData, amount_transferred: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs text-[#1E293B] font-mono focus:outline-none focus:border-[#2563EB]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowRecordModal(false)}
                  className="px-3 py-1.5 rounded-lg text-xs text-slate-600 hover:text-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={recordLoading}
                  className="px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  {recordLoading ? 'Recording...' : 'Record Bridge Hop'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
